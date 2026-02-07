"""
채널별 프로세스 관리 핵심.
- lease 없으면 실행 금지. lease 상실 시 즉시 종료.
- 무한 재시작 방지 (max_restarts). 상태 변경은 Repository만.
"""
from __future__ import annotations

import asyncio
import contextlib
import dataclasses
import logging
import signal
import time
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, Optional

from app.application.ports.event_bus import EventBus
from app.application.ports.lease_store import LeaseStore
from app.application.ports.stream_repository import StreamRepository
from app.infrastructure.messaging.kafka.schemas import stream_event_payload
from app.infrastructure.messaging.kafka.topics import STREAM_EVENTS
from app.services.worker_stream.backoff import next_delay, should_stop_restarting

logger = logging.getLogger(__name__)


@dataclasses.dataclass(slots=True)
class StreamSpec:
    channel_id: str
    source_uri: str
    output_type: str
    output_uri: Optional[str]
    ai_profile: Optional[str]
    params: dict
    worker_id: str


@dataclasses.dataclass(slots=True)
class ProcHandle:
    spec: StreamSpec
    process: asyncio.subprocess.Process
    started_at: float
    restart_count: int = 0
    last_exit_code: Optional[int] = None
    stopping: bool = False


def _is_lease_valid(row: Optional[dict], worker_id: str) -> bool:
    """assigned_worker_id가 나이고 lease 만료 전인지."""
    if not row:
        return False
    if (row.get("assigned_worker_id") or "") != worker_id:
        return False
    expires = row.get("lease_expires_at")
    if not expires:
        return True
    if hasattr(expires, "timestamp"):
        return datetime.now(timezone.utc).timestamp() < expires.timestamp()
    return True  # 문자열이면 보수적으로 유효로 간주


class StreamEventPublisher:
    """EventBus로 stream.events 발행 래퍼."""

    def __init__(self, event_bus: EventBus) -> None:
        self._bus = event_bus

    async def stream_event(
        self,
        event_type: str,
        channel_id: str,
        worker_id: str,
        job_id: Optional[str] = None,
        message: Optional[str] = None,
        payload: Optional[dict] = None,
        last_error: Optional[str] = None,
    ) -> None:
        p = payload or {}
        pl = stream_event_payload(
            event=event_type,
            channel_id=channel_id,
            worker_id=worker_id,
            job_id=job_id,
            message=message,
            frame_count=p.get("frame_count"),
            last_pts=p.get("last_pts"),
            last_error=last_error or p.get("last_error"),
        )
        await self._bus.publish_event(STREAM_EVENTS, channel_id, pl)


