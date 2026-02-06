"""
stream.commands 토픽 메시지 스키마.
Partition key: channel_id (동일 채널은 같은 파티션 → 순서 보장).
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import json
from datetime import datetime, timezone


class CommandType(str, Enum):
    START = "START"
    STOP = "STOP"
    RESTART = "RESTART"
    UPDATE = "UPDATE"


@dataclass
class StreamCommand:
    """stream.commands 페이로드."""
    command: CommandType
    channel_id: str
    job_id: str
    idempotency_key: str  # 멱등성: 동일 키면 중복 처리 방지
    params: Optional[dict[str, Any]] = None  # pipeline_params (source_rtsp, output type 등)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())  # noqa: E501

    def to_json(self) -> str:
        return json.dumps({
            "command": self.command.value,
            "channel_id": self.channel_id,
            "job_id": self.job_id,
            "idempotency_key": self.idempotency_key,
            "params": self.params or {},
            "created_at": self.created_at,
        }, ensure_ascii=False)


# ---------------------------------------------------------------------------
# JSON 예시 (stream.commands)
# ---------------------------------------------------------------------------
#
# START:
# {
#   "command": "START",
#   "channel_id": "cctv-01",
#   "job_id": "550e8400-e29b-41d4-a716-446655440000",
#   "idempotency_key": "client-request-abc123",
#   "params": {
#     "source_rtsp": "rtsp://user:pass@host:554/stream",
#     "output": "hls",
#     "output_path": "/data/playlist/streaming/cctv-01",
#     "ai_profile": "ppe"
#   },
#   "created_at": "2025-02-07T10:00:00.000000+00:00"
# }
#
# STOP:
# {
#   "command": "STOP",
#   "channel_id": "cctv-01",
#   "job_id": "550e8400-e29b-41d4-a716-446655440001",
#   "idempotency_key": "client-stop-xyz",
#   "params": null,
#   "created_at": "2025-02-07T10:05:00.000000+00:00"
# }
