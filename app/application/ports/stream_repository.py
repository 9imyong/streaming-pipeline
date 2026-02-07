"""
스트림 상태 저장 포트. Gateway/Orchestrator/Worker는 이 인터페이스만 사용.
- DB 드라이버·Kafka 직접 사용 금지.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional


class StreamRepository(ABC):
    @abstractmethod
    async def get(self, channel_id: str) -> Optional[dict[str, Any]]:
        """채널 단건 조회. 없으면 None. keys: status, desired_state, assigned_worker_id, lease_expires_at, pipeline_params, restart_count, last_error."""
        ...

    @abstractmethod
    async def set_desired_state(self, channel_id: str, state: str) -> None:
        """desired_state 설정 (running | stopped)."""
        ...

    @abstractmethod
    async def create_or_update(
        self,
        channel_id: str,
        desired_state: str,
        pipeline_params: Optional[dict[str, Any]] = None,
    ) -> None:
        """스트림 행 생성 또는 desired_state·pipeline_params 갱신."""
        ...

    @abstractmethod
    async def transition_status(self, channel_id: str, from_state: str, to_state: str) -> bool:
        """상태 전이. domain 검증 후 호출. 조건부 UPDATE로 원자성. 성공 시 True."""
        ...

    @abstractmethod
    async def set_assigned_worker(self, channel_id: str, worker_id: str, lease_expires_at: Any) -> bool:
        """assigned_worker_id, lease_expires_at 설정. lease 경쟁 시 조건부 UPDATE."""
        ...

    @abstractmethod
    async def increment_restart_count(self, channel_id: str) -> None:
        """restart_count += 1. 장애 복구 통계용."""
        ...

    @abstractmethod
    async def set_last_error(self, channel_id: str, message: str) -> None:
        """last_error 갱신."""
        ...

    @abstractmethod
    async def update_pipeline_params(self, channel_id: str, updates: dict) -> bool:
        """pipeline_params 일부 갱신 (source_rtsp, output 등). 기존 값과 병합. 채널 없으면 False."""
        ...

    @abstractmethod
    async def delete(self, channel_id: str) -> None:
        """채널 레코드 삭제 (목록에서 제거). STOP 후 호출 권장."""
        ...
