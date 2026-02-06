"""
ai.events 토픽 메시지 스키마.
Inference Worker가 발행. 이미지 바이트 대신 snapshot_url만 포함 (대역/저장 부담 감소).
"""
from dataclasses import dataclass, field
from typing import Any, List, Optional
import json
from datetime import datetime, timezone


@dataclass
class DetectionResult:
    """단일 검출 결과 (예: bbox, class, score)."""
    class_name: str
    score: float
    bbox: Optional[list[float]] = None  # [x1, y1, x2, y2] 정규화 등


@dataclass
class AIEvent:
    """ai.events 페이로드. snapshot_url만 포함, 이미지 바이트 없음."""
    channel_id: str
    snapshot_url: str  # 스냅샷 이미지 URL (Object Storage 또는 워커 로컬 URL)
    detections: List[dict[str, Any]]  # DetectionResult 직렬화
    frame_pts: Optional[float] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self) -> str:
        return json.dumps({
            "channel_id": self.channel_id,
            "snapshot_url": self.snapshot_url,
            "detections": self.detections,
            "frame_pts": self.frame_pts,
            "created_at": self.created_at,
        }, ensure_ascii=False)


# ---------------------------------------------------------------------------
# JSON 예시 (ai.events)
# ---------------------------------------------------------------------------
#
# {
#   "channel_id": "cctv-01",
#   "snapshot_url": "https://storage.example.com/snapshots/cctv-01/20250207/100005.jpg",
#   "detections": [
#     { "class_name": "helmet", "score": 0.95, "bbox": [0.1, 0.2, 0.3, 0.4] },
#     { "class_name": "person", "score": 0.88, "bbox": [0.5, 0.1, 0.9, 0.8] }
#   ],
#   "frame_pts": 123.456,
#   "created_at": "2025-02-07T10:00:05.000000+00:00"
# }
