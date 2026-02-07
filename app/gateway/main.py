"""
API Gateway 진입점.
- POST /v1/streams: 202 Accepted (유스케이스만 호출)
- GET/DELETE /v1/streams/{channel_id}: 상태 조회, 중지
- GET /hls/{channel_id}/index.m3u8 등: HLS 세그먼트 정적 서빙 (stream-worker와 공유 볼륨)
- GET /health
- lifespan에서 stream_repository, job_repository, command_bus 를 app.state에 주입.
  command_bus = KafkaCommandBus (stream.commands 발행), repository = DB 구현체.
"""
import logging
import os
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.gateway.routes import health, observability, streams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """리소스 초기화. COMMAND_BUS=kafka면 KafkaCommandBus, stub이면 StubCommandBus(dev/테스트)."""
    from app.core.config import get_settings
    from app.infrastructure.persistence.stream_repository import DbStreamRepository
    from app.infrastructure.persistence.job_repository import DbJobRepository

    settings = get_settings()
    from app.infrastructure.persistence.observability_reader import DbObservabilityReader
    app.state.stream_repository = DbStreamRepository()
    app.state.job_repository = DbJobRepository()
    app.state.observability_reader = DbObservabilityReader()
    from app.infrastructure.redis.ai_latest_store import RedisAiLatestStore
    app.state.ai_latest_store = RedisAiLatestStore()

    if settings.command_bus == "stub":
        from app.infrastructure.messaging.command_bus_stub import StubCommandBus
        app.state.command_bus = StubCommandBus()
        app.state._kafka_producer = None
        logger.info("Gateway lifespan: StubCommandBus (COMMAND_BUS=stub) + DB repositories wired")
    else:
        from app.infrastructure.messaging.kafka.command_bus import KafkaCommandBus
        from app.infrastructure.messaging.kafka.producer import KafkaProducerWrapper
        producer = KafkaProducerWrapper()
        await producer.start()
        app.state._kafka_producer = producer
        app.state.command_bus = KafkaCommandBus(producer)
        logger.info("Gateway lifespan: KafkaCommandBus + DB repositories wired")

    try:
        yield
    finally:
        if app.state._kafka_producer:
            await app.state._kafka_producer.stop()
            logger.info("Gateway lifespan: Kafka producer stopped")


app = FastAPI(title="streaming-pipeline-gateway", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def hls_cache_control(request: Request, call_next):
    """HLS 응답에 Cache-Control 추가. .m3u8은 no-cache, .ts는 짧은 캐시 (nginx 미사용 시 보완)."""
    response = await call_next(request)
    path = request.url.path or ""
    if path.startswith("/hls"):
        if ".m3u8" in path:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        elif ".ts" in path:
            response.headers["Cache-Control"] = "max-age=2, public"
    return response


app.include_router(streams.router, prefix="/v1")
app.include_router(observability.router, prefix="/v1")
app.include_router(health.router)

# HLS 세그먼트/플레이리스트 서빙 (stream-worker가 /data/hls 에 쓰고, api는 같은 볼륨 마운트)
_HLS_DIR = os.environ.get("HLS_SERVE_DIR", "/data/hls")
if os.path.isdir(_HLS_DIR):
    app.mount("/hls", StaticFiles(directory=_HLS_DIR), name="hls")
else:
    logging.getLogger(__name__).warning("HLS serve dir not found path=%s (skip /hls mount)", _HLS_DIR)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """500 시 로그에 traceback 남겨 원인 파악 가능하게."""
    logger.exception(
        "unhandled_exception path=%s method=%s: %s\n%s",
        request.url.path, request.method, exc, traceback.format_exc(),
    )
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
