"""
StreamRepository DB 구현. streams 테이블 접근만.
- 비즈니스 판단/상태 전이 검증은 domain에서. 여기서는 쿼리만.
- 각 쿼리에 목적 주석.
"""
import json
from datetime import datetime, timezone
from typing import Any, Optional

from app.application.ports.stream_repository import StreamRepository
from app.infrastructure.persistence.mysql import get_connection
from app.infrastructure.persistence.models import STREAMS_TABLE


class DbStreamRepository(StreamRepository):
    """MySQL streams 테이블 기반 StreamRepository."""

    async def get(self, channel_id: str) -> Optional[dict[str, Any]]:
        # 단건 조회: API/Orchestrator/Worker가 현재 상태·lease·파라미터 확인용
        def _run() -> Optional[dict[str, Any]]:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT channel_id, status, desired_state, assigned_worker_id, "
                        f"lease_expires_at, pipeline_params, restart_count, last_error, updated_at "
                        f"FROM {STREAMS_TABLE} WHERE channel_id = %s",
                        (channel_id,),
                    )
                    row = cur.fetchone()
                    if not row:
                        return None
                    if row.get("pipeline_params") and isinstance(row["pipeline_params"], str):
                        row["pipeline_params"] = json.loads(row["pipeline_params"])
                    if row.get("lease_expires_at"):
                        row["lease_expires_at"] = row["lease_expires_at"].isoformat() if hasattr(row["lease_expires_at"], "isoformat") else row["lease_expires_at"]
                    return dict(row)

        return await _run_in_executor(_run)

    async def set_desired_state(self, channel_id: str, state: str) -> None:
        # API STOP 요청 시 desired_state=stopped 반영. Orchestrator가 이 값을 보고 STOP 처리
        def _run() -> None:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"INSERT INTO {STREAMS_TABLE} (channel_id, desired_state, status, updated_at) "
                        f"VALUES (%s, %s, 'pending', NOW(3)) "
                        f"ON DUPLICATE KEY UPDATE desired_state = %s, updated_at = NOW(3)",
                        (channel_id, state, state),
                    )

        await _run_in_executor(_run)

    async def create_or_update(
        self,
        channel_id: str,
        desired_state: str,
        pipeline_params: Optional[dict[str, Any]] = None,
    ) -> None:
        # START 요청 시 스트림 행 생성 또는 desired_state·pipeline_params 갱신
        def _run() -> None:
            params_json = json.dumps(pipeline_params or {}, ensure_ascii=False) if pipeline_params else None
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"INSERT INTO {STREAMS_TABLE} (channel_id, desired_state, status, pipeline_params, updated_at) "
                        f"VALUES (%s, %s, 'pending', %s, NOW(3)) "
                        f"ON DUPLICATE KEY UPDATE desired_state = %s, pipeline_params = COALESCE(%s, pipeline_params), updated_at = NOW(3)",
                        (channel_id, desired_state, params_json, desired_state, params_json),
                    )

        await _run_in_executor(_run)

    async def transition_status(self, channel_id: str, from_state: str, to_state: str) -> bool:
        # 상태 전이: domain 검증 후 호출. 조건부 UPDATE로 동시성 안전 (한 번만 전이 성공)
        def _run() -> bool:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"UPDATE {STREAMS_TABLE} SET status = %s, updated_at = NOW(3) "
                        f"WHERE channel_id = %s AND status = %s",
                        (to_state, channel_id, from_state),
                    )
                    return cur.rowcount > 0

        return await _run_in_executor(_run)

    async def set_assigned_worker(self, channel_id: str, worker_id: str, lease_expires_at: Any) -> bool:
        # Orchestrator가 lease 획득 후 assigned_worker_id·lease_expires_at 기록 (실제 할당 반영)
        def _run() -> bool:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # lease_expires_at은 datetime 또는 ISO 문자열
                    ts = lease_expires_at
                    if hasattr(ts, "isoformat"):
                        ts = ts.isoformat()
                    cur.execute(
                        f"UPDATE {STREAMS_TABLE} SET assigned_worker_id = %s, lease_expires_at = %s, updated_at = NOW(3) "
                        f"WHERE channel_id = %s",
                        (worker_id, ts, channel_id),
                    )
                    return cur.rowcount > 0

        return await _run_in_executor(_run)

    async def increment_restart_count(self, channel_id: str) -> None:
        # 프로세스 재시작 시 restart_count 증가. 장애 통계/무한 재시작 판단용
        def _run() -> None:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"UPDATE {STREAMS_TABLE} SET restart_count = restart_count + 1, updated_at = NOW(3) WHERE channel_id = %s",
                        (channel_id,),
                    )

        await _run_in_executor(_run)

    async def set_last_error(self, channel_id: str, message: str) -> None:
        # FAILED/에러 시 last_error 저장. 운영 디버깅용
        def _run() -> None:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"UPDATE {STREAMS_TABLE} SET last_error = %s, updated_at = NOW(3) WHERE channel_id = %s",
                        (message[:4096] if message else None, channel_id),
                    )

        await _run_in_executor(_run)


async def _run_in_executor(f):
    import asyncio
    return await asyncio.to_thread(f)
