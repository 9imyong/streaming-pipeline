"""
/v1/streams 라우트.
- DB/Kafka/ffmpeg 직접 접근 금지. 유스케이스 실행기(Depends)만 호출.
- POST → 202 Accepted, DELETE → 202 Accepted, GET → 200 상태 조회.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.gateway.deps import (
    CreateStreamRunner,
    GetStreamRunner,
    StopStreamRunner,
    get_create_stream_use_case,
    get_get_stream_use_case,
    get_stop_stream_use_case,
)

router = APIRouter(prefix="/streams", tags=["streams"])


# ----- 요청/응답 스키마 (Pydantic, API 계층) -----


class StartStreamRequest(BaseModel):
    channel_id: str = Field(..., description="채널 식별자")
    source_rtsp: str = Field(..., description="RTSP 소스 URL")
    output: str = Field(default="hls", description="hls | rtsp | mjpeg")
    ai_profile: str | None = Field(None, description="AI 프로파일")
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


# ----- 라우트: 유스케이스만 호출 -----


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
        idempotency_key=body.idempotency_key,
    )
    return StartStreamResponse(job_id=result.job_id, channel_id=result.channel_id)


@router.delete("/{channel_id}", status_code=status.HTTP_202_ACCEPTED)
async def stop_stream(
    channel_id: str,
    use_case: StopStreamRunner = Depends(get_stop_stream_use_case),
) -> dict:
    """스트림 중지 요청. 202 Accepted."""
    await use_case.run(channel_id=channel_id)
    return {"channel_id": channel_id, "message": "Accepted"}


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
    )
