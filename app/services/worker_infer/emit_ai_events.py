"""
ai.events 발행. snapshot_url만 포함, 이미지 바이트 전송 금지.
- 이벤트 폭주 방지: 채널별 스로틀(최소 발행 간격).
- AI 결과의 책임 주체: Inference Worker. 검출 결과 생성 및 발행은 여기서만 수행.
- ai_latest_store 제공 시 Redis에 최신값 캐시 (API /ai/latest용).
"""
import logging
import time
from collections import Counter
from typing import Any, List, Optional

from app.application.ports.event_bus import EventBus
from app.application.ports.ai_latest_store import AiLatestStore
from app.infrastructure.messaging.kafka.schemas import ai_event_payload
from app.infrastructure.messaging.kafka.topics import AI_EVENTS

logger = logging.getLogger(__name__)

# 채널별 마지막 발행 시각. 스로틀용
_last_emit: dict[str, float] = {}
_throttle_seconds = 1.0
AI_LATEST_TTL = 10


def _build_ai_latest_payload(channel_id: str, ts: str, detections: List[dict]) -> dict[str, Any]:
    """API /ai/latest 응답 형식으로 payload 구성."""
    labels = Counter(
        d.get("label") or d.get("class") or "object" for d in (detections or [])
    )
    top = sorted(
        detections or [],
        key=lambda x: float(x.get("score") or 0),
        reverse=True,
    )[:5]
    top_detections = [
        {"label": d.get("label") or d.get("class"), "score": d.get("score")}
        for d in top
    ]
    return {
        "channel_id": channel_id,
        "ts": ts,
        "labels": dict(labels),
        "top_detections": top_detections,
        "source": "redis",
    }


async def emit_ai_event(
    event_bus: EventBus,
    channel_id: str,
    snapshot_url: str,
    detections: List[dict],
    frame_pts: float | None = None,
    throttle_seconds: float = _throttle_seconds,
    ai_latest_store: Optional[AiLatestStore] = None,
) -> None:
    """
    ai.events 발행. throttle: 동일 channel_id에서 throttle_seconds 미만 간격이면 스킵.
    ai_latest_store 있으면 Redis에 최신값 캐시.
    """
    now = time.monotonic()
    last = _last_emit.get(channel_id, 0.0)
    if now - last < throttle_seconds:
        logger.debug("throttle skip channel_id=%s", channel_id)
        return
    _last_emit[channel_id] = now
    payload = ai_event_payload(
        channel_id=channel_id,
        snapshot_url=snapshot_url,
        detections=detections,
        frame_pts=frame_pts,
    )
    ts = payload.get("created_at", "")
    await event_bus.publish_event(AI_EVENTS, channel_id, payload)
    if ai_latest_store:
        latest_payload = _build_ai_latest_payload(channel_id, ts, detections)
        await ai_latest_store.set_latest(channel_id, latest_payload, ttl_seconds=AI_LATEST_TTL)
    logger.debug("ai_event channel_id=%s url=%s", channel_id, snapshot_url)
