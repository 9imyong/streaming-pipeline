import asyncio
import json
from unittest.mock import AsyncMock, patch

from app.application.usecases.get_ai_latest import get_ai_latest
from app.infrastructure.redis.ai_latest_store import RedisAiLatestStore


def test_latest_round_trip_and_ttl():
    async def run():
        redis = AsyncMock()
        payload = {"channel_id": "ch1", "labels": {"person": 2}}
        redis.get.return_value = json.dumps(payload)
        store = RedisAiLatestStore()
        with patch(
            "app.infrastructure.redis.ai_latest_store.get_redis",
            new=AsyncMock(return_value=redis),
        ):
            await store.set_latest("ch1", payload, ttl_seconds=10)
            key, ttl, raw = redis.setex.call_args.args
            assert key == "ai:latest:ch1"
            assert ttl == 10
            assert json.loads(raw) == payload
            assert await get_ai_latest(store, "ch1") == payload
            redis.get.assert_awaited_once_with(key)

    asyncio.run(run())


def test_missing_or_invalid_cache():
    async def run():
        redis = AsyncMock()
        store = RedisAiLatestStore()
        with patch(
            "app.infrastructure.redis.ai_latest_store.get_redis",
            new=AsyncMock(return_value=redis),
        ):
            for raw in (None, "invalid json", "[]"):
                redis.get.return_value = raw
                assert await get_ai_latest(store, "ch1") is None

    asyncio.run(run())
