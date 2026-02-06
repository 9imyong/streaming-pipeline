"""Command 발행 인터페이스 (Kafka stream.commands)."""
from abc import ABC, abstractmethod
from typing import Any


class CommandBus(ABC):
    @abstractmethod
    async def publish_command(self, key: str, payload: dict[str, Any]) -> None:
        """Partition key=channel_id 로 발행."""
        ...
