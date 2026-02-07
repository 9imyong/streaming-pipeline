"""
스트리밍 실행 인터페이스. ffmpeg/GStreamer 구현은 infrastructure/runners에 둠.
- StreamProcessManager는 spawn(spec) 반환 handle(Process-like)로 채널당 1개 실행.
"""
import asyncio
import logging
from typing import Any, Union

from app.application.dto import StreamSpec

logger = logging.getLogger(__name__)


class StreamRunner:
    """
    StreamSpec에 따라 파이프라인 실행. 반환값은 Process-like (terminate, wait, returncode).
    구현: app.infrastructure.runners.gstreamer.GstreamerStreamRunner
    """
    async def spawn(self, spec: StreamSpec) -> Union[asyncio.subprocess.Process, Any]:
        raise NotImplementedError("StreamRunner.spawn: use GstreamerStreamRunner or ffmpeg implementation")
