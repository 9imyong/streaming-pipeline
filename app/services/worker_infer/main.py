"""
Inference Worker 진입점. lifespan에서 모델 1회 로드 → 추론 요청 소비 → ai.events 발행.
- 스트리밍 파이프라인 유지 금지. 이미지 바이트 Kafka 전송 금지. 이벤트 스로틀 적용.
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


async def lifespan_load_model() -> None:
    from app.services.worker_infer.pipeline import load_model
    load_model()


async def run() -> None:
    from app.infrastructure.messaging.kafka.producer import KafkaProducerWrapper
    from app.infrastructure.messaging.kafka.event_bus_kafka import KafkaEventBus
    from app.services.worker_infer.handlers import handle_inference_request

    await lifespan_load_model()
    producer = KafkaProducerWrapper()
    await producer.start()
    event_bus = KafkaEventBus(producer)
    # 스텁: 실제로는 inference 요청 토픽/큐 소비 루프에서 handle_inference_request 호출
    logger.info("Inference Worker ready (stub loop)")
    try:
        while True:
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        pass
    finally:
        await producer.stop()


def main() -> None:
    logger.info("Inference Worker starting")
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
