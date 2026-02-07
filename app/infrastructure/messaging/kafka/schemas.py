"""
Kafka JSON 메시지 스키마 정의.
- schema_version 필수 (하위 호환/검증용).
- 이미지/비디오 바이트 전송 금지. URL만 허용 (snapshot_url 등).
"""
from datetime import datetime, timezone

SCHEMA_VERSION = "1.0"


def with_schema_version(payload: dict) -> dict:
    """모든 발행 메시지에 schema_version 주입."""
    return {"schema_version": SCHEMA_VERSION, **payload}


def command_payload(
    command: str,
    channel_id: str,
    job_id: str,
    idempotency_key: str,
    params: dict | None = None,
) -> dict:
    """stream.commands 페이로드. 파티션 키=channel_id."""
    return with_schema_version({
        "command": command,
        "channel_id": channel_id,
        "job_id": job_id,
        "idempotency_key": idempotency_key,
        "params": params or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


def stream_event_payload(
    event: str,
    channel_id: str,
    worker_id: str,
    job_id: str | None = None,
    message: str | None = None,
    frame_count: int | None = None,
    last_pts: float | None = None,
    last_error: str | None = None,
) -> dict:
    """stream.events 페이로드. 이미지 바이트 없음. last_error는 FAILED 시 GStreamer 등 에러 요약."""
    payload = {
        "event": event,
        "channel_id": channel_id,
        "worker_id": worker_id,
        "job_id": job_id,
        "message": message,
        "frame_count": frame_count,
        "last_pts": last_pts,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if last_error is not None:
        payload["last_error"] = last_error[:1024]
    return with_schema_version(payload)


def ai_event_payload(
    channel_id: str,
    snapshot_url: str,
    detections: list[dict],
    frame_pts: float | None = None,
) -> dict:
    """ai.events 페이로드. snapshot_url만 포함, 이미지 바이트 전송 금지."""
    return with_schema_version({
        "channel_id": channel_id,
        "snapshot_url": snapshot_url,
        "detections": detections,
        "frame_pts": frame_pts,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
