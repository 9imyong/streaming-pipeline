"""
API Gateway 진입점.
- POST /v1/streams: 202 Accepted (유스케이스만 호출)
- GET/DELETE /v1/streams/{channel_id}: 상태 조회, 중지
- GET /health
- lifespan에서 stream_repository, job_repository, command_bus 를 app.state에 주입.
  command_bus = KafkaCommandBus (stream.commands 발행), repository = DB 구현체.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.gateway.routes import health, streams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """리소스 초기화. Kafka Producer + KafkaCommandBus, DB Repository 주입."""
    from app.infrastructure.messaging.kafka.command_bus_kafka import KafkaCommandBus
    from app.infrastructure.messaging.kafka.producer import KafkaProducerWrapper
    from app.infrastructure.persistence.stream_repository import DbStreamRepository
    from app.infrastructure.persistence.job_repository import DbJobRepository

    producer = KafkaProducerWrapper()
    await producer.start()
    app.state._kafka_producer = producer  # shutdown 시 stop용
    app.state.command_bus = KafkaCommandBus(producer)
    app.state.stream_repository = DbStreamRepository()
    app.state.job_repository = DbJobRepository()
    logger.info("Gateway lifespan: KafkaCommandBus + DB repositories wired")
    try:
        yield
    finally:
        await producer.stop()
        logger.info("Gateway lifespan: Kafka producer stopped")


app = FastAPI(title="streaming-pipeline-gateway", version="0.1.0", lifespan=lifespan)
app.include_router(streams.router, prefix="/v1")
app.include_router(health.router)
