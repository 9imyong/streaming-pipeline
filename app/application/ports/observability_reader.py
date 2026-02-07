"""
관측성 읽기 전용 포트. stream.events 반영된 DB 상태 기준 카운터·last_error.
- API /metrics·/observability에서만 사용.
"""
from abc import ABC, abstractmethod
from typing import Any


class ObservabilityReader(ABC):
    @abstractmethod
    async def get_status_counts(self) -> dict[str, int]:
        """streams 테이블 기준: streams_running, streams_failed, restarts_total."""
        ...

    @abstractmethod
    async def get_last_errors(self, limit: int = 50) -> list[dict[str, Any]]:
        """last_error가 있는 채널 목록. [{ channel_id, last_error, status, restart_count }]."""
        ...
