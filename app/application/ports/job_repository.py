"""Job 저장 포트 (멱등성용). Gateway는 이 인터페이스를 직접 사용하지 않고 유스케이스를 통해서만 호출한다."""
from abc import ABC, abstractmethod
from typing import Optional


class JobRepository(ABC):
    @abstractmethod
    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[dict]:
        """idempotency_key로 기존 job 조회. 없으면 None. 반환: {job_id, channel_id} 등."""
        ...

    @abstractmethod
    async def create(
        self,
        job_id: str,
        channel_id: str,
        idempotency_key: str,
        command: str,
    ) -> None:
        """Job 생성 (멱등 키 UNIQUE 제약으로 중복 시 예외)."""
        ...