class StreamProcessManager:
    """
    채널당 subprocess 1개. lease 없으면 시작 안 함. lease 상실 시 즉시 종료.
    재시작은 backoff + max_restarts 제한. 상태/에러는 Repository 경유만.
    """

    def __init__(
        self,
        worker_id: str,
        stream_repo: StreamRepository,
        lease_store: LeaseStore,
        event_bus: EventBus,
        runner: Any,  # spawn(spec) -> asyncio.subprocess.Process
        heartbeat_interval_sec: float = 15.0,
        lease_renew_interval_sec: float = 10.0,
        max_restarts: int = 10,
        lease_ttl_seconds: int = 30,
    ) -> None:
        self.worker_id = worker_id
        self.stream_repo = stream_repo
        self.lease_store = lease_store
        self.event_publisher = StreamEventPublisher(event_bus)
        self.runner = runner
        self.heartbeat_interval_sec = heartbeat_interval_sec
        self.lease_renew_interval_sec = lease_renew_interval_sec
        self.max_restarts = max_restarts
        self.lease_ttl_seconds = lease_ttl_seconds
        self._event_bus = event_bus
        self._procs: Dict[str, ProcHandle] = {}
        self._stop_event = asyncio.Event()

    async def run_forever(self, command_consumer: AsyncIterator[dict]) -> None:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            with contextlib.suppress(NotImplementedError):
                loop.add_signal_handler(sig, self._stop_event.set)

        tasks = [
            asyncio.create_task(self._consume_commands_loop(command_consumer), name="consume_commands"),
            asyncio.create_task(self._heartbeat_loop(), name="heartbeat"),
            asyncio.create_task(self._lease_renew_loop(), name="lease_renew"),
            asyncio.create_task(self._watch_processes_loop(), name="watch_processes"),
        ]
        await self._stop_event.wait()
        await self._shutdown(tasks)

    async def _shutdown(self, tasks: list[asyncio.Task]) -> None:
        for t in tasks:
            t.cancel()
        with contextlib.suppress(Exception):
            await asyncio.gather(*tasks, return_exceptions=True)
        for cid in list(self._procs.keys()):
            with contextlib.suppress(Exception):
                await self.stop_stream(cid, reason="shutdown")

    async def _consume_commands_loop(self, command_consumer: AsyncIterator[dict]) -> None:
        async for cmd in command_consumer:
            if self._stop_event.is_set():
                return
            if cmd.get("command") == "START":
                channel_id = cmd.get("channel_id") or ""
                # lease 없으면 실행 금지: DB에서 우리가 할당받았는지 확인
                row = await self.stream_repo.get(channel_id)
                if not _is_lease_valid(row, self.worker_id):
                    logger.debug("start skipped no lease channel_id=%s", channel_id)
                    continue
                spec = self._parse_spec(cmd)
                await self.start_stream(spec)
            elif cmd.get("command") == "STOP":
                await self.stop_stream(cmd.get("channel_id") or "", reason="command_stop")

    def _parse_spec(self, cmd: dict) -> StreamSpec:
        params = cmd.get("params") or {}
        return StreamSpec(
            channel_id=cmd.get("channel_id", ""),
            source_uri=params.get("source_rtsp", ""),
            output_type=params.get("output", "hls"),
            output_uri=None,
            ai_profile=params.get("ai_profile"),
            params=params,
            worker_id=self.worker_id,
        )

    async def start_stream(self, spec: StreamSpec) -> None:
        if spec.channel_id in self._procs:
            logger.debug("already running channel_id=%s", spec.channel_id)
            return
        try:
            proc = await self.runner.spawn(spec)
        except Exception as e:
            logger.exception("spawn failed channel_id=%s: %s", spec.channel_id, e)
            await self.stream_repo.set_last_error(spec.channel_id, str(e))
            await self.event_publisher.stream_event("FAILED", spec.channel_id, self.worker_id, message=str(e))
            return
        handle = ProcHandle(spec=spec, process=proc, started_at=time.time())
        self._procs[spec.channel_id] = handle
        await self.event_publisher.stream_event(
            "STARTED", spec.channel_id, self.worker_id,
            job_id=spec.params.get("job_id"),
            payload={"pid": proc.pid, "output_type": spec.output_type},
        )

    async def stop_stream(self, channel_id: str, reason: str) -> None:
        handle = self._procs.get(channel_id)
        if not handle:
            return
        handle.stopping = True
        proc = handle.process
        with contextlib.suppress(ProcessLookupError):
            proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            with contextlib.suppress(ProcessLookupError):
                proc.kill()
            with contextlib.suppress(Exception):
                await proc.wait()
        with contextlib.suppress(Exception):
            await self.lease_store.release(channel_id, self.worker_id)
        await self.event_publisher.stream_event(
            "STOPPED", channel_id, self.worker_id,
            payload={"reason": reason, "exit_code": proc.returncode},
        )
        self._procs.pop(channel_id, None)

    async def _heartbeat_loop(self) -> None:
        from app.services.worker_stream.heartbeat import emit_heartbeat
        while not self._stop_event.is_set():
            await asyncio.sleep(self.heartbeat_interval_sec)
            for channel_id in list(self._procs.keys()):
                with contextlib.suppress(Exception):
                    await emit_heartbeat(self._event_bus, channel_id, self.worker_id)

    async def _lease_renew_loop(self) -> None:
        """lease 갱신 실패 시 해당 채널 즉시 종료 (lease 상실)."""
        while not self._stop_event.is_set():
            await asyncio.sleep(self.lease_renew_interval_sec)
            for channel_id in list(self._procs.keys()):
                renewed = await self.lease_store.renew(channel_id, self.worker_id, self.lease_ttl_seconds)
                if not renewed:
                    logger.warning("lease renew failed channel_id=%s stopping", channel_id)
                    await self.stop_stream(channel_id, reason="lease_lost")

    async def _watch_processes_loop(self) -> None:
        while not self._stop_event.is_set():
            await asyncio.sleep(1.0)
            for channel_id, handle in list(self._procs.items()):
                proc = handle.process
                if proc.returncode is None:
                    continue
                handle.last_exit_code = proc.returncode
                if handle.stopping:
                    continue

                # stderr 수집 (FAILED 시 last_error로 발행)
                stderr_snippet: Optional[str] = None
                if proc.stderr:
                    try:
                        raw = await asyncio.wait_for(proc.stderr.read(), timeout=1.0)
                        stderr_snippet = raw.decode("utf-8", errors="replace").strip()[-2000:]
                    except (asyncio.TimeoutError, Exception):
                        pass

                # 정상 종료(0): STOPPED 발행, DB 전이, lease 해제, 재시작 없음
                if proc.returncode == 0:
                    await self.stream_repo.set_last_error(channel_id, "")
                    row = await self.stream_repo.get(channel_id)
                    current = (row or {}).get("status") or "running"
                    await self.stream_repo.transition_status(channel_id, current, "stopped")
                    await self.event_publisher.stream_event(
                        "STOPPED", channel_id, self.worker_id,
                        message="eos",
                        payload={"reason": "eos", "exit_code": 0},
                    )
                    with contextlib.suppress(Exception):
                        await self.lease_store.release(channel_id, self.worker_id)
                    self._procs.pop(channel_id, None)
                    logger.info("channel_id=%s pipeline exited normally exit_code=0", channel_id)
                    continue

                # 비정상 종료: FAILED 발행 후 재시작 로직
                err_msg = f"exit_code={proc.returncode}"
                if stderr_snippet:
                    err_msg += " " + stderr_snippet[:500]
                await self.stream_repo.set_last_error(channel_id, err_msg)
                await self.event_publisher.stream_event(
                    "FAILED", channel_id, self.worker_id,
                    message=err_msg,
                    last_error=stderr_snippet[:1024] if stderr_snippet else None,
                )

                handle.restart_count += 1
                await self.stream_repo.increment_restart_count(channel_id)
                if should_stop_restarting(handle.restart_count, self.max_restarts):
                    await self.stream_repo.set_last_error(
                        channel_id, f"max_restarts exceeded ({handle.restart_count})"
                    )
                    await self.event_publisher.stream_event(
                        "FAILED", channel_id, self.worker_id,
                        message=f"max_restarts exceeded ({handle.restart_count})",
                    )
                    await self.stop_stream(channel_id, reason="max_restart_exceeded")
                    continue
                delay = next_delay(handle.restart_count)
                logger.info("restart channel_id=%s attempt=%s delay=%.1fs", channel_id, handle.restart_count, delay)
                await asyncio.sleep(delay)
                row = await self.stream_repo.get(channel_id)
                if not _is_lease_valid(row, self.worker_id):
                    await self.stop_stream(channel_id, reason="lease_lost")
                    continue
                try:
                    new_proc = await self.runner.spawn(handle.spec)
                except Exception as e:
                    await self.stream_repo.set_last_error(channel_id, str(e))
                    continue
                handle.process = new_proc
                handle.stopping = False
