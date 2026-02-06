"""
API Gateway 진입점.
- POST /v1/streams: 202 Accepted (유스케이스만 호출)
- GET/DELETE /v1/streams/{channel_id}: 상태 조회, 중지
- GET /health
- lifespan에서 stream_repository, job_repository, command_bus 를 app.state에 주입 (실서비스에서는 실제 구현체로 교체)
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.gateway.routes import health, streams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """리소스 초기화. 포트 구현체를 app.state에 주입 (Gateway는 이걸 통해서만 유스케이스가 DB/Kafka 사용)."""
    from app.infrastructure.messaging.command_bus_stub import StubCommandBus
    from app.infrastructure.persistence.inmem import InMemoryJobRepository, InMemoryStreamRepository

    app.state.stream_repository = InMemoryStreamRepository()
    app.state.job_repository = InMemoryJobRepository()
    app.state.command_bus = StubCommandBus()
    logger.info("Gateway lifespan: in-memory stubs wired")
    yield
    # shutdown 시 정리 (필요 시)


app = FastAPI(title="streaming-pipeline-gateway", version="0.1.0", lifespan=lifespan)
app.include_router(streams.router, prefix="/v1")
app.include_router(health.router)
