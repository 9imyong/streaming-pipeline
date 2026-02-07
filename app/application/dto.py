"""유스케이스 입출력 DTO (dataclass). API ↔ Usecase 간 전달용. worker_stream runner 스펙 포함."""
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(slots=True)
class StreamSpec:
    """채널 스트리밍 파이프라인 실행 스펙. manager·runner·infrastructure 공통.
    params: overlay_mode(NONE|SIMPLE|OSD), overlay_label, source_rtsp, output 등.
    """
    channel_id: str
    source_uri: str
    output_type: str
    output_uri: Optional[str]
    ai_profile: Optional[str]
    params: dict  # overlay_mode, overlay_label, source_rtsp, output, ...
    worker_id: str


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
