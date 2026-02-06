"""
채널당 1개의 ffmpeg 또는 GStreamer subprocess 실행 래퍼.
- 실행/종료만 담당. 상태 보고는 channel_manager에서.
"""
import logging
import subprocess
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PipelineParams:
    """파이프라인 실행 파라미터 (stream.commands params에서)."""
    source_rtsp: str
    output: str = "hls"  # hls | rtsp | mjpeg
    output_path: Optional[str] = None
    ai_profile: Optional[str] = None


def run_ffmpeg_subprocess(channel_id: str, params: PipelineParams) -> subprocess.Popen:
    """
    ffmpeg subprocess 기동. HLS 예시.
    실제 명령은 params.output 등에 따라 분기.
    """
    # 예: ffmpeg -rtsp_transport tcp -i <source_rtsp> -c copy -f hls ...
    cmd = [
        "ffmpeg",
        "-rtsp_transport", "tcp",
        "-i", params.source_rtsp,
        "-c", "copy",
        "-f", "hls",
        "-hls_time", "2",
        "-hls_list_size", "5",
        "-hls_flags", "delete_segments",
    ]
    if params.output_path:
        cmd.extend(["-hls_segment_filename", f"{params.output_path}/segment_%03d.ts"])
        cmd.append(f"{params.output_path}/index.m3u8")
    else:
        cmd.append("pipe:1")

    logger.info("channel_id=%s starting ffmpeg", channel_id)
    return subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )


def run_gstreamer_subprocess(channel_id: str, params: PipelineParams) -> subprocess.Popen:
    """
    GStreamer subprocess (gst-launch 또는 Python Gst 파이프라인).
    기존 legacy/gstreamer-python/run_appsrc 로직을 래핑할 수 있음.
    """
    # 예: gst-launch-1.0 rtspsrc location=... ! ...
    cmd = [
        "gst-launch-1.0",
        "rtspsrc", f"location={params.source_rtsp}",
        "!", "decodebin", "!", "autovideosink",
    ]
    logger.info("channel_id=%s starting gst", channel_id)
    return subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )


def start_pipeline(channel_id: str, params: PipelineParams, use_ffmpeg: bool = True) -> subprocess.Popen:
    """채널 1개에 대해 파이프라인 subprocess 1개 시작."""
    if use_ffmpeg:
        return run_ffmpeg_subprocess(channel_id, params)
    return run_gstreamer_subprocess(channel_id, params)
