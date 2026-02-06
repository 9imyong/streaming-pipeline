"""CommandBus Kafka 구현. stream.commands 토픽에 발행. application은 이 모듈을 직접 import 하지 않음."""
import logging
from typing import Any

from app.application.ports.command_bus import CommandBus
from app.infrastructure.messaging.kafka.producer import KafkaProducerWrapper
from app.infrastructure.messaging.kafka.schemas import command_payload
from app.infrastructure.messaging.kafka.topics import STREAM_COMMANDS

logger = logging.getLogger(__name__)


class KafkaCommandBus(CommandBus):
    """Kafka stream.commands 발행. key=channel_id."""

    def __init__(self, producer: KafkaProducerWrapper) -> None:
        self._producer = producer

    async def publish_command(self, key: str, payload: dict[str, Any]) -> None:
        # payload에 이미 command, channel_id 등 있으면 그대로 사용, schema_version은 producer에서
        if "schema_version" not in payload:
            from app.infrastructure.messaging.kafka.schemas import with_schema_version
            payload = with_schema_version(payload)
        await self._producer.send(STREAM_COMMANDS, key=key, value=payload)
        logger.info("command_bus.publish key=%s command=%s", key, payload.get("command"))
