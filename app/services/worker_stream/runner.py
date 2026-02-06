"""
스트리밍 subprocess 실행. ffmpeg/gstreamer 호출은 여기만.
- StreamProcessManager는 이 인터페이스를 통해만 프로세스 생성.
"""
import asyncio
import logging
from typing import Any

from app.services.worker_stream.manager import StreamSpec

logger = logging.getLogger(__name__)


class StreamRunner:
    """
    StreamSpec에 따라 subprocess 생성. 실제 구현은 ffmpeg 또는 gst-launch.
    """
    async def spawn(self, spec: StreamSpec) -> asyncio.subprocess.Process:
        # 스텁: 실제로는 ffmpeg/gst-launch 명령 구성 후 asyncio.create_subprocess_exec
        raise NotImplementedError("StreamRunner.spawn: inject ffmpeg or gst-launch implementation")


class StubStreamRunner(StreamRunner):
    """테스트/개발용. sleep 프로세스로 동작만 확인."""
    async def spawn(self, spec: StreamSpec) -> asyncio.subprocess.Process:
        return await asyncio.create_subprocess_exec(
            "sleep", "3600",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
