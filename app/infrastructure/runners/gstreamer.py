"""
GStreamer 기반 StreamRunner. gst-launch-1.0 subprocess 방식.
- channel_id당 파이프라인 1개. RTSP 입력 → HLS/RTSP 출력.
- overlay_mode: NONE | SIMPLE(textoverlay) | OSD(플러그인 훅).
- 프레임을 Python으로 꺼내지 않음. bus/종료는 stderr·종료코드로 감지.
"""
import asyncio
import logging
import os
import shutil
from typing import Optional

from app.services.worker_stream.manager import StreamSpec

logger = logging.getLogger(__name__)

GST_LAUNCH = "gst-launch-1.0"
# 지연 최소화
RTSPSRC_LATENCY_MS = 200
QUEUE_MAX_BUFFERS = 3
HLS_TARGET_DURATION_SEC = 2
HLS_PLAYLIST_LENGTH = 3


def _build_pipeline(spec: StreamSpec) -> list[str]:
    """
    StreamSpec으로 gst-launch-1.0 인자 리스트 생성.
    출력: HLS(기본). overlay_mode에 따라 textoverlay/OSD 훅 삽입.
    """
    source_uri = spec.source_uri or "rtsp://localhost/fake"
    params = spec.params or {}
    overlay_mode = (params.get("overlay_mode") or "NONE").upper()
    output_type = (spec.output_type or "hls").lower()
    channel_id = spec.channel_id

    # HLS 출력 경로: output_uri가 디렉터리면 그대로, 없으면 /tmp/hls/{channel_id}
    output_path = params.get("output_path") or spec.output_uri or ""
    if not output_path:
        output_path = f"/tmp/hls/{channel_id}"
    if "%" in output_path or output_path.rstrip("/").endswith(".ts"):
        output_path = os.path.dirname(output_path) or output_path
    os.makedirs(output_path, exist_ok=True)
    segment_pattern = os.path.join(output_path, "seg%05d.ts")

    # 공통: rtspsrc → depay → parse → decode → convert
    parts = [
        "-e",
        "rtspsrc", "location=" + source_uri,
        f"latency={RTSPSRC_LATENCY_MS}", "drop-on-latency=true",
        "!", "queue", f"max-size-buffers={QUEUE_MAX_BUFFERS}",
        "!", "rtph264depay", "!", "h264parse",
        "!", "avdec_h264", "!", "videoconvert",
    ]

    if overlay_mode == "SIMPLE":
        # 옵션 A: textoverlay로 간단 텍스트 (라벨 리스트는 overlay_store 연동 시 동적 갱신은 OSD에서)
        label = params.get("overlay_label") or f"CH:{channel_id}"
        parts.extend(["!", "textoverlay", "text=" + label, "valignment=top", "halignment=left"])
    elif overlay_mode == "OSD":
        # 옵션 B: 메타데이터/OSD 훅. identity로 플러그인 교체 지점 표시
        parts.extend(["!", "identity", "name=osd-inject", "single-segment=true"])

    if output_type == "hls":
        parts.extend([
            "!", "x264enc", "tune=zerolatency", "speed-preset=1",
            "!", "mpegtsmux",
            "!", "hlssink2",
            f"target-duration={HLS_TARGET_DURATION_SEC}",
            f"playlist-length={HLS_PLAYLIST_LENGTH}",
            "location=" + segment_pattern,
        ])
    else:
        # RTSP 재송출 또는 기타: fakesink로 안전 폴백 (실제 rtsp sink는 환경별 추가)
        parts.extend(["!", "fakesink", "sync=true"])

    return [GST_LAUNCH] + parts


def _log_stderr_line(channel_id: str, line: str, pipeline_id: str = "") -> None:
    """stderr 라인 단위 구조화 로그."""
    line = (line or "").strip()
    if not line:
        return
    logger.info("channel_id=%s pipeline_id=%s stderr=%s", channel_id, pipeline_id or channel_id, line[:500])


class GstreamerStreamRunner:
    """
    gst-launch-1.0 subprocess로 파이프라인 실행.
    StreamRunner 인터페이스: spawn(spec) -> asyncio.subprocess.Process.
    terminate/timeout/wait는 manager가 process.terminate(), process.wait()로 수행.
    """

    async def spawn(self, spec: StreamSpec) -> asyncio.subprocess.Process:
        if not shutil.which(GST_LAUNCH):
            raise RuntimeError(f"{GST_LAUNCH} not found; install gstreamer1.0-tools and plugins")
        argv = _build_pipeline(spec)
        logger.info(
            "channel_id=%s pipeline_id=%s starting pipeline argv=%s",
            spec.channel_id, spec.channel_id, argv[:10],
        )
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.DEVNULL,
        )
        # stderr 라인 단위 로깅 (비동기, 프로세스와 별도)
        asyncio.create_task(
            _consume_stderr(proc.stderr, spec.channel_id, spec.channel_id),
            name=f"stderr-{spec.channel_id}",
        )
        return proc


async def _consume_stderr(stream: Optional[asyncio.StreamReader], channel_id: str, pipeline_id: str) -> None:
    """stderr 스트림을 라인 단위로 읽어 로그 출력. 프로세스 종료 시 스트림 닫힘."""
    if stream is None:
        return
    buf = b""
    try:
        while True:
            chunk = await stream.read(4096)
            if not chunk:
                break
            buf += chunk
            while b"\n" in buf or b"\r" in buf:
                line, _, buf = buf.partition(b"\n")
                if b"\r" in line:
                    line = line.split(b"\r")[-1]
                _log_stderr_line(channel_id, line.decode("utf-8", errors="replace"), pipeline_id)
        if buf.strip():
            _log_stderr_line(channel_id, buf.decode("utf-8", errors="replace"), pipeline_id)
    except (ConnectionResetError, BrokenPipeError, asyncio.CancelledError):
        pass
    except Exception as e:
        logger.debug("channel_id=%s stderr consume done: %s", channel_id, e)
