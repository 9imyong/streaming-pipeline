"""
스트림 시작 유스케이스 (START).
- 비동기 흐름: 요청 수신 → 멱등 검사 → 상태·Job 저장 → command 발행 → 즉시 202 반환. 실행은 Orchestrator/Worker가 담당.
- 멱등성: idempotency_key로 기존 job 조회 후 있으면 동일 job_id 반환 (중복 START 방지).
- DB/Kafka 직접 사용 금지. 반드시 ports(StreamRepository, JobRepository, CommandBus) 경유.
"""
import uuid

from app.application.dto import StartStreamResult
from app.application.ports.command_bus import CommandBus
from app.application.ports.job_repository import JobRepository
from app.application.ports.stream_repository import StreamRepository


async def create_stream(
    stream_repo: StreamRepository,
    job_repo: JobRepository,
    command_bus: CommandBus,
    *,
    channel_id: str,
    source_rtsp: str,
    output: str = "hls",
    ai_profile: str | None = None,
    idempotency_key: str | None = None,
    job_id: str | None = None,
) -> StartStreamResult:
    """
    START 요청: 상태 저장 + command 발행만. 실행은 하지 않음.
    """
    jid = job_id or str(uuid.uuid4())
    idem = idempotency_key or f"start-{channel_id}-{jid}"

    # [멱등성] 동일 idempotency_key로 이미 처리된 job이 있으면 그대로 반환 (재전송/중복 방지)
    existing = await job_repo.get_by_idempotency_key(idem)
    if existing:
        return StartStreamResult(job_id=existing["job_id"], channel_id=existing["channel_id"])

    # 상태·Job 저장 (ports 경유)
    await job_repo.create(job_id=jid, channel_id=channel_id, idempotency_key=idem, command="START")
    await stream_repo.create_or_update(
        channel_id=channel_id,
        desired_state="running",
        pipeline_params={
            "source_rtsp": source_rtsp,
            "output": output,
            "ai_profile": ai_profile,
        },
    )
    # command 발행 → Orchestrator가 소비해 lease 할당 후 Worker에 지시 (이 레이어는 발행만)
    await command_bus.publish_command(
        key=channel_id,
        payload={
            "command": "START",
            "channel_id": channel_id,
            "job_id": jid,
            "idempotency_key": idem,
            "params": {
                "source_rtsp": source_rtsp,
                "output": output,
                "ai_profile": ai_profile,
            },
        },
    )
    return StartStreamResult(job_id=jid, channel_id=channel_id)
