"""
LeaseStore DB 구현. 조건부 UPDATE로 lease 획득/갱신/해제. 원자적 경쟁 해결.
- 비즈니스 판단 없음. Orchestrator/Worker가 호출.
"""
from datetime import datetime, timedelta, timezone
from typing import List

from app.application.ports.lease_store import LeaseStore
from app.infrastructure.persistence.mysql import get_connection
from app.infrastructure.persistence.models import STREAMS_TABLE


async def _run_in_executor(f):
    import asyncio
    return await asyncio.to_thread(f)


class DbLeaseStore(LeaseStore):
    """streams 테이블의 assigned_worker_id, lease_expires_at으로 lease 관리."""

    async def acquire(self, channel_id: str, worker_id: str, ttl_seconds: int) -> bool:
        # lease 획득: 만료되었거나 미할당인 경우에만 해당 worker_id로 갱신. 중복 할당 방지
        def _run() -> bool:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    expires = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    cur.execute(
                        f"UPDATE {STREAMS_TABLE} SET assigned_worker_id = %s, lease_expires_at = %s, status = 'assigned', updated_at = NOW(3) "
                        f"WHERE channel_id = %s AND (lease_expires_at IS NULL OR lease_expires_at < NOW(3) OR assigned_worker_id = %s)",
                        (worker_id, expires, channel_id, worker_id),
                    )
                    return cur.rowcount > 0

        return await _run_in_executor(_run)

    async def renew(self, channel_id: str, worker_id: str, ttl_seconds: int) -> bool:
        # lease 갱신: 현재 소유자만 갱신 가능. Worker heartbeat 시 주기 호출
        def _run() -> bool:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    expires = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    cur.execute(
                        f"UPDATE {STREAMS_TABLE} SET lease_expires_at = %s, updated_at = NOW(3) "
                        f"WHERE channel_id = %s AND assigned_worker_id = %s",
                        (expires, channel_id, worker_id),
                    )
                    return cur.rowcount > 0

        return await _run_in_executor(_run)

    async def release(self, channel_id: str, worker_id: str) -> bool:
        # lease 해제: 해당 worker만 해제. STOP/장애 시 Worker가 호출
        def _run() -> bool:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"UPDATE {STREAMS_TABLE} SET assigned_worker_id = NULL, lease_expires_at = NULL, updated_at = NOW(3) "
                        f"WHERE channel_id = %s AND assigned_worker_id = %s",
                        (channel_id, worker_id),
                    )
                    return cur.rowcount > 0

        return await _run_in_executor(_run)

    async def list_expired(self) -> List[str]:
        # 만료된 channel_id 목록: Orchestrator가 재할당 대상으로 조회
        def _run() -> List[str]:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT channel_id FROM {STREAMS_TABLE} "
                        f"WHERE assigned_worker_id IS NOT NULL AND lease_expires_at < NOW(3)"
                    )
                    return [r["channel_id"] for r in cur.fetchall()]

        return await _run_in_executor(_run)
