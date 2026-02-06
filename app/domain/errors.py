"""
도메인 에러 정의. API/인프라에서 HTTP·재시도 정책으로 매핑.
- Kafka, DB, subprocess 없음. 순수 예외 타입만.
"""

from typing import Any


class DomainError(Exception):
    """도메인 규칙 위반 공통 베이스."""

    def __init__(self, message: str, **details: Any) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


# -----------------------------------------------------------------------------
# 상태 전이
# -----------------------------------------------------------------------------


class InvalidTransitionError(DomainError):
    """허용되지 않은 상태 전이 시도."""

    def __init__(self, from_state: str, to_state: str) -> None:
        super().__init__(
            f"Invalid transition: {from_state} -> {to_state}",
            from_state=from_state,
            to_state=to_state,
        )
        self.from_state = from_state
        self.to_state = to_state


# -----------------------------------------------------------------------------
# 스트림/채널
# -----------------------------------------------------------------------------


class StreamNotFoundError(DomainError):
    """해당 채널 스트림이 없음 (조회/중지 시)."""

    def __init__(self, channel_id: str) -> None:
        super().__init__(f"Stream not found: {channel_id}", channel_id=channel_id)
        self.channel_id = channel_id


class StreamAlreadyRunningError(DomainError):
    """이미 RUNNING인 채널에 START 요청 (멱등이 아닌 경우)."""

    def __init__(self, channel_id: str) -> None:
        super().__init__(f"Stream already running: {channel_id}", channel_id=channel_id)
        self.channel_id = channel_id


# -----------------------------------------------------------------------------
# 입력/검증 (도메인 규칙)
# -----------------------------------------------------------------------------


class ValidationError(DomainError):
    """입력이 도메인 규칙에 맞지 않음 (예: 빈 channel_id)."""
    pass


class ConflictError(DomainError):
    """멱등/중복 등 충돌 (예: 동일 idempotency_key로 이미 처리됨)."""
    pass
