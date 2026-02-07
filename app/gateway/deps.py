"""
Gateway 의존성: 유스케이스 실행기만 주입.
- DB/Kafka/ffmpeg 직접 접근 금지. StreamRepository, JobRepository, CommandBus는 app.state에서 조회.
- 앱 lifespan에서 app.state.stream_repository, app.state.job_repository, app.state.command_bus 를 설정해야 함.
"""
from fastapi import Depends, Request

from app.application.dto import StartStreamResult, StreamStatusResult
from app.application.ports.command_bus import CommandBus
from app.application.ports.job_repository import JobRepository
from app.application.ports.observability_reader import ObservabilityReader
from app.application.ports.stream_repository import StreamRepository
from app.application.usecases.create_stream import create_stream
from app.application.usecases.get_stream import get_stream
from app.application.usecases.stop_stream import stop_stream


def get_stream_repository(request: Request) -> StreamRepository:
    """스트림 저장소. lifespan에서 설정 필수."""
    repo = getattr(request.app.state, "stream_repository", None)
    if repo is None:
        raise RuntimeError("stream_repository not set on app.state (wire in lifespan)")
    return repo


def get_job_repository(request: Request) -> JobRepository:
    """Job 저장소. lifespan에서 설정 필수."""
    repo = getattr(request.app.state, "job_repository", None)
    if repo is None:
        raise RuntimeError("job_repository not set on app.state (wire in lifespan)")
    return repo


def get_command_bus(request: Request) -> CommandBus:
    """Command 버스. lifespan에서 설정 필수."""
    bus = getattr(request.app.state, "command_bus", None)
    if bus is None:
        raise RuntimeError("command_bus not set on app.state (wire in lifespan)")
    return bus


# ----- 유스케이스 실행기 (Gateway는 이걸 통해서만 로직 호출) -----


class CreateStreamRunner:
    """create_stream 유스케이스 실행기. DB/Kafka는 내부 포트로만 접근."""

    def __init__(
        self,
        stream_repo: StreamRepository,
        job_repo: JobRepository,
        command_bus: CommandBus,
    ):
        self._stream_repo = stream_repo
        self._job_repo = job_repo
        self._command_bus = command_bus

    async def run(
        self,
        channel_id: str,
        source_rtsp: str,
        output: str = "hls",
        ai_profile: str | None = None,
        overlay_mode: str | None = None,
        overlay_label: str | None = None,
        idempotency_key: str | None = None,
    ) -> StartStreamResult:
        return await create_stream(
            self._stream_repo,
            self._job_repo,
            self._command_bus,
            channel_id=channel_id,
            source_rtsp=source_rtsp,
            output=output,
            ai_profile=ai_profile,
            overlay_mode=overlay_mode,
            overlay_label=overlay_label,
            idempotency_key=idempotency_key,
        )


class StopStreamRunner:
    """stop_stream 유스케이스 실행기."""

    def __init__(self, stream_repo: StreamRepository, command_bus: CommandBus):
        self._stream_repo = stream_repo
        self._command_bus = command_bus

    async def run(self, channel_id: str) -> None:
        await stop_stream(self._stream_repo, self._command_bus, channel_id)


class GetStreamRunner:
    """get_stream 유스케이스 실행기."""

    def __init__(self, stream_repo: StreamRepository):
        self._stream_repo = stream_repo

    async def run(self, channel_id: str) -> StreamStatusResult:
        return await get_stream(self._stream_repo, channel_id)


def get_create_stream_use_case(
    stream_repo: StreamRepository = Depends(get_stream_repository),
    job_repo: JobRepository = Depends(get_job_repository),
    command_bus: CommandBus = Depends(get_command_bus),
) -> CreateStreamRunner:
    """POST /v1/streams 에서 사용."""
    return CreateStreamRunner(stream_repo, job_repo, command_bus)


def get_stop_stream_use_case(
    stream_repo: StreamRepository = Depends(get_stream_repository),
    command_bus: CommandBus = Depends(get_command_bus),
) -> StopStreamRunner:
    """DELETE /v1/streams/{channel_id} 에서 사용."""
    return StopStreamRunner(stream_repo, command_bus)


def get_get_stream_use_case(
    stream_repo: StreamRepository = Depends(get_stream_repository),
) -> GetStreamRunner:
    """GET /v1/streams/{channel_id} 에서 사용."""
    return GetStreamRunner(stream_repo)


def get_observability_reader(request: Request) -> ObservabilityReader:
    """관측성 읽기. lifespan에서 설정 필수."""
    reader = getattr(request.app.state, "observability_reader", None)
    if reader is None:
        raise RuntimeError("observability_reader not set on app.state (wire in lifespan)")
    return reader
