"""CommandBus 스텁 구현 (테스트/로컬 개발 전용). Kafka 대신 로깅만.
- 기본 Gateway는 KafkaCommandBus 사용. 이 스텁은 테스트/uv run 시 Kafka 없이 동작할 때만 사용."""
import logging
from typing import Any

from app.application.ports.command_bus import CommandBus

logger = logging.getLogger(__name__)


class StubCommandBus(CommandBus):
    """Kafka 없이 로깅만. 테스트 또는 Kafka 미가동 로컬 개발용."""

    async def publish_command(self, key: str, payload: dict[str, Any]) -> None:
        logger.info("command_bus.publish key=%s command=%s", key, payload.get("command"))
