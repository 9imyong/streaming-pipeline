"""Lease 획득/갱신/해제 인터페이스 (포트)."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional


class LeaseStore(ABC):
    @abstractmethod
    def acquire(self, channel_id: str, worker_id: str, ttl_seconds: int) -> bool:
        """조건부 lease 획득. 성공 시 True."""
        ...

    @abstractmethod
    def renew(self, channel_id: str, worker_id: str, ttl_seconds: int) -> bool:
        """Lease 갱신."""
        ...

    @abstractmethod
    def release(self, channel_id: str, worker_id: str) -> bool:
        """Lease 해제."""
        ...

    @abstractmethod
    def list_expired(self) -> list[str]:
        """만료된 channel_id 목록."""
        ...
