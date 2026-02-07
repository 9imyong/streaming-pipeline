"""
JobRepository DB 구현. jobs 테이블, 멱등성용 idempotency_key.
- 각 쿼리 목적 주석.
"""
from typing import Optional

from app.application.ports.job_repository import JobRepository
from app.infrastructure.persistence.mysql import get_connection
from app.infrastructure.persistence.models import JOBS_TABLE


async def _run_in_executor(f):
    import asyncio
    return await asyncio.to_thread(f)


class DbJobRepository(JobRepository):
    """MySQL jobs 테이블 기반 JobRepository."""

    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[dict]:
        # 멱등 조회: 동일 키로 이미 처리된 job이 있으면 반환 (중복 START 방지)
        def _run() -> Optional[dict]:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT job_id, channel_id, command FROM {JOBS_TABLE} WHERE idempotency_key = %s",
                        (idempotency_key,),
                    )
                    row = cur.fetchone()
                    return dict(row) if row else None

        return await _run_in_executor(_run)

    async def get_latest_job_id_by_channel(self, channel_id: str) -> Optional[str]:
        def _run() -> Optional[str]:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT job_id FROM {JOBS_TABLE} WHERE channel_id = %s ORDER BY created_at DESC LIMIT 1",
                        (channel_id,),
                    )
                    row = cur.fetchone()
                    return row["job_id"] if row else None

        return await _run_in_executor(_run)

    async def create(
        self,
        job_id: str,
        channel_id: str,
        idempotency_key: str,
        command: str,
    ) -> None:
        # Job 생성: UNIQUE(idempotency_key)로 중복 시 예외. 유스케이스에서 멱등 조회 후 호출
        def _run() -> None:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"INSERT INTO {JOBS_TABLE} (job_id, channel_id, idempotency_key, command) VALUES (%s, %s, %s, %s)",
                        (job_id, channel_id, idempotency_key, command),
                    )

        await _run_in_executor(_run)
