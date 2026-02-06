"""
/v1/streams 라우트.
- 멱등성: POST 시 idempotency_key로 동일 요청 재전송 시 기존 job 반환 또는 202 + 동일 job_id.
- Control DB jobs 테이블에 idempotency_key UNIQUE 제약으로 중복 삽입 방지.
"""
import uuid
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/streams", tags=["streams"])


# ----- 스키마 (Pydantic) -----
from pydantic import BaseModel, Field


class StartStreamRequest(BaseModel):
    channel_id: str = Field(..., description="채널 식별자")
    source_rtsp: str = Field(..., description="RTSP 소스 URL")
    output: str = Field(default="hls", description="hls | rtsp | mjpeg")
    ai_profile: Optional[str] = Field(None, description="AI 프로파일")
    idempotency_key: Optional[str] = Field(None, description="멱등 키. 없으면 자동 생성")


class StartStreamResponse(BaseModel):
    job_id: str
    channel_id: str
    message: str = "Accepted"


# ----- 멱등성 -----
# 1. idempotency_key가 있으면 DB jobs에서 조회.
# 2. 존재하면 기존 job_id로 202 + 동일 응답 (중복 실행 방지).
# 3. 없으면 새 job_id 생성, jobs insert, streams desired_state=RUNNING, Kafka stream.commands 발행 후 202.


@router.post("/", response_model=StartStreamResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_stream(body: StartStreamRequest) -> StartStreamResponse:
    """
    스트림 시작 요청. 즉시 202 Accepted + job_id 반환.
    실제 시작은 Orchestrator가 stream.commands를 소비해 lease 할당 후 Worker에 지시.
    """
    job_id = str(uuid.uuid4())
    idem_key = body.idempotency_key or f"start-{body.channel_id}-{job_id}"

    # TODO: DB에서 idempotency_key로 기존 job 조회
    # existing = await job_repo.get_by_idempotency_key(idem_key)
    # if existing: return StartStreamResponse(job_id=existing.job_id, channel_id=body.channel_id)

    # TODO: jobs insert, streams desired_state=RUNNING, Kafka stream.commands 발행
    # await job_repo.create(job_id=job_id, channel_id=body.channel_id, idempotency_key=idem_key, command="START")
    # await stream_repo.set_desired_state(body.channel_id, "running")
    # await kafka_producer.send(STREAM_COMMANDS, key=body.channel_id, value=...)

    return StartStreamResponse(job_id=job_id, channel_id=body.channel_id)


@router.delete("/{channel_id}", status_code=status.HTTP_202_ACCEPTED)
async def stop_stream(channel_id: str) -> dict:
    """스트림 중지 요청. 202 Accepted. stream.commands STOP 발행."""
    # TODO: stream_repo.set_desired_state(channel_id, "stopped"), Kafka STOP
    return {"channel_id": channel_id, "message": "Accepted"}


@router.get("/{channel_id}")
async def get_stream_status(channel_id: str) -> dict:
    """스트림 상태 조회. Control DB streams 테이블에서 status, worker_id 등 반환."""
    # TODO: stream_repo.get(channel_id)
    return {"channel_id": channel_id, "status": "idle", "worker_id": None}
