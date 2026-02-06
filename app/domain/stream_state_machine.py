"""
Stream 상태 머신: 상태(State) + 허용 전이(Transition).

- desired_state: 사용자/API가 원하는 상태 (RUNNING, STOPPED)
- status: 실제 현재 상태 (워커/오케스트레이터가 보고)
- lease: 특정 워커가 해당 채널을 점유한 경우에만 RUNNING 유지 가능.
"""
from enum import Enum
from typing import Set, Tuple

# ---------------------------------------------------------------------------
# 상태 정의
# ---------------------------------------------------------------------------


class StreamStatus(str, Enum):
    """실제 스트림 상태 (DB status 컬럼)."""
    IDLE = "idle"                     # 초기/미할당
    STARTING = "starting"             # 명령 수신, 워커 할당 대기 또는 파이프라인 기동 중
    RUNNING = "running"               # 파이프라인 실행 중, heartbeat 수신
    STOPPING = "stopping"             # 중지 명령 처리 중
    STOPPED = "stopped"               # 정상 종료
    FAILED = "failed"                 # 오류로 종료, last_error 기록
    LOST = "lost"                     # lease 만료 등으로 워커 응답 없음 (takeover 대상)


class DesiredState(str, Enum):
    """사용자가 원하는 상태 (DB desired_state)."""
    RUNNING = "running"
    STOPPED = "stopped"


# ---------------------------------------------------------------------------
# 허용 전이 (from_status -> to_status)
# ---------------------------------------------------------------------------

ALLOWED_TRANSITIONS: Set[Tuple[StreamStatus, StreamStatus]] = {
    # IDLE: 오직 STARTING 또는 STOPPED 로만 진입; STARTING 또는 유지
    (StreamStatus.IDLE, StreamStatus.STARTING),
    (StreamStatus.IDLE, StreamStatus.IDLE),
    # STARTING: RUNNING(성공), FAILED(실패), STOPPING(중지 요청)
    (StreamStatus.STARTING, StreamStatus.RUNNING),
    (StreamStatus.STARTING, StreamStatus.FAILED),
    (StreamStatus.STARTING, StreamStatus.STOPPING),
    # RUNNING: STOPPING, FAILED, LOST(heartbeat 끊김)
    (StreamStatus.RUNNING, StreamStatus.STOPPING),
    (StreamStatus.RUNNING, StreamStatus.FAILED),
    (StreamStatus.RUNNING, StreamStatus.LOST),
    (StreamStatus.RUNNING, StreamStatus.RUNNING),  # heartbeat 갱신
    # STOPPING: STOPPED, FAILED
    (StreamStatus.STOPPING, StreamStatus.STOPPED),
    (StreamStatus.STOPPING, StreamStatus.FAILED),
    # STOPPED: STARTING(재시작)
    (StreamStatus.STOPPED, StreamStatus.STARTING),
    (StreamStatus.STOPPED, StreamStatus.STOPPED),
    # FAILED: STARTING(재시도), STOPPED(수동 정리)
    (StreamStatus.FAILED, StreamStatus.STARTING),
    (StreamStatus.FAILED, StreamStatus.STOPPED),
    # LOST: STARTING(다른 워커가 takeover)
    (StreamStatus.LOST, StreamStatus.STARTING),
    (StreamStatus.LOST, StreamStatus.LOST),
}


def can_transition(from_status: StreamStatus, to_status: StreamStatus) -> bool:
    """허용된 전이인지 검사 (DB/오케스트레이터에서 사용)."""
    return (from_status, to_status) in ALLOWED_TRANSITIONS


def transition_or_raise(from_status: StreamStatus, to_status: StreamStatus) -> None:
    """허용되지 않은 전이면 ValueError."""
    if not can_transition(from_status, to_status):
        raise ValueError(
            f"Invalid stream transition: {from_status.value} -> {to_status.value}"
        )


# ---------------------------------------------------------------------------
# 표: 상태 전이 (문서용)
# ---------------------------------------------------------------------------
#
# | 현재 상태  | 다음 상태   | 트리거 / 비고 |
# |------------|------------|----------------|
# | IDLE       | STARTING   | START 명령 수신, lease 할당 |
# | IDLE       | IDLE       | (유지) |
# | STARTING   | RUNNING    | stream.events STARTED 수신 |
# | STARTING   | FAILED     | stream.events FAILED 또는 타임아웃 |
# | STARTING   | STOPPING   | STOP 명령 수신 |
# | RUNNING    | STOPPING   | STOP 명령 수신 |
# | RUNNING    | FAILED     | stream.events FAILED |
# | RUNNING    | LOST       | lease_expires_at 경과, heartbeat 없음 |
# | RUNNING    | RUNNING    | HEARTBEAT 수신 (갱신만) |
# | STOPPING   | STOPPED    | stream.events STOPPED |
# | STOPPING   | FAILED     | 정리 중 오류 |
# | STOPPED    | STARTING   | START 명령 (재시작) |
# | FAILED     | STARTING   | RESTART 명령 (backoff 후) |
# | FAILED     | STOPPED    | 수동 정리 |
# | LOST       | STARTING   | Orchestrator가 다른 워커에 재할당 (takeover) |
