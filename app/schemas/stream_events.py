"""
stream.events 토픽 메시지 스키마.
Worker가 발행: STARTED, STOPPED, FAILED, HEARTBEAT.
Partition key: channel_id.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import json
from datetime import datetime, timezone


class EventType(str, Enum):
    STARTED = "STARTED"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    HEARTBEAT = "HEARTBEAT"


@dataclass
class StreamEvent:
    """stream.events 페이로드."""
    event: EventType
    channel_id: str
    worker_id: str
    job_id: Optional[str] = None
    message: Optional[str] = None       # FAILED 시 last_error 요약
    frame_count: Optional[int] = None  # HEARTBEAT 시
    last_pts: Optional[float] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self) -> str:
        return json.dumps({
            "event": self.event.value,
            "channel_id": self.channel_id,
            "worker_id": self.worker_id,
            "job_id": self.job_id,
            "message": self.message,
            "frame_count": self.frame_count,
            "last_pts": self.last_pts,
            "created_at": self.created_at,
        }, ensure_ascii=False)


# ---------------------------------------------------------------------------
# JSON 예시 (stream.events)
# ---------------------------------------------------------------------------
#
# STARTED:
# {
#   "event": "STARTED",
#   "channel_id": "cctv-01",
#   "worker_id": "worker-pod-abc",
#   "job_id": "550e8400-e29b-41d4-a716-446655440000",
#   "message": null,
#   "frame_count": null,
#   "last_pts": null,
#   "created_at": "2025-02-07T10:00:05.000000+00:00"
# }
#
# HEARTBEAT:
# {
#   "event": "HEARTBEAT",
#   "channel_id": "cctv-01",
#   "worker_id": "worker-pod-abc",
#   "job_id": null,
#   "message": null,
#   "frame_count": 12345,
#   "last_pts": 123.456,
#   "created_at": "2025-02-07T10:01:00.000000+00:00"
# }
#
# FAILED:
# {
#   "event": "FAILED",
#   "channel_id": "cctv-01",
#   "worker_id": "worker-pod-abc",
#   "job_id": "550e8400-e29b-41d4-a716-446655440000",
#   "message": "Connection refused rtsp://...",
#   "frame_count": null,
#   "last_pts": null,
#   "created_at": "2025-02-07T10:02:00.000000+00:00"
# }
