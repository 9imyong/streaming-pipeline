"""
공통 Kafka Producer 래퍼.
- partition key = channel_id (동일 채널 순서 보장).
- at-least-once: acks=all, retries 설정.
- application/domain에서는 사용 금지. CommandBus/EventBus 구현체에서만 사용.
"""
import json
import logging
from typing import Any

from app.core.config import get_settings
from app.infrastructure.messaging.kafka.schemas import with_schema_version
from app.infrastructure.messaging.kafka.topics import AI_EVENTS, STREAM_COMMANDS, STREAM_EVENTS

logger = logging.getLogger(__name__)


class KafkaProducerWrapper:
    """
    Kafka Producer. key=channel_id로 전송 (파티션 키).
    이미지/비디오 바이트 전송 금지. JSON 페이로드만.
    """

    def __init__(self, bootstrap_servers: str | None = None) -> None:
        self._bootstrap = bootstrap_servers or get_settings().kafka_bootstrap_servers
        self._producer: Any = None

    async def start(self) -> None:
        """Producer 생성. aiokafka 사용 시 비동기 시작."""
        try:
            from aiokafka import AIOKafkaProducer
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self._bootstrap,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
                acks="all",
                retries=3,
            )
            await self._producer.start()
            logger.info("Kafka producer started bootstrap=%s", self._bootstrap)
        except ImportError:
            logger.warning("aiokafka not installed, producer no-op")
            self._producer = None

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()
            self._producer = None

    async def send(self, topic: str, key: str, value: dict[str, Any]) -> None:
        """
        메시지 발행. key=channel_id (파티션 키).
        value에는 schema_version 포함 권장 (with_schema_version).
        """
        if not self._producer:
            logger.debug("producer no-op send topic=%s key=%s", topic, key)
            return
        payload = value if "schema_version" in value else with_schema_version(value)
        await self._producer.send_and_wait(
            topic,
            key=key.encode("utf-8") if isinstance(key, str) else key,
            value=payload,
        )
        logger.debug("kafka send topic=%s key=%s", topic, key)
