"""
/v1/streams 라우트.
- DB/Kafka/ffmpeg 직접 접근 금지. 유스케이스 실행기(Depends)만 호출.
- POST → 202 Accepted, DELETE → 202 Accepted, GET → 200 상태 조회, GET .../ai/latest → AI 최신값.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.application.ports.observability_reader import ObservabilityReader
from app.application.ports.stream_repository import StreamRepository
from app.gateway.deps import (
    CreateStreamRunner,
    GetStreamRunner,
    GetAiLatestRunner,
    StopStreamRunner,
    get_create_stream_use_case,
    get_get_stream_use_case,
    get_stop_stream_use_case,
    get_ai_latest_runner,
    get_observability_reader,
    get_stream_repository,
)

router = APIRouter(prefix="/streams", tags=["streams"])


# ----- 요청/응답 스키마 (Pydantic, API 계층) -----


class StartStreamRequest(BaseModel):
    channel_id: str = Field(..., description="채널 식별자")
    source_rtsp: str = Field(..., description="RTSP 소스 URL")
    output: str = Field(default="hls", description="hls | rtsp | mjpeg")
    ai_profile: str | None = Field(None, description="AI 프로파일")
    overlay_mode: str | None = Field(None, description="NONE | SIMPLE | OSD. 기본 NONE")
    overlay_label: str | None = Field(None, description="SIMPLE 시 textoverlay 텍스트")
    rtsp_transport: str | None = Field(None, description="RTSP 전송: tcp | udp. 기본 tcp")
    rtsp_latency_ms: int | None = Field(None, description="rtspsrc latency(ms). 기본 300")
    rtsp_timeout_ms: int | None = Field(None, description="rtspsrc timeout(ms). 기본 15000")
    idempotency_key: str | None = Field(None, description="멱등 키. 없으면 자동 생성")


class StartStreamResponse(BaseModel):
    job_id: str
    channel_id: str
    message: str = "Accepted"


class StreamStatusResponse(BaseModel):
    channel_id: str
    status: str
    worker_id: str | None = None
    desired_state: str | None = None
    last_error: str | None = None
    restart_count: int = 0
    updated_at: str | None = None
    pipeline_params: dict | None = None  # source_rtsp, output 등 (START 시 사용)


class AiLatestResponse(BaseModel):
    channel_id: str
    ts: str = Field(..., description="ISO timestamp of latest result")
    labels: dict[str, int] = Field(default_factory=dict, description="label -> count")
    top_detections: list[dict] = Field(default_factory=list, description="top N detections")
    source: str = Field(default="redis", description="redis | db")


class UpdateStreamParamsRequest(BaseModel):
    source_rtsp: str | None = Field(None, description="소스 RTSP/RTMP URL 갱신")
    output: str | None = Field(None, description="output 타입 갱신 (hls 등)")
    overlay_mode: str | None = None
    overlay_label: str | None = None
    rtsp_transport: str | None = Field(None, description="RTSP 전송: tcp | udp")
    rtsp_latency_ms: int | None = Field(None, description="rtspsrc latency(ms)")
    rtsp_timeout_ms: int | None = Field(None, description="rtspsrc timeout(ms)")


class StreamListItem(BaseModel):
    channel_id: str
    status: str
    desired_state: str | None = None
    assigned_worker_id: str | None = None
    restart_count: int = 0
    last_error: str | None = None
    updated_at: str | None = None


# ----- 라우트: 유스케이스만 호출 -----


@router.get("", response_model=List[StreamListItem])
async def list_streams(
    reader: ObservabilityReader = Depends(get_observability_reader),
    limit: int = 100,
) -> List[StreamListItem]:
    """채널 목록 (status, desired_state, worker_id, updated_at). UI/콘솔용."""
    rows = await reader.get_stream_list(limit=min(limit, 200))
    return [
        StreamListItem(
            channel_id=r["channel_id"],
            status=r.get("status", "pending"),
            desired_state=r.get("desired_state"),
            assigned_worker_id=r.get("assigned_worker_id"),
            restart_count=int(r.get("restart_count") or 0),
            last_error=r.get("last_error"),
            updated_at=str(r["updated_at"]) if r.get("updated_at") else None,
        )
        for r in rows
    ]


@router.post("/", response_model=StartStreamResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_stream(
    body: StartStreamRequest,
    use_case: CreateStreamRunner = Depends(get_create_stream_use_case),
) -> StartStreamResponse:
    """스트림 시작 요청. 즉시 202 Accepted + job_id 반환. 실제 시작은 Orchestrator/Worker가 수행."""
    result = await use_case.run(
        channel_id=body.channel_id,
        source_rtsp=body.source_rtsp,
        output=body.output,
        ai_profile=body.ai_profile,
        overlay_mode=body.overlay_mode,
        overlay_label=body.overlay_label,
        rtsp_transport=body.rtsp_transport,
        rtsp_latency_ms=body.rtsp_latency_ms,
        rtsp_timeout_ms=body.rtsp_timeout_ms,
        idempotency_key=body.idempotency_key,
    )
    return StartStreamResponse(job_id=result.job_id, channel_id=result.channel_id)


@router.patch("/{channel_id}", status_code=status.HTTP_200_OK)
async def update_stream_params(
    channel_id: str,
    body: UpdateStreamParamsRequest,
    stream_repo: StreamRepository = Depends(get_stream_repository),
) -> dict:
    """채널 pipeline_params 일부 갱신 (소스 URL 등). 채널 없으면 404."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        return {"channel_id": channel_id, "message": "No updates"}
    ok = await stream_repo.update_pipeline_params(channel_id, updates)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    return {"channel_id": channel_id, "message": "Updated", "updated": list(updates.keys())}


