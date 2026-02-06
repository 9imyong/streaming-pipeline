# CCTV 스트리밍 도메인. 상태 머신·전이·에러.
from app.domain.errors import (
    ConflictError,
    DomainError,
    InvalidTransitionError,
    StreamAlreadyRunningError,
    StreamNotFoundError,
    ValidationError,
)
from app.domain.stream_state_machine import (
    DesiredState,
    StreamState,
    can_transition,
    is_desired_satisfied,
    validate_transition,
)

__all__ = [
    "StreamState",
    "DesiredState",
    "can_transition",
    "validate_transition",
    "is_desired_satisfied",
    "DomainError",
    "InvalidTransitionError",
    "StreamNotFoundError",
    "StreamAlreadyRunningError",
    "ValidationError",
    "ConflictError",
]
