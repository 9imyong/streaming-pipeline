"""
스트림 단건 조회 유스케이스.
- StreamRepository.get()만 호출. 비즈니스 판단 없음. 포트 경유만.
"""
from app.application.dto import StreamStatusResult
from app.application.ports.stream_repository import StreamRepository


async def get_stream(
    stream_repo: StreamRepository,
    channel_id: str,
) -> StreamStatusResult:
    """채널 상태 조회. 없으면 status=pending 수준으로 반환."""
    row = await stream_repo.get(channel_id)
    if not row:
        return StreamStatusResult(channel_id=channel_id, status="pending")
    return StreamStatusResult(
        channel_id=channel_id,
        status=row.get("status", "pending"),
        worker_id=row.get("assigned_worker_id"),
        desired_state=row.get("desired_state"),
        last_error=row.get("last_error"),
        restart_count=row.get("restart_count", 0),
        pipeline_params=row.get("pipeline_params"),
    )
