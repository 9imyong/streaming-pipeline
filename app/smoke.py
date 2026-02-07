"""
Smoke 검증: HLS(videotestsrc→hlssink2) / RTSP(rtspsrc→fakesink) / RTSP→HLS(rtspsrc→hlssink2) 검증.
- HLS: 세그먼트·플레이리스트 생성 여부 확인.
- RTSP: rtspsrc SDP 수신·연결 여부 확인.
- RTSP→HLS: rtspsrc ! rtph264depay ! h264parse ! hlssink2 로 실제 URL 검증.
사용: python -m app.smoke hls | python -m app.smoke rtsp --url rtsp://... | python -m app.smoke rtsp-hls --url rtsp://...
"""
from __future__ import annotations

import argparse
import os
import sys
import time


def _init_gst():
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import Gst
    Gst.init(None)
    return Gst


def smoke_hls(out_dir: str = "/tmp/smoke_hls", run_sec: float = 5.0) -> int:
    """videotestsrc → hlssink2 로 HLS 생성 검증. run_sec 후 index.m3u8 존재 여부 확인."""
    Gst = _init_gst()
    os.makedirs(out_dir, exist_ok=True)
    seg = os.path.join(out_dir, "seg%05d.ts")
    playlist = os.path.join(out_dir, "index.m3u8")
    pipeline_desc = (
        "videotestsrc is-live=true num-buffers=0 ! video/x-raw,framerate=25/1 ! "
        "queue ! x264enc tune=zerolatency speed-preset=ultrafast key-int-max=25 ! "
        "h264parse ! hlssink2 target-duration=2 playlist-length=3 "
        f"location={seg} playlist-location={playlist}"
    )
    pipeline = Gst.parse_launch(pipeline_desc)
    if not pipeline:
        print("smoke_hls: parse_launch failed", file=sys.stderr)
        return 1
    pipeline.set_state(Gst.State.PLAYING)
    time.sleep(run_sec)
    pipeline.set_state(Gst.State.NULL)
    if os.path.isfile(playlist):
        print(f"smoke_hls: OK {playlist} exists")
        return 0
    print(f"smoke_hls: FAIL {playlist} not found", file=sys.stderr)
    return 1


def smoke_rtsp(url: str, run_sec: float = 5.0, latency_ms: int = 300, timeout_ms: int = 15000) -> int:
    """rtspsrc → fakesink 로 RTSP 연결 검증. SDP 수신·스트림 연결 여부 확인."""
    if not url or not url.strip().lower().startswith("rtsp://"):
        print("smoke_rtsp: --url rtsp://... required", file=sys.stderr)
        return 1
    Gst = _init_gst()
    timeout_us = min(120000000, max(1000000, int(timeout_ms) * 1000))
    pipeline_desc = (
        f'rtspsrc location="{url.strip()}" protocols=tcp latency={latency_ms} '
        f'timeout={timeout_us} do-rtsp-keep-alive=true ! fakesink sync=false'
    )
    pipeline = Gst.parse_launch(pipeline_desc)
    if not pipeline:
        print("smoke_rtsp: parse_launch failed", file=sys.stderr)
        return 1
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    err_seen = [None]  # list to allow closure to assign

    def on_message(bus, message):
        if message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            err_seen[0] = f"{err.message} ({debug or ''})"

    bus.connect("message", on_message)
    pipeline.set_state(Gst.State.PLAYING)
    deadline = time.monotonic() + run_sec
    while time.monotonic() < deadline and err_seen[0] is None:
        time.sleep(0.2)
    pipeline.set_state(Gst.State.NULL)
    if err_seen[0]:
        print(f"smoke_rtsp: FAIL {err_seen[0]}", file=sys.stderr)
        return 1
    print("smoke_rtsp: OK connection and stream received")
    return 0


