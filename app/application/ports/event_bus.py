"""이벤트 발행 포트 (stream.events, ai.events 등). Kafka 구현은 infrastructure에만 둠."""
from abc import ABC, abstractmethod
from typing import Any


class EventBus(ABC):
    @abstractmethod
    async def publish_event(self, topic: str, key: str, payload: dict[str, Any]) -> None:
        """Partition key=channel_id. schema_version 등은 payload에 포함."""
        ...
