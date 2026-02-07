"""
Kafka Consumer 기본 클래스.
- group_id로 소비 그룹. partition key=channel_id 기준 토픽 구독.
- at-least-once: 처리 후 commit. application/domain에서는 사용 금지.
"""
import asyncio
import json
import logging
from typing import Any, AsyncIterator, Callable, Awaitable

from app.core.config import get_settings

logger = logging.getLogger(__name__)

KAFKA_CONNECT_RETRIES = 15
KAFKA_CONNECT_SLEEP_SEC = 2


class KafkaConsumerBase:
    """
    Consumer 래퍼. subscribe(topic) 후 iterate 또는 run_forever.
    메시지 value는 schema_version 포함 JSON.
    """

    def __init__(
        self,
        group_id: str,
        bootstrap_servers: str | None = None,
    ) -> None:
        self._group_id = group_id
        self._bootstrap = bootstrap_servers or get_settings().kafka_bootstrap_servers
        self._consumer: Any = None

    async def start(self, topics: list[str]) -> None:
        try:
            from aiokafka import AIOKafkaConsumer
            last_exc = None
            for attempt in range(1, KAFKA_CONNECT_RETRIES + 1):
                c = AIOKafkaConsumer(
                    *topics,
                    bootstrap_servers=self._bootstrap,
                    group_id=self._group_id,
                    value_deserializer=lambda v: json.loads(v.decode("utf-8")) if v else {},
                    auto_offset_reset="earliest",
                )
                try:
                    await c.start()
                    self._consumer = c
                    logger.info("Kafka consumer started group_id=%s topics=%s", self._group_id, topics)
                    return
                except Exception as e:
                    last_exc = e
                    try:
                        await c.stop()
                    except Exception:
                        pass
                    if attempt < KAFKA_CONNECT_RETRIES:
                        logger.warning(
                            "Kafka consumer connect attempt %s/%s failed: %s, retrying in %ss",
                            attempt, KAFKA_CONNECT_RETRIES, e, KAFKA_CONNECT_SLEEP_SEC,
                        )
                        await asyncio.sleep(KAFKA_CONNECT_SLEEP_SEC)
            logger.error("Kafka consumer connect failed after %s attempts: %s", KAFKA_CONNECT_RETRIES, last_exc)
            raise last_exc
        except ImportError:
            logger.warning("aiokafka not installed, consumer no-op")
            self._consumer = None

    async def stop(self) -> None:
        if self._consumer:
            await self._consumer.stop()
            self._consumer = None

    async def consume_one(self) -> tuple[str, int, int, dict] | None:
        """한 건 폴링. (topic, partition, offset, value_dict). 없으면 None."""
        if not self._consumer:
            return None
        msg = await self._consumer.getone()
        if msg is None:
            return None
        return (msg.topic, msg.partition, msg.offset, (msg.value or {}))

    async def iterate(self) -> AsyncIterator[tuple[str, int, int, dict]]:
        """메시지 비동기 이터레이터."""
        while self._consumer:
            one = await self.consume_one()
            if one is None:
                continue
            yield one

    async def run_forever(
        self,
        handler: Callable[[str, dict], Awaitable[None]],
    ) -> None:
        """메시지 수신 시 handler(topic, value) 호출. commit은 handler 성공 후."""
        async for topic, _part, offset, value in self.iterate():
            try:
                await handler(topic, value)
                if self._consumer:
                    await self._consumer.commit()
            except Exception as e:  # noqa: BLE001
                logger.exception("consumer handler error topic=%s offset=%s: %s", topic, offset, e)
                # at-least-once: 실패 시 commit 안 함 → 재처리
