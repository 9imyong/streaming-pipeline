"""Redis에 최신 AI 결과를 JSON과 TTL로 저장한다."""
import json
from typing import Any

from app.application.ports.ai_latest_store import AiLatestStore
from app.infrastructure.redis.client import get_redis


class RedisAiLatestStore(AiLatestStore):
    async def get_latest(self, channel_id: str) -> dict[str, Any] | None:
        redis = await get_redis()
        if redis is None:
            return None
        raw = await redis.get(f"ai:latest:{channel_id}")
        if raw is None:
            return None
        try:
            payload = json.loads(raw)
        except (ValueError, TypeError):
            return None
        return payload if isinstance(payload, dict) else None

    async def set_latest(
        self, channel_id: str, payload: dict[str, Any], ttl_seconds: int = 10
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        redis = await get_redis()
        if redis is not None:
            await redis.setex(
                f"ai:latest:{channel_id}", ttl_seconds, json.dumps(payload, ensure_ascii=False)
            )
