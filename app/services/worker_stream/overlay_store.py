"""
channel_id별 최신 detection 저장소. thread-safe / async-safe.
- Inference Worker가 ai.events 수신 시 set_detections(channel_id, detections) 호출.
- SIMPLE/OSD 오버레이에서 get_detections(channel_id)로 조회.
- detection 포맷: [{x1, y1, x2, y2, score, label}] (좌표 0~1 정규화 또는 픽셀, 프로젝트에서 통일).
"""
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

_lock = asyncio.Lock()
_store: dict[str, list[dict[str, Any]]] = {}


async def set_detections(channel_id: str, detections: list[dict[str, Any]]) -> None:
    """channel_id에 대한 최신 detection 목록 저장."""
    async with _lock:
        _store[channel_id] = list(detections) if detections else []
    logger.debug("overlay_store set_detections channel_id=%s count=%s", channel_id, len(detections or []))


async def get_detections(channel_id: str) -> list[dict[str, Any]]:
    """channel_id에 대한 최신 detection 목록 조회. 없으면 []."""
    async with _lock:
        return list(_store.get(channel_id, []))
