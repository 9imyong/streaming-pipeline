"""
channel_id별 최신 추론 결과 캐시. TTL 기반, thread-safe.
- Inference Worker(또는 ai.events 소비 측)가 set_detections 호출.
- Stream Worker 오버레이에서 get_detections_sync로 조회 (GStreamer 스레드용).
- 캐시 비어있거나 TTL 만료 시 오버레이 생략 또는 기본 텍스트.
- 데이터 포맷: detections = [{label, x1?, y1?, x2?, y2?, score?}, ...]
"""
import logging
import threading
import time
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_store: dict[str, dict[str, Any]] = {}  # channel_id -> { "detections": [...], "ts": monotonic }
TTL_SECONDS = 2.0


def set_detections_sync(channel_id: str, detections: list[dict[str, Any]]) -> None:
    """채널별 최신 detection 저장 (thread-safe). 호출: Inference Worker 또는 ai.events 소비 측."""
    with _lock:
        _store[channel_id] = {
            "detections": list(detections) if detections else [],
            "ts": time.monotonic(),
        }
    logger.debug("overlay_store set_detections channel_id=%s count=%s", channel_id, len(detections or []))


def get_detections_sync(channel_id: str) -> list[dict[str, Any]]:
    """
    TTL 내 최신 detection 목록 반환. 만료 또는 없으면 [].
    GStreamer 스레드 등 sync 컨텍스트에서 호출.
    """
    with _lock:
        ent = _store.get(channel_id)
        if not ent:
            return []
        if time.monotonic() - ent["ts"] > TTL_SECONDS:
            return []
        return list(ent["detections"])


def format_detections_to_label_string(detections: list[dict[str, Any]], max_items: int = 5) -> str:
    """
    예: "person=3, car=1". label 필드 기준 카운트. bbox 개수만 사용, 좌표는 사용하지 않음.
    비어있으면 "" (오버레이 생략 시 사용).
    """
    if not detections:
        return ""
    labels = [d.get("label") or d.get("class") or "object" for d in detections]
    counts = Counter(labels)
    parts = [f"{k}={v}" for k, v in sorted(counts.items())[:max_items]]
    return ", ".join(parts) if parts else ""


async def set_detections(channel_id: str, detections: list[dict[str, Any]]) -> None:
    """async 래퍼 (기존 호환). Inference Worker 등에서 호출."""
    import asyncio
    await asyncio.to_thread(set_detections_sync, channel_id, detections)


async def get_detections(channel_id: str) -> list[dict[str, Any]]:
    """async 래퍼. TTL 적용된 결과."""
    import asyncio
    return await asyncio.to_thread(get_detections_sync, channel_id)
