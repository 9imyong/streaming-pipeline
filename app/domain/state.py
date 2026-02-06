"""상태 머신(전이 규칙) 재노출. 진입점: stream_state_machine."""
from app.domain.stream_state_machine import (
    ALLOWED_TRANSITIONS,
    DesiredState,
    StreamState,
    can_transition,
    is_desired_satisfied,
    validate_transition,
    transition_or_raise,
)

# 이전 코드 호환: StreamStatus -> StreamState
StreamStatus = StreamState

__all__ = [
    "StreamState",
    "StreamStatus",
    "DesiredState",
    "ALLOWED_TRANSITIONS",
    "can_transition",
    "validate_transition",
    "transition_or_raise",
    "is_desired_satisfied",
]
