"""
관측성 읽기: streams 테이블 기준 상태 카운터·last_error 목록.
- stream.events 반영된 DB가 Single Source of Truth.
"""
from typing import Any

from app.application.ports.observability_reader import ObservabilityReader
from app.infrastructure.persistence.mysql import get_connection
from app.infrastructure.persistence.models import STREAMS_TABLE


async def _run_in_executor(f):
    import asyncio
    return await asyncio.to_thread(f)


class DbObservabilityReader(ObservabilityReader):
    """MySQL streams 테이블 기반 ObservabilityReader."""

    async def get_status_counts(self) -> dict[str, int]:
        def _run() -> dict[str, int]:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT status, COUNT(*) AS cnt FROM {STREAMS_TABLE} GROUP BY status"
                    )
                    rows = cur.fetchall()
                    by_status = {r["status"]: r["cnt"] for r in rows}
                    cur.execute(
                        f"SELECT COALESCE(SUM(restart_count), 0) AS total FROM {STREAMS_TABLE}"
                    )
                    restarts_row = cur.fetchone()
                    restarts_total = int(restarts_row["total"] or 0)
                    return {
                        "streams_running": by_status.get("running", 0),
                        "streams_failed": by_status.get("failed", 0),
                        "streams_pending": by_status.get("pending", 0),
                        "streams_assigned": by_status.get("assigned", 0),
                        "streams_stopped": by_status.get("stopped", 0),
                        "restarts_total": restarts_total,
                    }
        return await _run_in_executor(_run)

    async def get_last_errors(self, limit: int = 50) -> list[dict[str, Any]]:
        def _run() -> list[dict[str, Any]]:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT channel_id, last_error, status, restart_count, updated_at "
                        f"FROM {STREAMS_TABLE} WHERE last_error IS NOT NULL AND last_error != '' "
                        f"ORDER BY updated_at DESC LIMIT %s",
                        (limit,),
                    )
                    return [dict(r) for r in cur.fetchall()]
        return await _run_in_executor(_run)

    async def get_stream_list(self, limit: int = 100) -> list[dict[str, Any]]:
        def _run() -> list[dict[str, Any]]:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT channel_id, status, desired_state, assigned_worker_id, "
                        f"restart_count, last_error, updated_at FROM {STREAMS_TABLE} "
                        f"ORDER BY updated_at DESC LIMIT %s",
                        (limit,),
                    )
                    rows = cur.fetchall()
                    out = []
                    for r in rows:
                        d = dict(r)
                        if d.get("updated_at") and hasattr(d["updated_at"], "isoformat"):
                            d["updated_at"] = d["updated_at"].isoformat()
                        out.append(d)
                    return out
        return await _run_in_executor(_run)
