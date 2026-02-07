"""
스트림 중지 유스케이스 (STOP).
- 비동기: desired_state=stopped 저장 후 STOP command 발행. 실제 종료는 Orchestrator/Worker가 수행.
- ports 경유만. DB/Kafka 직접 사용 금지.
"""
import uuid

from app.application.ports.command_bus import CommandBus
from app.application.ports.stream_repository import StreamRepository


async def stop_stream(
    stream_repo: StreamRepository,
    command_bus: CommandBus,
    channel_id: str,
) -> None:
    """STOP 요청: desired_state 반영 + command 발행. 실행은 하지 않음."""
    await stream_repo.set_desired_state(channel_id, "stopped")
    command_id = str(uuid.uuid4())
    await command_bus.publish_command(
        key=channel_id,
        payload={
            "command": "STOP",
            "type": "STOP",
            "channel_id": channel_id,
            "job_id": "",
            "idempotency_key": f"stop-{channel_id}",
            "command_id": command_id,
            "params": {},
        },
    )
