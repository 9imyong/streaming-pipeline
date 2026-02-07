"""
구조화 로그 필드 통일: channel_id, worker_id, event_type, command_id, restart_count.
- Worker/Orchestrator에서 logger.info(..., extra=stream_log_extra(...)) 사용 시
  "어디서/왜/몇 번 재시작" 검색·대시보드 가능.
"""
from typing import Any, Optional


def stream_log_extra(
    channel_id: str,
    worker_id: Optional[str] = None,
    event_type: Optional[str] = None,
    command_id: Optional[str] = None,
    restart_count: Optional[int] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """구조화 로그용 extra dict. event_type: STARTED|STOPPED|FAILED|HEARTBEAT|lease_expired 등."""
    out: dict[str, Any] = {"channel_id": channel_id}
    if worker_id is not None:
        out["worker_id"] = worker_id
    if event_type is not None:
        out["event_type"] = event_type
    if command_id is not None:
        out["command_id"] = command_id
    if restart_count is not None:
        out["restart_count"] = restart_count
    out.update(kwargs)
    return out
