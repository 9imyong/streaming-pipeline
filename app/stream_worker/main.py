"""
Stream Worker 진입점.
- stream.commands를 소비하거나, Orchestrator가 이 워커에게 직접 지시하는 토픽/HTTP를 구독.
- ChannelManager로 채널당 subprocess 1개 유지.
- stream.events 발행 (STARTED/STOPPED/FAILED/HEARTBEAT).
"""
import logging
import os
import signal
import sys
import threading
import time
from pathlib import Path

# 프로젝트 루트를 path에 추가
_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from app.stream_worker.channel_manager import ChannelManager
from app.schemas.stream_events import StreamEvent
from app.infrastructure.kafka.topics import STREAM_EVENTS
from app.infrastructure.kafka.client import get_producer, produce_with_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WORKER_ID = os.environ.get("WORKER_ID", "worker-default")
KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


def main() -> None:
    producer = get_producer(KAFKA_BOOTSTRAP)

    def publish_event(ev: StreamEvent) -> None:
        """stream.events 토픽에 channel_id를 key로 발행 (partition key = channel_id)."""
        # 멱등성: 동일 이벤트 중복 발행 방지는 Kafka 측에서 필요 시 메시지 키/헤더로 처리 가능.
        payload = ev.to_json().encode("utf-8")
        produce_with_key(producer, STREAM_EVENTS, ev.channel_id, payload)

    manager = ChannelManager(
        WORKER_ID,
        publish_event=publish_event,
        heartbeat_interval_sec=30.0,
        max_restarts=5,
    )

    def on_sigterm(*args) -> None:
        logger.info("SIGTERM received, shutting down")
        manager.shutdown()

    signal.signal(signal.SIGTERM, on_sigterm)

    # heartbeat 스레드
    heartbeat_thread = threading.Thread(target=manager.heartbeat_loop, daemon=True)
    heartbeat_thread.start()

    # 스켈레톤: 여기서는 무한 루프로 종료된 프로세스만 체크.
    # 실제로는 Kafka consumer loop에서 stream.commands 수신 → start_channel/stop_channel 호출.
    try:
        while True:
            manager.check_exited_processes()
            time.sleep(5)
    except KeyboardInterrupt:
        pass
    finally:
        manager.shutdown()


if __name__ == "__main__":
    main()
