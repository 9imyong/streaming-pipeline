"""CommandBus 스텁 구현 (테스트/개발용). Kafka 대신 로깅만."""
import logging
from typing import Any

from app.application.ports.command_bus import CommandBus

logger = logging.getLogger(__name__)


class StubCommandBus(CommandBus):
    """Kafka 없이 로깅만. Gateway lifespan 주입용."""

    async def publish_command(self, key: str, payload: dict[str, Any]) -> None:
        logger.info("command_bus.publish key=%s command=%s", key, payload.get("command"))
