"""
Stream Worker 진입점. stream.commands 소비 → lease 확인 후 채널당 subprocess 실행.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _command_iterator(consumer):
    """Kafka 메시지를 command dict 스트림으로 변환."""
    async for topic, _part, _offset, value in consumer.iterate():
        if value and value.get("command"):
            yield value


async def run() -> None:
    from app.infrastructure.messaging.kafka.consumer import KafkaConsumerBase
    from app.infrastructure.messaging.kafka.producer import KafkaProducerWrapper
    from app.infrastructure.messaging.kafka.topics import STREAM_COMMANDS
    from app.infrastructure.messaging.kafka.event_bus_kafka import KafkaEventBus
    from app.infrastructure.persistence.stream_repository import DbStreamRepository
    from app.infrastructure.persistence.lease_db import DbLeaseStore
    from app.services.worker_stream.manager import StreamProcessManager
    from app.services.worker_stream.runner import StubStreamRunner

    worker_id = os.environ.get("WORKER_ID") or os.environ.get("HOSTNAME", "worker-1")
    producer = KafkaProducerWrapper()
    await producer.start()
    event_bus = KafkaEventBus(producer)
    stream_repo = DbStreamRepository()
    lease_store = DbLeaseStore()
    consumer = KafkaConsumerBase(group_id="stream-worker-v1")
    await consumer.start([STREAM_COMMANDS])
    command_iter = _command_iterator(consumer)
    runner = StubStreamRunner()
    manager = StreamProcessManager(
        worker_id=worker_id,
        stream_repo=stream_repo,
        lease_store=lease_store,
        event_bus=event_bus,
        runner=runner,
    )
    try:
        await manager.run_forever(command_iter)
    finally:
        await consumer.stop()
        await producer.stop()


def main() -> None:
    logger.info("Stream Worker starting")
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
