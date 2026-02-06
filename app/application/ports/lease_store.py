"""Lease(소유권) 획득/갱신/해제 인터페이스. 구현은 persistence에서 조건부 UPDATE로 원자 처리."""
from abc import ABC, abstractmethod


class LeaseStore(ABC):
    @abstractmethod
    async def acquire(self, channel_id: str, worker_id: str, ttl_seconds: int) -> bool:
        """조건부 lease 획득. (lease_expires_at < NOW() OR assigned_worker_id IS NULL) 일 때만 UPDATE. 성공 시 True."""
        ...

    @abstractmethod
    async def renew(self, channel_id: str, worker_id: str, ttl_seconds: int) -> bool:
        """Lease 갱신. assigned_worker_id = worker_id 일 때만 lease_expires_at 갱신."""
        ...

    @abstractmethod
    async def release(self, channel_id: str, worker_id: str) -> bool:
        """Lease 해제. assigned_worker_id = worker_id 일 때만 NULL/만료 처리."""
        ...

    @abstractmethod
    async def list_expired(self) -> list[str]:
        """만료된 channel_id 목록 (lease_expires_at < NOW()). 재할당 대상."""
        ...
