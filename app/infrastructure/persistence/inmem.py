"""인메모리 저장 (테스트 전용). 포트 인터페이스 구현.
- 운영/배포는 DB 구현체 사용 (DbStreamRepository, DbJobRepository).
- application port 인터페이스는 동일하게 유지.
"""
from typing import Any, Optional

from app.application.ports.job_repository import JobRepository
from app.application.ports.stream_repository import StreamRepository


class InMemoryStreamRepository(StreamRepository):
    """스트림 저장소 인메모리 구현. 테스트 전용. 운영은 DbStreamRepository 사용."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    async def get(self, channel_id: str) -> Optional[dict[str, Any]]:
        return self._store.get(channel_id)

    async def set_desired_state(self, channel_id: str, state: str) -> None:
        if channel_id not in self._store:
            self._store[channel_id] = {}
        self._store[channel_id]["desired_state"] = state

    async def create_or_update(
        self,
        channel_id: str,
        desired_state: str,
        pipeline_params: Optional[dict[str, Any]] = None,
    ) -> None:
        if channel_id not in self._store:
            self._store[channel_id] = {
                "channel_id": channel_id,
                "status": "pending",
                "restart_count": 0,
                "assigned_worker_id": None,
                "lease_expires_at": None,
                "last_error": None,
            }
        self._store[channel_id]["desired_state"] = desired_state
        if pipeline_params is not None:
            self._store[channel_id]["pipeline_params"] = pipeline_params

    async def transition_status(self, channel_id: str, from_state: str, to_state: str) -> bool:
        row = self._store.get(channel_id)
        if not row or row.get("status") != from_state:
            return False
        row["status"] = to_state
        return True

    async def set_assigned_worker(self, channel_id: str, worker_id: str, lease_expires_at: Any) -> bool:
        if channel_id not in self._store:
            return False
        self._store[channel_id]["assigned_worker_id"] = worker_id
        self._store[channel_id]["lease_expires_at"] = lease_expires_at
        return True

    async def increment_restart_count(self, channel_id: str) -> None:
        if channel_id in self._store:
            self._store[channel_id]["restart_count"] = self._store[channel_id].get("restart_count", 0) + 1

    async def set_last_error(self, channel_id: str, message: str) -> None:
        if channel_id in self._store:
            self._store[channel_id]["last_error"] = message

    async def update_pipeline_params(self, channel_id: str, updates: dict) -> bool:
        if channel_id not in self._store:
            return False
        current = self._store[channel_id].get("pipeline_params") or {}
        if isinstance(current, dict):
            current = dict(current)
        else:
            current = {}
        current.update(updates)
        self._store[channel_id]["pipeline_params"] = current
        return True

    async def delete(self, channel_id: str) -> None:
        self._store.pop(channel_id, None)


class InMemoryJobRepository(JobRepository):
    """Job 저장소 인메모리 구현. 테스트 전용. 운영은 DbJobRepository 사용."""

    def __init__(self) -> None:
        self._by_key: dict[str, dict] = {}

    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[dict]:
        return self._by_key.get(idempotency_key)

    async def create(
        self,
        job_id: str,
        channel_id: str,
        idempotency_key: str,
        command: str,
    ) -> None:
        self._by_key[idempotency_key] = {
            "job_id": job_id,
            "channel_id": channel_id,
            "command": command,
        }
