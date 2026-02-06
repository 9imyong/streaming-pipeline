"""
비동기 Redis 클라이언트. lease/cache/idempotency/rate_limit 모듈에서 공통 사용.
- Kafka·DB 접근 없음.
"""
import logging
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_redis: Any = None


async def get_redis() -> Any:
    """싱글톤 async Redis 연결. redis.asyncio 사용."""
    global _redis
    if _redis is not None:
        return _redis
    try:
        from redis.asyncio import Redis
        s = get_settings()
        _redis = Redis(host=s.redis_host, port=s.redis_port, db=0, decode_responses=True)
        await _redis.ping()
        logger.info("Redis connected %s:%s", s.redis_host, s.redis_port)
        return _redis
    except ImportError:
        logger.warning("redis package not installed, Redis features disabled")
        return None


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None