@router.delete("/{channel_id}", status_code=status.HTTP_202_ACCEPTED)
async def stop_stream(
    channel_id: str,
    use_case: StopStreamRunner = Depends(get_stop_stream_use_case),
) -> dict:
    """스트림 중지 요청. 202 Accepted."""
    await use_case.run(channel_id=channel_id)
    return {"channel_id": channel_id, "message": "Accepted"}


@router.delete("/{channel_id}/record", status_code=status.HTTP_200_OK)
async def delete_channel_record(
    channel_id: str,
    use_case: StopStreamRunner = Depends(get_stop_stream_use_case),
    stream_repo: StreamRepository = Depends(get_stream_repository),
) -> dict:
    """채널 중지 후 DB에서 삭제(목록에서 제거)."""
    await use_case.run(channel_id=channel_id)
    await stream_repo.delete(channel_id)
    return {"channel_id": channel_id, "message": "Deleted"}


@router.get("/{channel_id}/ai/latest", response_model=AiLatestResponse)
async def get_stream_ai_latest(
    channel_id: str,
    runner: GetAiLatestRunner = Depends(get_ai_latest_runner),
) -> AiLatestResponse:
    """AI 최신 결과 조회 (Redis 캐시). 없으면 200 + 빈 본문 (로그 404 방지)."""
    data = await runner.run(channel_id=channel_id)
    if not data:
        return AiLatestResponse(
            channel_id=channel_id,
            ts="",
            labels={},
            top_detections=[],
            source="redis",
        )
    return AiLatestResponse(
        channel_id=data.get("channel_id", channel_id),
        ts=data.get("ts", ""),
        labels=data.get("labels", {}),
        top_detections=data.get("top_detections", []),
        source=data.get("source", "redis"),
    )


@router.get("/{channel_id}", response_model=StreamStatusResponse)
async def get_stream_status(
    channel_id: str,
    use_case: GetStreamRunner = Depends(get_get_stream_use_case),
) -> StreamStatusResponse:
    """스트림 상태 조회. 유스케이스를 통해서만 저장소 접근."""
    result = await use_case.run(channel_id=channel_id)
    return StreamStatusResponse(
        channel_id=result.channel_id,
        status=result.status,
        worker_id=result.worker_id,
        desired_state=result.desired_state,
        last_error=result.last_error,
        restart_count=getattr(result, "restart_count", 0),
        updated_at=None,
        pipeline_params=getattr(result, "pipeline_params", None),
    )
