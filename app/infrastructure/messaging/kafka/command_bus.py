"""
CommandBus Kafka 구현. stream.commands 토픽에 발행.
- application/ports/command_bus.py 인터페이스 구현.
- Kafka message key = channel_id. schema_version, command, channel_id 등 schemas 규칙 준수.
"""
import logging
from typing import Any

from app.application.ports.command_bus import CommandBus
from app.infrastructure.messaging.kafka.producer import KafkaProducerWrapper
from app.infrastructure.messaging.kafka.topics import STREAM_COMMANDS

logger = logging.getLogger(__name__)


class KafkaCommandBus(CommandBus):
    """Kafka stream.commands 발행. key=channel_id."""

    def __init__(self, producer: KafkaProducerWrapper) -> None:
        self._producer = producer

    async def publish_command(self, key: str, payload: dict[str, Any]) -> None:
        if "schema_version" not in payload:
            from app.infrastructure.messaging.kafka.schemas import with_schema_version
            payload = with_schema_version(payload)
        await self._producer.send(STREAM_COMMANDS, key=key, value=payload)
        command_id = payload.get("command_id") or payload.get("job_id") or ""
        logger.info(
            "command_bus.publish command_id=%s channel_id=%s type=%s",
            command_id, key, payload.get("command"),
        )
