"""EventBus Kafka 구현. stream.events / ai.events 발행. application은 이 모듈을 직접 import 하지 않음."""
from typing import Any

from app.application.ports.event_bus import EventBus
from app.infrastructure.messaging.kafka.producer import KafkaProducerWrapper


class KafkaEventBus(EventBus):
    """Kafka 이벤트 토픽 발행. key=channel_id."""

    def __init__(self, producer: KafkaProducerWrapper) -> None:
        self._producer = producer

    async def publish_event(self, topic: str, key: str, payload: dict[str, Any]) -> None:
        await self._producer.send(topic, key=key, value=payload)
