"""
Stream Worker 핵심: 채널별 subprocess 1개 관리.
- 한 워커가 여러 채널을 담당 (channel_id -> process 매핑).
- Lease: 이 워커가 할당받은 채널만 실행. (Orchestrator가 stream.commands 또는 전용 토픽으로 지시)
- 멱등성: 동일 (channel_id, job_id/idempotency_key) 재진입 시 이미 RUNNING이면 무시 또는 재시작 정책에 따름.
- 재시작(backoff): 프로세스 비정상 종료 시 exponential backoff 후 재시도, 최대 횟수 초과 시 FAILED 발행.
"""
import logging
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Callable, Dict, Optional

from app.stream_worker.pipeline_runner import PipelineParams, start_pipeline
from app.schemas.stream_events import EventType, StreamEvent

logger = logging.getLogger(__name__)


@dataclass
class ChannelHandle:
    """채널 1개에 대한 런타임 핸들: process + 메타."""
    channel_id: str
    job_id: str
    process: Optional[subprocess.Popen] = None
    params: Optional[PipelineParams] = None
    frame_count: int = 0
    last_pts: float = 0.0
    # backoff: 재시작 간격 (초). 실패 시 증가, 성공 시 리셋.
    backoff_sec: float = 1.0
    restart_count: int = 0
    max_restarts: int = 5


