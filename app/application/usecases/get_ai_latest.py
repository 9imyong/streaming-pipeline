"""최신 AI 결과 조회."""
from typing import Any

from app.application.ports.ai_latest_store import AiLatestStore


async def get_ai_latest(store: AiLatestStore, channel_id: str) -> dict[str, Any] | None:
    return await store.get_latest(channel_id)