def smoke_rtsp_hls(
    url: str,
    out_dir: str = "/tmp/smoke_rtsp_hls",
    run_sec: float = 8.0,
    latency_ms: int = 200,
    timeout_ms: int = 15000,
) -> int:
    """rtspsrc ! rtph264depay ! h264parse ! hlssink2 로 RTSP→HLS 검증. 실제 URL 사용 가능."""
    if not url or not url.strip().lower().startswith("rtsp://"):
        print("smoke_rtsp_hls: --url rtsp://... required", file=sys.stderr)
        return 1
    Gst = _init_gst()
    os.makedirs(out_dir, exist_ok=True)
    segment_tpl = os.path.join(out_dir, "segment_%05d.ts")
    playlist_path = os.path.join(out_dir, "index.m3u8")
    timeout_us = min(120000000, max(1000000, int(timeout_ms) * 1000))
    pipeline_desc = (
        f'rtspsrc location="{url.strip()}" protocols=tcp latency={latency_ms} '
        f'timeout={timeout_us} do-rtsp-keep-alive=true ! '
        "rtph264depay ! h264parse ! "
        f"hlssink2 target-duration=2 playlist-length=3 "
        f"location={segment_tpl} playlist-location={playlist_path}"
    )
    pipeline = Gst.parse_launch(pipeline_desc)
    if not pipeline:
        print("smoke_rtsp_hls: parse_launch failed", file=sys.stderr)
        return 1
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    err_seen = [None]

    def on_message(bus, message):
        if message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            err_seen[0] = f"{err.message} ({debug or ''})"

    bus.connect("message", on_message)
    pipeline.set_state(Gst.State.PLAYING)
    deadline = time.monotonic() + run_sec
    while time.monotonic() < deadline and err_seen[0] is None:
        time.sleep(0.2)
    pipeline.set_state(Gst.State.NULL)
    if err_seen[0]:
        print(f"smoke_rtsp_hls: FAIL {err_seen[0]}", file=sys.stderr)
        return 1
    if os.path.isfile(playlist_path):
        print(f"smoke_rtsp_hls: OK {playlist_path} exists")
        return 0
    print(f"smoke_rtsp_hls: FAIL {playlist_path} not found", file=sys.stderr)
    return 1


def main():
    parser = argparse.ArgumentParser(description="Smoke: HLS or RTSP pipeline verification")
    sub = parser.add_subparsers(dest="cmd", required=True)
    hls_p = sub.add_parser("hls", help="videotestsrc → hlssink2 HLS generation")
    hls_p.add_argument("--out-dir", default="/tmp/smoke_hls", help="HLS output directory")
    hls_p.add_argument("--run-sec", type=float, default=5.0, help="Run duration seconds")
    rtsp_p = sub.add_parser("rtsp", help="rtspsrc → fakesink RTSP connection")
    rtsp_p.add_argument("--url", required=True, help="RTSP URL (e.g. rtsp://host/path)")
    rtsp_p.add_argument("--run-sec", type=float, default=5.0, help="Run duration seconds")
    rtsp_p.add_argument("--latency-ms", type=int, default=300, help="rtspsrc latency ms")
    rtsp_p.add_argument("--timeout-ms", type=int, default=15000, help="rtspsrc timeout ms")
    rtsp_hls_p = sub.add_parser("rtsp-hls", help="rtspsrc ! rtph264depay ! h264parse ! hlssink2 RTSP→HLS")
    rtsp_hls_p.add_argument("--url", required=True, help="RTSP URL (e.g. rtsp://host/path)")
    rtsp_hls_p.add_argument("--out-dir", default="/tmp/smoke_rtsp_hls", help="HLS output directory")
    rtsp_hls_p.add_argument("--run-sec", type=float, default=8.0, help="Run duration seconds")
    rtsp_hls_p.add_argument("--latency-ms", type=int, default=200, help="rtspsrc latency ms")
    rtsp_hls_p.add_argument("--timeout-ms", type=int, default=15000, help="rtspsrc timeout ms")
    args = parser.parse_args()
    if args.cmd == "hls":
        return smoke_hls(out_dir=args.out_dir, run_sec=args.run_sec)
    if args.cmd == "rtsp":
        return smoke_rtsp(
            url=args.url,
            run_sec=args.run_sec,
            latency_ms=args.latency_ms,
            timeout_ms=args.timeout_ms,
        )
    if args.cmd == "rtsp-hls":
        return smoke_rtsp_hls(
            url=args.url,
            out_dir=args.out_dir,
            run_sec=args.run_sec,
            latency_ms=args.latency_ms,
            timeout_ms=args.timeout_ms,
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
