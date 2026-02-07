"""
추론 요청 핸들러. URL/프레임 수신 → 스냅샷 저장 → URL 생성 → pipeline.detect() → ai.events 발행.
- 이미지 바이트는 Kafka에 넣지 않음. 저장 후 URL만 이벤트에 포함.
"""
import logging
import uuid
from typing import Any

from app.application.ports.event_bus import EventBus
from app.application.ports.ai_latest_store import AiLatestStore
from app.services.worker_infer.pipeline import detect
from app.services.worker_infer.emit_ai_events import emit_ai_event

logger = logging.getLogger(__name__)


async def save_snapshot_and_get_url(image_bytes: bytes, channel_id: str) -> str:
    """
    스냅샷 저장 후 URL 반환. 실제 구현은 Object Storage 또는 로컬 경로 + base URL.
    """
    # 스텁: 로컬 경로 또는 S3 등에 저장 후 URL 반환
    name = f"{channel_id}/{uuid.uuid4().hex}.jpg"
    return f"https://storage.example.com/snapshots/{name}"


async def handle_inference_request(
    event_bus: EventBus,
    channel_id: str,
    image_url: str | None = None,
    image_bytes: bytes | None = None,
    frame_pts: float | None = None,
    ai_latest_store: AiLatestStore | None = None,
) -> None:
    """
    추론 1건 처리. 이미지 URL이면 다운로드 후 detect; 바이트면 저장 후 URL 생성해 detect.
    결과는 Inference Worker가 책임지고 ai.events에만 발행 (snapshot_url + detections).
    """
    if image_bytes:
        snapshot_url = await save_snapshot_and_get_url(image_bytes, channel_id)
    elif image_url:
        snapshot_url = image_url
    else:
        logger.warning("handle_inference_request no image_url or image_bytes")
        return
    detections = detect(image_url=snapshot_url, image_bytes=image_bytes)
    await emit_ai_event(
        event_bus, channel_id, snapshot_url, detections, frame_pts,
        ai_latest_store=ai_latest_store,
    )
