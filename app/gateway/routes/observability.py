"""
GET /v1/observability — stream.events 기준 상태 카운터 + 마지막 에러 1줄 캐시(DB).
- streams_running, streams_failed, restarts_total
- last_errors: channel_id, last_error(1줄), status, restart_count
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.application.ports.observability_reader import ObservabilityReader
from app.gateway.deps import get_observability_reader

router = APIRouter(prefix="/observability", tags=["observability"])


class StatusCounts(BaseModel):
    streams_running: int = 0
    streams_failed: int = 0
    streams_pending: int = 0
    streams_assigned: int = 0
    streams_stopped: int = 0
    restarts_total: int = 0


class LastErrorRow(BaseModel):
    channel_id: str
    last_error: str = Field(..., description="마지막 에러 1줄(DB 캐시)")
    status: str
    restart_count: int


class ObservabilityResponse(BaseModel):
    counts: StatusCounts
    last_errors: list[LastErrorRow] = Field(default_factory=list, description="last_error 있는 채널, 최근 순")


@router.get("", response_model=ObservabilityResponse)
async def get_observability(
    reader: ObservabilityReader = Depends(get_observability_reader),
) -> ObservabilityResponse:
    """관측성 MVP: 상태 카운터 + 마지막 에러 목록. 장애 시 어디서/왜/몇 번 재시작 확인용."""
    counts = await reader.get_status_counts()
    last_errors_raw = await reader.get_last_errors(limit=50)
    last_errors = [
        LastErrorRow(
            channel_id=r["channel_id"],
            last_error=(r.get("last_error") or "")[:500],
            status=r.get("status") or "unknown",
            restart_count=int(r.get("restart_count") or 0),
        )
        for r in last_errors_raw
    ]
    return ObservabilityResponse(
        counts=StatusCounts(**counts),
        last_errors=last_errors,
    )
