"""
ai.events 발행. snapshot_url만 포함, 이미지 바이트 전송 금지.
- 이벤트 폭주 방지: 채널별 스로틀(최소 발행 간격).
- AI 결과의 책임 주체: Inference Worker. 검출 결과 생성 및 발행은 여기서만 수행.
"""
import asyncio
import logging
import time
from typing import List

from app.application.ports.event_bus import EventBus
from app.infrastructure.messaging.kafka.schemas import ai_event_payload
from app.infrastructure.messaging.kafka.topics import AI_EVENTS

logger = logging.getLogger(__name__)

# 채널별 마지막 발행 시각. 스로틀용
_last_emit: dict[str, float] = {}
_throttle_seconds = 1.0


async def emit_ai_event(
    event_bus: EventBus,
    channel_id: str,
    snapshot_url: str,
    detections: List[dict],
    frame_pts: float | None = None,
    throttle_seconds: float = _throttle_seconds,
) -> None:
    """
    ai.events 발행. throttle: 동일 channel_id에서 throttle_seconds 미만 간격이면 스킵.
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
    await event_bus.publish_event(AI_EVENTS, channel_id, payload)
    logger.debug("ai_event channel_id=%s url=%s", channel_id, snapshot_url)
