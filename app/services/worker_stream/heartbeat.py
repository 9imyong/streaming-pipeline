"""
stream.events HEARTBEAT 발행. Worker가 주기적으로 호출.
- 이미지/비디오 바이트 전송 금지. frame_count, last_pts 등 메타만.
"""
import logging
from typing import Optional

from app.application.ports.event_bus import EventBus
from app.infrastructure.messaging.kafka.schemas import stream_event_payload
from app.infrastructure.messaging.kafka.topics import STREAM_EVENTS

logger = logging.getLogger(__name__)


async def emit_heartbeat(
    event_bus: EventBus,
    channel_id: str,
    worker_id: str,
    frame_count: Optional[int] = None,
    last_pts: Optional[float] = None,
) -> None:
    """HEARTBEAT 이벤트 발행. schema_version은 payload에 포함."""
    payload = stream_event_payload(
        event="HEARTBEAT",
        channel_id=channel_id,
        worker_id=worker_id,
        frame_count=frame_count,
        last_pts=last_pts,
    )
    await event_bus.publish_event(STREAM_EVENTS, channel_id, payload)
    logger.debug("heartbeat channel_id=%s worker_id=%s", channel_id, worker_id)
