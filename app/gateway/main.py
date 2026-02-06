"""
API Gateway 진입점.
- POST /v1/streams: Job 생성(멱등) + stream.commands 발행 → 202 Accepted.
- GET/DELETE /v1/streams/{channel_id}: 상태 조회, 중지.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.gateway.routes import health, streams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="streaming-pipeline-gateway", version="0.1.0")
app.include_router(streams.router, prefix="/v1")
app.include_router(health.router)
