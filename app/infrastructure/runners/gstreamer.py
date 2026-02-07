"""
GStreamer 기반 StreamRunner. Python Gst 파이프라인 구성/제어.
- 프레임을 Python으로 꺼내지 않음. bus ERROR/EOS/STATE_CHANGED → stream.events STARTED/FAILED/STOPPED.
- channel_id당 파이프라인 1개. stop 시 graceful shutdown (pipeline → NULL).
"""
from __future__ import annotations

import asyncio
import logging
import threading
from typing import Any, Optional

from app.application.dto import StreamSpec
from app.application.ports.event_bus import EventBus

logger = logging.getLogger(__name__)

# Gst는 스레드에서만 초기화 (메인 스레드가 아닐 수 있음)
def _init_gst() -> None:
    try:
        import gi
        gi.require_version("Gst", "1.0")
        from gi.repository import Gst
        Gst.init(None)
    except (ImportError, ValueError) as e:
        raise RuntimeError(
            "GStreamer Python bindings required. Install: apt install gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good; pip install PyGObject"
        ) from e


def _overlay_segment(overlay_mode: Optional[str], overlay_label: Optional[str]) -> str:
    """
    overlay_mode=NONE|SIMPLE|OSD 에 따른 파이프라인 세그먼트.
    - NONE: 없음.
    - SIMPLE: textoverlay name=overlay (주기적으로 overlay_store에서 갱신).
    - OSD: 메타데이터 주입 훅(고정). DeepStream/custom plugin 교체 가능.
    """
    mode = (overlay_mode or "NONE").upper()
    if mode == "NONE":
        return ""
    if mode == "SIMPLE":
        # 초기 텍스트; 런타임에 overlay_store 기반으로 갱신
        fallback = (overlay_label or "—").replace('"', '\\"')[:64]
        return f'textoverlay name=overlay text="{fallback}" valignment=top halignment=left ! '
    if mode == "OSD":
        # 고정 훅: element 이름만 바꿔서 DeepStream/custom plugin 교체 가능 (docs/OVERLAY_OSD.md)
        return "timeoverlay valignment=top halignment=left ! "
    return ""


def _build_pipeline_descriptor(spec: StreamSpec) -> str:
    """최소 동작: videotestsrc -> [overlay] -> x264enc -> fakesink. overlay_mode에 따라 NONE|SIMPLE|OSD."""
    params = spec.params or {}
    output_type = (spec.output_type or "fakesink").lower()
    channel_id = spec.channel_id
    overlay_mode = params.get("overlay_mode")
    overlay_label = params.get("overlay_label")
    overlay = _overlay_segment(overlay_mode, overlay_label)
    video_head = "videotestsrc ! video/x-raw,framerate=25/1 ! "
    encode_tail = "x264enc tune=zerolatency speed-preset=1 ! "

    if output_type == "hls":
        import os
        out_dir = params.get("output_path") or f"/tmp/hls/{channel_id}"
        os.makedirs(out_dir, exist_ok=True)
        seg = os.path.join(out_dir, "seg%05d.ts")
        return (
            video_head + overlay + encode_tail
            + "mpegtsmux ! hlssink2 target-duration=2 playlist-length=3 "
            f"location={seg}"
        )
    return video_head + overlay + encode_tail + "fakesink sync=true"


class _GstPipelineHandle:
    """Process-like handle: returncode, terminate(), wait(), publishes_lifecycle_events."""

    __slots__ = (
        "returncode", "stderr", "pid", "publishes_lifecycle_events",
        "_done", "_loop", "_pipeline_id", "_thread",
    )

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.returncode: Optional[int] = None
        self.stderr: Optional[Any] = None  # subprocess는 StreamReader; 여기선 미사용
        self.pid: Optional[int] = None
        self.publishes_lifecycle_events: bool = True
        self._done = threading.Event()
        self._loop = loop
        self._pipeline_id: Optional[str] = None
        self._thread: Optional[threading.Thread] = None
        self._quit_glib: Optional[Any] = None  # main_loop.quit 호출용

    def terminate(self) -> None:
        if self._quit_glib:
            self._quit_glib()

    def kill(self) -> None:
        self.terminate()

    async def wait(self) -> None:
        def _block() -> None:
            self._done.wait()

        await asyncio.get_running_loop().run_in_executor(None, _block)