class ChannelManager:
    """
    채널당 프로세스 1개 유지.
    - start_channel: lease를 받은 채널에 대해 subprocess 기동, STARTED 발행.
    - stop_channel: 프로세스 종료, STOPPED 발행.
    - heartbeat_loop: 주기적으로 HEARTBEAT 발행 (frame_count, last_pts는 파이프라인에서 파싱하거나 0).
    - _check_exited: 프로세스 비정상 종료 시 backoff 후 재시작 또는 FAILED 발행.
    """

    def __init__(
        self,
        worker_id: str,
        *,
        publish_event: Callable[[StreamEvent], None],
        heartbeat_interval_sec: float = 30.0,
        max_restarts: int = 5,
    ):
        self.worker_id = worker_id
        self._publish = publish_event
        self._heartbeat_interval = heartbeat_interval_sec
        self._max_restarts = max_restarts
        self._channels: Dict[str, ChannelHandle] = {}
        self._lock = threading.RLock()
        self._shutdown = False

    # ----- 멱등성 -----
    # Orchestrator가 동일 channel_id에 대해 한 워커만 lease를 준다.
    # 따라서 이 워커가 start_channel을 두 번 받는 경우는 "같은 명령 재전달"이면
    # 이미 RUNNING인 채널은 무시하거나, 정책에 따라 재시작(stop 후 start) 가능.
    # job_id/idempotency_key가 바뀌면 "새 job"이므로 기존 프로세스 정리 후 새로 시작.

    def start_channel(self, channel_id: str, job_id: str, idempotency_key: str, params: PipelineParams) -> None:
        """채널 시작. 이미 같은 channel_id가 RUNNING이면 job_id 비교 후 멱등 처리."""
        with self._lock:
            existing = self._channels.get(channel_id)
            if existing and existing.process is not None and existing.process.poll() is None:
                # 이미 실행 중. 같은 job이면 무시(멱등).
                if existing.job_id == job_id:
                    logger.info("channel_id=%s job_id=%s already running (idempotent)", channel_id, job_id)
                    return
                # 다른 job: 기존 중지 후 새로 시작
                self._stop_internal(channel_id)

            handle = ChannelHandle(channel_id=channel_id, job_id=job_id, params=params)
            try:
                proc = start_pipeline(channel_id, params, use_ffmpeg=True)
                handle.process = proc
                self._channels[channel_id] = handle
                self._publish(StreamEvent(
                    event=EventType.STARTED,
                    channel_id=channel_id,
                    worker_id=self.worker_id,
                    job_id=job_id,
                ))
            except Exception as e:
                logger.exception("channel_id=%s start failed: %s", channel_id, e)
                self._publish(StreamEvent(
                    event=EventType.FAILED,
                    channel_id=channel_id,
                    worker_id=self.worker_id,
                    job_id=job_id,
                    message=str(e),
                ))

    def stop_channel(self, channel_id: str) -> None:
        """채널 중지. STOPPED 이벤트 발행."""
        with self._lock:
            self._stop_internal(channel_id)

    def _stop_internal(self, channel_id: str) -> None:
        """락 내부에서만 호출."""
        handle = self._channels.pop(channel_id, None)
        if not handle or not handle.process:
            return
        try:
            handle.process.terminate()
            handle.process.wait(timeout=10)
        except Exception as e:
            logger.warning("channel_id=%s terminate: %s", channel_id, e)
            try:
                handle.process.kill()
            except Exception:
                pass
        self._publish(StreamEvent(
            event=EventType.STOPPED,
            channel_id=channel_id,
            worker_id=self.worker_id,
            job_id=handle.job_id,
        ))

    # ----- Lease -----
    # Orchestrator가 "이 워커에게 이 채널을 할당"했다는 전제로 start_channel이 호출됨.
    # Lease 갱신: Orchestrator가 stream.events의 HEARTBEAT를 보고 DB의 lease_expires_at을 갱신.
    # Lease 만료: Orchestrator가 만료된 채널을 LOST로 전이하고, 다른 워커에 재할당(takeover).

    def heartbeat_loop(self) -> None:
        """주기적으로 HEARTBEAT 발행. 별도 스레드에서 호출."""
        while not self._shutdown:
            time.sleep(self._heartbeat_interval)
            with self._lock:
                for channel_id, handle in list(self._channels.items()):
                    if handle.process and handle.process.poll() is None:
                        self._publish(StreamEvent(
                            event=EventType.HEARTBEAT,
                            channel_id=channel_id,
                            worker_id=self.worker_id,
                            frame_count=handle.frame_count,
                            last_pts=handle.last_pts,
                        ))

    # ----- 재시작(backoff) -----
    # 프로세스가 비정상 종료되면: restart_count를 올리고, backoff_sec 동안 대기 후 재시작.
    # backoff_sec은 실패마다 증가 (예: 1, 2, 4, 8, 16). max_restarts 초과 시 FAILED 발행하고 해당 채널 제거.

    def check_exited_processes(self) -> None:
        """주기적으로 호출: 종료된 프로세스 감지 → backoff 후 재시작 또는 FAILED."""
        with self._lock:
            for channel_id, handle in list(self._channels.items()):
                if not handle.process:
                    continue
                ret = handle.process.poll()
                if ret is None:
                    continue
                # 프로세스 종료됨
                handle.process = None
                handle.restart_count += 1
                if handle.restart_count > self._max_restarts:
                    logger.error("channel_id=%s max_restarts exceeded, emitting FAILED", channel_id)
                    self._publish(StreamEvent(
                        event=EventType.FAILED,
                        channel_id=channel_id,
                        worker_id=self.worker_id,
                        job_id=handle.job_id,
                        message=f"Process exited with {ret} after {handle.restart_count} restarts",
                    ))
                    self._channels.pop(channel_id, None)
                    continue
                # backoff 후 재시작 (다음 루프에서 start_pipeline 호출하려면 스레드/스케줄러 사용)
                backoff = min(handle.backoff_sec * (2 ** (handle.restart_count - 1)), 60.0)
                logger.warning("channel_id=%s exited ret=%s, restart %s/%s in %.1fs",
                              channel_id, ret, handle.restart_count, self._max_restarts, backoff)
                # 실제로는 별도 스레드에서 time.sleep(backoff) 후 start_channel 재호출
                # 여기서는 로그만. 스켈레톤에서는 run_loop에서 타이머로 처리 가능.
                handle.backoff_sec = backoff

    def shutdown(self) -> None:
        """모든 채널 정리."""
        self._shutdown = True
        with self._lock:
            for channel_id in list(self._channels.keys()):
                self._stop_internal(channel_id)
