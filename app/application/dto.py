"""유스케이스 입출력 DTO (dataclass). API ↔ Usecase 간 전달용."""
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class StartStreamResult:
    """create_stream 유스케이스 반환값 (202 Accepted)."""
    job_id: str
    channel_id: str


@dataclass
class StreamStatusResult:
    """get_stream 유스케이스 반환값."""
    channel_id: str
    status: str
    worker_id: Optional[str] = None
    desired_state: Optional[str] = None
    last_error: Optional[str] = None
    restart_count: int = 0
    pipeline_params: Optional[dict[str, Any]] = None


@dataclass
class StartStreamRequest:
    """create_stream 유스케이스 입력 (API 요청 변환 후)."""
    channel_id: str
    source_rtsp: str
    output: str = "hls"
    ai_profile: Optional[str] = None
    idempotency_key: Optional[str] = None
