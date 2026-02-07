"""
스트림 단건 조회 유스케이스.
- StreamRepository.get() + JobRepository.get_latest_job_id_by_channel() 로 worker_id와 작업 ID 구분.
"""
from app.application.dto import StreamStatusResult
from app.application.ports.job_repository import JobRepository
from app.application.ports.stream_repository import StreamRepository


async def get_stream(
    stream_repo: StreamRepository,
    channel_id: str,
    job_repo: JobRepository | None = None,
) -> StreamStatusResult:
    """채널 상태 조회. job_repo 있으면 해당 채널 최근 job_id를 current_job_id로 반환."""
    row = await stream_repo.get(channel_id)
    if not row:
        return StreamStatusResult(channel_id=channel_id, status="pending")
    current_job_id = None
    if job_repo:
        current_job_id = await job_repo.get_latest_job_id_by_channel(channel_id)
    return StreamStatusResult(
        channel_id=channel_id,
        status=row.get("status", "pending"),
        worker_id=row.get("assigned_worker_id"),
        desired_state=row.get("desired_state"),
        last_error=row.get("last_error"),
        restart_count=row.get("restart_count", 0),
        pipeline_params=row.get("pipeline_params"),
        current_job_id=current_job_id,
    )
