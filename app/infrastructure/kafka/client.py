"""
Kafka Producer/Consumer 설정.
- Partition key: channel_id 사용 (동일 채널 순서 보장, 워커별 분산).
"""
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# 실제 구현 시: from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
# 또는 confluent_kafka 등 사용


def get_producer(bootstrap_servers: str = "localhost:9092") -> Any:
    """Producer 인스턴스 (라이브러리 선택에 따라 교체)."""
    # return AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
    return None  # 스켈레톤


def get_consumer(
    topic: str,
    group_id: str,
    bootstrap_servers: str = "localhost:9092",
) -> Any:
    """Consumer 인스턴스. Partition key 기준으로 같은 채널은 같은 파티션."""
    # return AIOKafkaConsumer(topic, bootstrap_servers=..., group_id=group_id)
    return None  # 스켈레톤


def produce_with_key(
    producer: Any,
    topic: str,
    key: str,  # channel_id
    value: bytes,
) -> None:
    """Partition key = channel_id 로 전송."""
    # await producer.send(topic, key=key.encode(), value=value)
    logger.info("produce_with_key %s key=%s", topic, key)
