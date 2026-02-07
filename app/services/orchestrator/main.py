"""
Orchestrator 진입점.
- stream.commands 소비 → START/STOP 핸들러 → lease·assigned_worker_id 갱신.
- stream.events 소비 → HEARTBEAT 수신 시 lease 갱신.
- Lease 만료 스캐너 → 만료 시 FAILED 전이 후 START 재발행.
- Prometheus /metrics (port 9090).
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

METRICS_PORT = 9090


async def _metrics_refresh_loop(reader) -> None:
    """주기적으로 DB 기준 streams_running 갱신."""
    from app.infrastructure.observability.stream_metrics import streams_running_gauge
    while True:
        try:
            await asyncio.sleep(15)
            counts = await reader.get_status_counts()
            streams_running_gauge.set(counts.get("streams_running", 0))
        except asyncio.CancelledError:
            break
        except Exception:  # noqa: BLE001
            logger.debug("metrics refresh error", exc_info=True)


async def run() -> None:
    from app.infrastructure.messaging.kafka.consumer import KafkaConsumerBase
    from app.infrastructure.messaging.kafka.producer import KafkaProducerWrapper
    from app.infrastructure.messaging.kafka.topics import STREAM_COMMANDS, STREAM_EVENTS
    from app.infrastructure.persistence.stream_repository import DbStreamRepository
    from app.infrastructure.persistence.lease_db import DbLeaseStore
    from app.services.orchestrator.handlers import (
        handle_start,
        handle_stop,
        LEASE_TTL_SECONDS,
    )
    from app.services.orchestrator.assigner import assign_worker
    from app.services.orchestrator.lease_scanner import run_lease_expiry_scanner
    from app.infrastructure.persistence.observability_reader import DbObservabilityReader
    from app.core.observability import start_metrics_server

    start_metrics_server(METRICS_PORT)
    obs_reader = DbObservabilityReader()
    stream_repo = DbStreamRepository()
    lease_store = DbLeaseStore()
    consumer = KafkaConsumerBase(group_id="orchestrator-v1")
    await consumer.start([STREAM_COMMANDS, STREAM_EVENTS])
    producer = KafkaProducerWrapper()
    await producer.start()

    async def on_message(topic: str, value: dict) -> None:
        if topic == STREAM_EVENTS:
            if value.get("event") == "HEARTBEAT":
                ch = value.get("channel_id") or ""
                wid = value.get("worker_id") or ""
                if ch and wid:
                    await lease_store.renew(ch, wid, LEASE_TTL_SECONDS)
                    logger.debug("lease renewed channel_id=%s worker_id=%s", ch, wid)
            return
        if topic != STREAM_COMMANDS:
            return
        cmd = value.get("command")
        if cmd == "START":
            await handle_start(stream_repo, lease_store, assign_worker, value)
        elif cmd == "STOP":
            await handle_stop(stream_repo, lease_store, value)
        else:
            logger.debug("ignore command command=%s", cmd)

    scanner_task = asyncio.create_task(run_lease_expiry_scanner(stream_repo, lease_store, producer))
    metrics_task = asyncio.create_task(_metrics_refresh_loop(obs_reader))

    try:
        await consumer.run_forever(on_message)
    except asyncio.CancelledError:
        pass
    finally:
        scanner_task.cancel()
        metrics_task.cancel()
        try:
            await scanner_task
            await metrics_task
        except asyncio.CancelledError:
            pass
        await consumer.stop()
        await producer.stop()


def main() -> None:
    logger.info("Orchestrator starting metrics_port=%s", METRICS_PORT)
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
