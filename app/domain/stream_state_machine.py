"""
CCTV 스트리밍 도메인: 상태 머신 + 전이 규칙 (Single Source of Truth).
- Kafka, DB, subprocess 접근 금지. 순수 Python.
"""

from enum import Enum
from typing import Set, Tuple

# =============================================================================
# 1. 상태 정의
# =============================================================================


class StreamState(str, Enum):
    """스트림 실제 상태 (DB status 등에 저장)."""
    PENDING = "pending"      # 시작 요청됨, 워커 할당 대기
    ASSIGNED = "assigned"    # 워커 할당됨, 파이프라인 기동 중
    RUNNING = "running"      # 파이프라인 실행 중
    FAILED = "failed"       # 오류로 종료
    STOPPED = "stopped"      # 정상 중지됨


class DesiredState(str, Enum):
    """사용자가 원하는 상태 (API: RUNNING=시작 요청, STOPPED=중지 요청)."""
    RUNNING = "running"
    STOPPED = "stopped"


# =============================================================================
# 2. 허용 전이 (한 눈에 보는 규칙)
# =============================================================================
#
#   PENDING ──(할당)──► ASSIGNED
#      │                    │
#      │                    ├──(기동 성공)──► RUNNING
#      │                    ├──(기동 실패)──► FAILED
#      │                    └──(중지 명령)──► STOPPED
#      │
#      └──(중지/취소)──► STOPPED
#
#   RUNNING ──(중지)──► STOPPED
#      │
#      └──(오류)──────► FAILED
#
#   FAILED ──(재시도)──► PENDING
#      │
#      └──(정리)──────► STOPPED
#
#   STOPPED ──(재시작)──► PENDING
#
# =============================================================================

ALLOWED_TRANSITIONS: Set[Tuple[StreamState, StreamState]] = {
    (StreamState.PENDING, StreamState.ASSIGNED),
    (StreamState.PENDING, StreamState.STOPPED),
    (StreamState.PENDING, StreamState.PENDING),
    (StreamState.ASSIGNED, StreamState.RUNNING),
    (StreamState.ASSIGNED, StreamState.FAILED),
    (StreamState.ASSIGNED, StreamState.STOPPED),
    (StreamState.ASSIGNED, StreamState.ASSIGNED),
    (StreamState.RUNNING, StreamState.STOPPED),
    (StreamState.RUNNING, StreamState.FAILED),
    (StreamState.RUNNING, StreamState.RUNNING),  # heartbeat 갱신
    (StreamState.FAILED, StreamState.PENDING),
    (StreamState.FAILED, StreamState.STOPPED),
    (StreamState.FAILED, StreamState.FAILED),
    (StreamState.STOPPED, StreamState.PENDING),
    (StreamState.STOPPED, StreamState.STOPPED),
}


# =============================================================================
# 3. 전이 검증
# =============================================================================


def can_transition(from_state: StreamState, to_state: StreamState) -> bool:
    """허용된 전이인지 검사."""
    return (from_state, to_state) in ALLOWED_TRANSITIONS


def validate_transition(from_state: StreamState, to_state: StreamState) -> None:
    """
    허용된 전이만 허용. 아니면 도메인 에러 발생.
    오케스트레이터/인프라에서 상태 갱신 전에 호출.
    """
    if not can_transition(from_state, to_state):
        from app.domain.errors import InvalidTransitionError
        raise InvalidTransitionError(
            from_state=from_state.value,
            to_state=to_state.value,
        )


def transition_or_raise(from_state: StreamState, to_state: StreamState) -> None:
    """validate_transition 별칭 (기존 호환)."""
    validate_transition(from_state, to_state)


# =============================================================================
# 4. desired_state vs 현재 상태 (규칙)
# =============================================================================


def is_desired_satisfied(current: StreamState, desired: DesiredState) -> bool:
    """현재 상태가 desired_state를 만족하는지."""
    if desired == DesiredState.RUNNING:
        return current == StreamState.RUNNING
    if desired == DesiredState.STOPPED:
        return current in (StreamState.STOPPED, StreamState.PENDING, StreamState.FAILED)
    return False
