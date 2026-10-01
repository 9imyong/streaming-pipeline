"""채널별 최신 AI 결과 캐시 포트."""
from abc import ABC, abstractmethod
from typing import Any


class AiLatestStore(ABC):
    @abstractmethod
    async def get_latest(self, channel_id: str) -> dict[str, Any] | None:
        """캐시가 없거나 만료되면 None을 반환한다."""
        ...

    @abstractmethod
    async def set_latest(
        self, channel_id: str, payload: dict[str, Any], ttl_seconds: int = 10
    ) -> None:
        """최신 결과를 TTL과 함께 저장한다."""
        ...
