"""ID 생성 추상화 (job_id, idempotency_key 등)."""
from abc import ABC, abstractmethod
import uuid


class IdGenerator(ABC):
    @abstractmethod
    def new_job_id(self) -> str:
        ...

    def new_idempotency_key(self, prefix: str = "") -> str:
        return f"{prefix}{uuid.uuid4().hex}" if prefix else uuid.uuid4().hex


class UuidIdGenerator(IdGenerator):
    def new_job_id(self) -> str:
        return str(uuid.uuid4())