def _run_pipeline_thread(
    pipeline_desc: str,
    channel_id: str,
    worker_id: str,
    job_id: Optional[str],
    event_bus: EventBus,
    loop: asyncio.AbstractEventLoop,
    handle: _GstPipelineHandle,
    overlay_mode: Optional[str] = None,
    overlay_label: Optional[str] = None,
) -> None:
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import GLib, Gst

    _init_gst()
    pipeline = Gst.parse_launch(pipeline_desc)
    if not pipeline:
        handle.returncode = 1
        handle._done.set()
        return

    main_loop = GLib.MainLoop()
    handle._pipeline_id = channel_id

    # SIMPLE: overlay_store에서 주기적으로 텍스트 갱신
    if (overlay_mode or "").upper() == "SIMPLE":
        from app.services.worker_stream.overlay_store import (
            get_detections_sync,
            format_detections_to_label_string,
        )

        overlay_el = pipeline.get_by_name("overlay")
        fallback_text = (overlay_label or "—")[:64]

        def _update_overlay_text() -> bool:
            if overlay_el is None:
                return False
            if handle._done.is_set():
                return False  # 파이프라인 종료 시 타이머 중단
            try:
                dets = get_detections_sync(channel_id)
                text = format_detections_to_label_string(dets) or fallback_text
                overlay_el.set_property("text", text[:256])
            except Exception:  # noqa: BLE001
                pass
            return True  # 계속 주기 호출

        GLib.timeout_add(500, _update_overlay_text)

    def _publish(event_type: str, message: Optional[str] = None, last_error: Optional[str] = None) -> None:
        async def _do() -> None:
            from app.infrastructure.messaging.kafka.schemas import stream_event_payload
            from app.infrastructure.messaging.kafka.topics import STREAM_EVENTS
            pl = stream_event_payload(
                event=event_type,
                channel_id=channel_id,
                worker_id=worker_id,
                job_id=job_id,
                message=message,
                last_error=last_error,
            )
            await event_bus.publish_event(STREAM_EVENTS, channel_id, pl)

        asyncio.run_coroutine_threadsafe(_do(), loop)  # 비동기 발행만 스케줄, Gst 스레드 블록 방지

    def _on_bus_message(bus: Any, message: Any, _: Any) -> bool:
        t = message.type
        if t == Gst.MessageType.EOS:
            handle.returncode = 0
            _publish("STOPPED", message="eos")
            main_loop.quit()
            return False
        if t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            err_str = f"{err.message} ({debug or ''})"
            handle.returncode = 1
            _publish("FAILED", message=err_str, last_error=err_str[:1024])
            main_loop.quit()
            return False
        if t == Gst.MessageType.STATE_CHANGED:
            if message.src == pipeline and message.parse_state_changed()[1] == Gst.State.PLAYING:
                _publish("STARTED")
        return True

    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", _on_bus_message, None)

    def _quit() -> None:
        try:
            pipeline.set_state(Gst.State.NULL)
        except Exception:
            pass
        main_loop.quit()

    handle._quit_glib = _quit

    ret = pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        handle.returncode = 1
        _publish("FAILED", message="set_state PLAYING failed")
        handle._done.set()
        return

    try:
        main_loop.run()
    except Exception as e:
        handle.returncode = 1
        logger.exception("channel_id=%s main_loop.run: %s", channel_id, e)
    finally:
        pipeline.set_state(Gst.State.NULL)
        if handle.returncode is None:
            handle.returncode = 0
        handle._done.set()


class GstreamerStreamRunner:
    """
    Python Gst 파이프라인 실행. bus ERROR/EOS/STATE_CHANGED → stream.events 발행.
    spawn(spec) 반환값은 Process-like handle (terminate, wait, returncode, publishes_lifecycle_events=True).
    """

    def __init__(self, worker_id: str, event_bus: EventBus, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self._worker_id = worker_id
        self._event_bus = event_bus
        self._loop = loop or asyncio.get_event_loop()

    async def spawn(self, spec: StreamSpec) -> _GstPipelineHandle:
        pipeline_desc = _build_pipeline_descriptor(spec)
        logger.info("channel_id=%s starting Gst pipeline (no frame pull)", spec.channel_id)

        handle = _GstPipelineHandle(self._loop)
        job_id = (spec.params or {}).get("job_id")

        params = spec.params or {}
        overlay_mode = params.get("overlay_mode")
        overlay_label = params.get("overlay_label")

        def run() -> None:
            _run_pipeline_thread(
                pipeline_desc,
                spec.channel_id,
                self._worker_id,
                job_id,
                self._event_bus,
                self._loop,
                handle,
                overlay_mode=overlay_mode,
                overlay_label=overlay_label,
            )

        t = threading.Thread(target=run, name=f"gst-{spec.channel_id}", daemon=True)
        handle._thread = t
        t.start()
        return handle
