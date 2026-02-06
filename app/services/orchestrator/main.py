"""
Orchestrator 진입점. stream.commands 소비 → START/STOP 핸들러 → lease·assigned_worker_id만 갱신.
- ffmpeg/gstreamer/subprocess 실행 금지. 결정만 하고 실행은 Worker가 담당.
"""
import asyncio
import logging
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run() -> None:
    from app.infrastructure.messaging.kafka.consumer import KafkaConsumerBase
    from app.infrastructure.messaging.kafka.topics import STREAM_COMMANDS
    from app.infrastructure.persistence.stream_repository import DbStreamRepository
    from app.infrastructure.persistence.lease_db import DbLeaseStore
    from app.services.orchestrator.handlers import handle_start, handle_stop
    from app.services.orchestrator.assigner import assign_worker

    stream_repo = DbStreamRepository()
    lease_store = DbLeaseStore()
    consumer = KafkaConsumerBase(group_id="orchestrator-v1")
    await consumer.start([STREAM_COMMANDS])

    async def on_message(topic: str, value: dict) -> None:
        cmd = value.get("command")
        if cmd == "START":
            await handle_start(stream_repo, lease_store, assign_worker, value)
        elif cmd == "STOP":
            await handle_stop(stream_repo, lease_store, value)
        else:
            logger.debug("ignore command command=%s", cmd)

    try:
        await consumer.run_forever(on_message)
    except asyncio.CancelledError:
        pass
    finally:
        await consumer.stop()


def main() -> None:
    logger.info("Orchestrator starting")
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
