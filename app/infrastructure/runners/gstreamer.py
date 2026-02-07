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


def _uri_host_for_log(uri: str) -> str:
    """로그용: URI에서 호스트:포트만 추출 (비밀번호 등 제거)."""
    if not uri or not uri.strip():
        return ""
    u = uri.strip()
    for prefix in ("rtsp://", "rtmp://", "http://", "https://"):
        if u.lower().startswith(prefix):
            rest = u[len(prefix) :].split("/")[0]
            return rest or "(empty)"
    return "(unknown)"


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


def _rtspsrc_options_from_params(params: dict) -> str:
    """StreamSpec params에서 rtspsrc 옵션 문자열 생성. 기본: protocols=tcp, latency=300, do-rtsp-keep-alive=true."""
    transport = (params.get("rtsp_transport") or "tcp").strip().lower()
    if transport not in ("tcp", "udp"):
        transport = "tcp"
    latency_ms = params.get("rtsp_latency_ms")
    if latency_ms is None:
        latency_ms = 300
    try:
        latency_ms = int(latency_ms)
    except (TypeError, ValueError):
        latency_ms = 300
    latency_ms = max(0, min(latency_ms, 60000))
    timeout_ms = params.get("rtsp_timeout_ms")
    if timeout_ms is None:
        timeout_us = 15000000  # 15초
    else:
        try:
            timeout_us = int(timeout_ms) * 1000
        except (TypeError, ValueError):
            timeout_us = 15000000
        timeout_us = max(1000000, min(timeout_us, 120000000))  # 1초~120초
    opts = f'protocols={transport} latency={latency_ms} timeout={timeout_us}'
    # do-rtsp-keep-alive: 지원 시 true (일부 서버/카메라에서 연결 유지)
    opts += " do-rtsp-keep-alive=true"
    return opts


def _video_source_segment(spec: StreamSpec) -> str:
    """RTSP/RTMP가 있으면 해당 소스 → 디코드 → raw, 없으면 videotestsrc (테스트용)."""
    uri = (spec.source_uri or "").strip()
    lower = uri.lower()
    if lower.startswith("rtsp://"):
        # RTSP는 H.264/H.265 등 코덱 다양 → 코드로 조립(_build_rtsp_pipeline)하여 pad-added에서 분기
        return "__rtsp__"
    if lower.startswith("rtmp://"):
        # RTMP는 flvdemux 동적 패드 때문에 parse_launch 대신 코드로 조립. 여기선 꼬리만 반환하지 않고 플레이스홀더.
        return "__rtmp__"
    return "videotestsrc is-live=true do-timestamp=true ! video/x-raw,framerate=25/1 ! "


def _build_pipeline_descriptor(spec: StreamSpec) -> str:
    params = spec.params or {}
    output_type = (spec.output_type or "fakesink").lower()
    channel_id = spec.channel_id
    overlay_mode = params.get("overlay_mode")
    overlay_label = params.get("overlay_label")
    overlay = _overlay_segment(overlay_mode, overlay_label)
    video_head = _video_source_segment(spec)
    encode_hls = "queue ! x264enc tune=zerolatency speed-preset=ultrafast key-int-max=25 ! h264parse ! "
    encode_fake = "queue ! x264enc tune=zerolatency speed-preset=ultrafast ! "
    if output_type == "hls":
        import os
        hls_base = os.environ.get("HLS_OUTPUT_DIR", "/tmp/hls")
        out_dir = params.get("output_path") or f"{hls_base.rstrip('/')}/{channel_id}"
        os.makedirs(out_dir, exist_ok=True)
        segment_tpl = f"{out_dir}/segment_%05d.ts"
        playlist_path = f"{out_dir}/index.m3u8"
        hls_tail = (
            f"hlssink2 target-duration=2 playlist-length=3 "
            f"location={segment_tpl} playlist-location={playlist_path}"
        )
        if video_head == "__rtmp__":
            return (
                "__rtmp__"
                + "queue ! h264parse ! avdec_h264 ! videoconvert ! video/x-raw,framerate=25/1 ! queue ! "
                + overlay
                + encode_hls
                + hls_tail
            )
        if video_head == "__rtsp__":
            return "__rtsp__"  # tail은 _build_rtsp_pipeline에서 rtspsrc→depay→parse→hlssink2 로 조립
        return video_head + overlay + encode_hls + hls_tail

    if video_head == "__rtmp__":
        return "__rtmp__" + "queue ! h264parse ! avdec_h264 ! videoconvert ! video/x-raw,framerate=25/1 ! queue ! " + overlay + encode_fake + "fakesink sync=true"
    if video_head == "__rtsp__":
        return "__rtsp__"  # tail은 _build_rtsp_pipeline에서 rtspsrc→depay→parse→fakesink 로 조립
    return video_head + overlay + encode_fake + "fakesink sync=true"


class _GstPipelineHandle:
    """Process-like handle: returncode, terminate(), wait(), publishes_lifecycle_events.
    __slots__ 미사용: _quit_glib 등 런타임에 설정되는 속성으로 인한 배포/캐시 이슈 방지.
    RTSP 등 실패 시 last_error에 rtspsrc 에러 메시지 저장 (manager에서 set_last_error에 사용).
    """

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.returncode: Optional[int] = None
        self.stderr: Optional[Any] = None  # subprocess는 StreamReader; 여기선 미사용
        self.pid: Optional[int] = None
        self.publishes_lifecycle_events: bool = True
        self.last_error: Optional[str] = None  # bus ERROR 시 메시지 (manager에서 DB last_error 저장용)
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


def _build_rtsp_pipeline(spec: StreamSpec, tail_desc: str):
    """RTSP: rtspsrc pad-added에서 H.264/H.265 분기 후 depay ! parse → hlssink2/fakesink (디코드 없이 패스스루, not-negotiated 방지)."""
    import os
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import Gst

    uri = (spec.source_uri or "").strip()
    params = spec.params or {}
    output_type = (spec.output_type or "fakesink").lower()
    channel_id = spec.channel_id
    # params.rtsp_codec=h265|hevc 이면 H.265 체인 강제, 없으면 pad caps encoding-name 자동 감지
    force_codec = (params.get("rtsp_codec") or "").strip().upper()

    pipeline = Gst.Pipeline.new(None)
    rtspsrc = Gst.ElementFactory.make("rtspsrc", "rtspsrc0")
    if not rtspsrc:
        return None
    rtspsrc.set_property("location", uri)
    transport = (params.get("rtsp_transport") or "tcp").strip().lower()
    if transport not in ("tcp", "udp"):
        transport = "tcp"
    try:
        latency_ms = int(params.get("rtsp_latency_ms") or 200)
        latency_ms = max(0, min(latency_ms, 60000))
    except (TypeError, ValueError):
        latency_ms = 200
    try:
        timeout_us = int(params.get("rtsp_timeout_ms") or 15000) * 1000
        timeout_us = max(1000000, min(timeout_us, 120000000))
    except (TypeError, ValueError):
        timeout_us = 15000000
    rtspsrc.set_property("latency", latency_ms)
    rtspsrc.set_property("timeout", timeout_us)
    try:
        gi.require_version("GstRtsp", "1.0")
        from gi.repository import GstRtsp
        protocols_val = getattr(GstRtsp.RTSPLowerTrans, transport.upper(), 4)
        rtspsrc.set_property("protocols", protocols_val)
    except (ValueError, AttributeError):
        pass
    try:
        rtspsrc.set_property("do-rtsp-keep-alive", True)
    except Exception:
        pass
    pipeline.add(rtspsrc)

    # output=hls: hlssink2만 추가. pad-added에서 depay ! parse → hlssink2 video request pad 연결.
    # output=fakesink: fakesink만 추가. pad-added에서 depay ! parse → fakesink 연결.
    if output_type == "hls":
        hls_base = os.environ.get("HLS_OUTPUT_DIR", "/tmp/hls")
        out_dir = params.get("output_path") or f"{hls_base.rstrip('/')}/{channel_id}"
        os.makedirs(out_dir, exist_ok=True)
        segment_tpl = f"{out_dir}/segment_%05d.ts"
        playlist_path = f"{out_dir}/index.m3u8"
        target_dur = max(2, min(10, int(params.get("hls_target_duration_sec") or 4)))
        playlist_len = max(3, min(20, int(params.get("hls_playlist_length") or 6)))
        hlssink2 = Gst.ElementFactory.make("hlssink2", "hlssink2")
        if not hlssink2:
            return None
        hlssink2.set_property("target-duration", target_dur)
        hlssink2.set_property("playlist-length", playlist_len)
        hlssink2.set_property("location", segment_tpl)
        hlssink2.set_property("playlist-location", playlist_path)
        pipeline.add(hlssink2)
        sink_el = hlssink2
        sink_pad_getter = lambda: hlssink2.get_request_pad("video")
    else:
        fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
        if not fakesink:
            return None
        fakesink.set_property("sync", True)
        pipeline.add(fakesink)
        sink_el = fakesink
        sink_pad_getter = lambda: fakesink.get_static_pad("sink")

    def _on_rtsp_pad_added(src, pad):
        if pad.is_linked():
            return
        caps = pad.get_current_caps() or pad.query_caps(None)
        if not caps or caps.is_empty():
            return
        st = caps.get_structure(0)
        if not st:
            return
        if (st.get_name() or "") != "application/x-rtp":
            return
        media = (st.get_string("media") or "").lower()
        if media and media != "video":
            return
        # params.rtsp_codec=h265|hevc 이면 H.265, 없으면 pad caps encoding-name 사용, 없으면 H.264
        if force_codec in ("H265", "HEVC"):
            encoding = "H265"
        else:
            encoding = (st.get_string("encoding-name") or "").upper() or "H264"
            if encoding not in ("H264", "H265", "HEVC"):
                encoding = "H264"
        queue_el = Gst.ElementFactory.make("queue", None)
        if encoding in ("H265", "HEVC"):
            depay = Gst.ElementFactory.make("rtph265depay", None)
            parse_el = Gst.ElementFactory.make("h265parse", None)
        else:
            depay = Gst.ElementFactory.make("rtph264depay", None)
            parse_el = Gst.ElementFactory.make("h264parse", None)
        # H.264: 매 IDR마다 SPS/PPS 삽입 → 세그먼트 경계에서 디코더가 독립 디코딩 가능 (멈춤 완화)
        if parse_el and encoding not in ("H265", "HEVC"):
            try:
                parse_el.set_property("config-interval", -1)
            except Exception:
                pass
        queue2 = Gst.ElementFactory.make("queue", None) if output_type == "hls" else None
        if not queue_el or not depay or not parse_el:
            return
        for el in (queue_el, depay, parse_el):
            pipeline.add(el)
        if queue2:
            pipeline.add(queue2)
        queue_el.link(depay)
        depay.link(parse_el)
        if queue2:
            parse_el.link(queue2)
        sink_pad = sink_pad_getter()
        if not sink_pad:
            return
        if pad.link(queue_el.get_static_pad("sink")) != Gst.PadLinkReturn.OK:
            return
        tail_src = queue2.get_static_pad("src") if queue2 else parse_el.get_static_pad("src")
        if tail_src.link(sink_pad) != Gst.PadLinkReturn.OK:
            return
        for el in (queue_el, depay, parse_el) + ((queue2,) if queue2 else ()):
            el.sync_state_with_parent()

    rtspsrc.connect("pad-added", _on_rtsp_pad_added)
    return pipeline


def _build_rtmp_pipeline(spec: StreamSpec, tail_desc: str):
    """RTMP: rtmpsrc ! flvdemux, pad-added 시 비디오만 tail에 연결.
    hlssink2는 request pad 사용·bin 내부에서 splitmuxsink 링크 실패하므로, tail은 bin(hlssink2 제외) + hlssink2를 파이프라인에 직접 추가.
    """
    import os
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import Gst

    uri = (spec.source_uri or "").strip()
    lower = uri.lower()
    loc = f"{uri} live=1" if " " not in uri and "live=" not in uri.lower() else uri

    params = spec.params or {}
    output_type = (spec.output_type or "fakesink").lower()
    channel_id = spec.channel_id
    overlay = _overlay_segment(params.get("overlay_mode"), params.get("overlay_label"))
    # tail_bin은 hlssink2 직전까지; 맨 끝에 ' ! ' 없이 (parse_bin_from_description 구문 오류 방지)
    encode_hls_to_h264 = "queue ! x264enc tune=zerolatency speed-preset=ultrafast key-int-max=25 ! h264parse"

    pipeline = Gst.Pipeline.new(None)
    rtmpsrc = Gst.ElementFactory.make("rtmpsrc", "rtmpsrc0")
    flvdemux = Gst.ElementFactory.make("flvdemux", "demux")
    if not rtmpsrc or not flvdemux:
        return None
    rtmpsrc.set_property("location", loc)
    # timeout(초): 데이터 미수신 시 대기. rtmp_timeout_sec 또는 rtsp_timeout_ms 사용, 기본 30초
    try:
        if params.get("rtmp_timeout_sec") is not None:
            t = int(params.get("rtmp_timeout_sec"))
        else:
            t = int((params.get("rtsp_timeout_ms") or 30000) / 1000)
        rtmpsrc.set_property("timeout", max(10, min(t, 300)))
    except (TypeError, ValueError):
        rtmpsrc.set_property("timeout", 30)
    pipeline.add(rtmpsrc)
    pipeline.add(flvdemux)
    rtmpsrc.link(flvdemux)

    # RTMP는 H.264/H.265 등 코덱 다양 → decodebin으로 디코딩 후 H.264 재인코딩 (not-negotiated 방지)
    decodebin = Gst.ElementFactory.make("decodebin", "decodebin0")
    if not decodebin:
        return None
    pipeline.add(decodebin)

    # tail: decodebin 출력(video/x-raw)부터; hlssink2는 request pad라 bin 밖에 추가
    if output_type == "hls":
        hls_base = os.environ.get("HLS_OUTPUT_DIR", "/tmp/hls")
        out_dir = params.get("output_path") or f"{hls_base.rstrip('/')}/{channel_id}"
        os.makedirs(out_dir, exist_ok=True)
        segment_tpl = f"{out_dir}/segment_%05d.ts"
        playlist_path = f"{out_dir}/index.m3u8"
        tail_bin_desc = (
            "videoconvert ! video/x-raw,framerate=25/1 ! queue ! "
            + overlay
            + encode_hls_to_h264
        )
        tail_bin = Gst.parse_bin_from_description(tail_bin_desc, True)
        if not tail_bin:
            return None
        pipeline.add(tail_bin)
        _add_ghost_pads(tail_bin, has_output=True)
        target_dur = max(2, min(10, int(params.get("hls_target_duration_sec") or 4)))
        playlist_len = max(3, min(20, int(params.get("hls_playlist_length") or 6)))
        hlssink2 = Gst.ElementFactory.make("hlssink2", "hlssink2")
        if not hlssink2:
            return None
        hlssink2.set_property("target-duration", target_dur)
        hlssink2.set_property("playlist-length", playlist_len)
        hlssink2.set_property("location", segment_tpl)
        hlssink2.set_property("playlist-location", playlist_path)
        pipeline.add(hlssink2)
        tail_src = tail_bin.get_static_pad("src")
        video_pad = hlssink2.get_request_pad("video")
        if tail_src and video_pad:
            tail_src.link(video_pad)
    else:
        tail_bin_desc = (
            "videoconvert ! video/x-raw,framerate=25/1 ! queue ! "
            + overlay
            + "queue ! x264enc tune=zerolatency speed-preset=ultrafast ! fakesink sync=true"
        )
        tail_bin = Gst.parse_bin_from_description(tail_bin_desc, True)
        if not tail_bin:
            return None
        pipeline.add(tail_bin)
        _add_ghost_pads(tail_bin, has_output=False)

    def _on_flv_pad_added(demux, pad):
        if pad.is_linked():
            return
        name = pad.get_name() or ""
        if "video" not in name.lower():
            return
        sink = decodebin.get_static_pad("sink")
        if sink:
            pad.link(sink)

    def _on_decode_pad_added(dec, pad):
        if pad.is_linked():
            return
        caps = pad.get_current_caps() or pad.query_caps(None)
        if not caps or caps.is_empty():
            return
        s = caps.get_structure(0)
        if not s or not s.get_name().startswith("video/"):
            return
        sink = tail_bin.get_static_pad("sink")
        if sink:
            pad.link(sink)

    flvdemux.connect("pad-added", _on_flv_pad_added)
    decodebin.connect("pad-added", _on_decode_pad_added)
    return pipeline


def _add_ghost_pads(bin_el, has_output: bool = False) -> None:
    """bin에 sink ghost pad 추가. has_output이면 아직 링크 안 된 src 패드를 src ghost로 추가."""
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import Gst

    it = bin_el.iterate_elements()
    if not it:
        return
    unlinked_sink = None
    unlinked_src = None
    while True:
        res, el = it.next()
        if res != 1 or not el:
            break
        sp = el.get_static_pad("sink")
        if sp and not sp.is_linked():
            unlinked_sink = sp
        src = el.get_static_pad("src")
        if src and not src.is_linked():
            unlinked_src = src
    if unlinked_sink:
        bin_el.add_pad(Gst.GhostPad.new("sink", unlinked_sink))
    if has_output and unlinked_src:
        bin_el.add_pad(Gst.GhostPad.new("src", unlinked_src))


def _run_pipeline_thread(
    pipeline_desc: str,
    spec: StreamSpec,
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
    pipeline = None
    if pipeline_desc.startswith("__rtsp__"):
        tail_desc = pipeline_desc[len("__rtsp__") :].strip()
        pipeline = _build_rtsp_pipeline(spec, tail_desc)
        if not pipeline:
            handle.returncode = 1
            handle.last_error = "_build_rtsp_pipeline failed"
            logger.error("channel_id=%s _build_rtsp_pipeline failed tail_desc=%s", channel_id, tail_desc[:200])
            handle._done.set()
            return
    elif pipeline_desc.startswith("__rtmp__"):
        tail_desc = pipeline_desc[len("__rtmp__") :].strip()
        pipeline = _build_rtmp_pipeline(spec, tail_desc)
        if not pipeline:
            handle.returncode = 1
            handle.last_error = "_build_rtmp_pipeline failed"
            logger.error("channel_id=%s _build_rtmp_pipeline failed tail_desc=%s", channel_id, tail_desc[:200])
            handle._done.set()
            return
    else:
        try:
            pipeline = Gst.parse_launch(pipeline_desc)
        except Exception as e:
            handle.returncode = 1
            handle.last_error = str(e)[:1024]
            logger.exception(
                "channel_id=%s Gst.parse_launch failed: %s pipeline_desc=%s",
                channel_id,
                e,
                pipeline_desc[:350],
            )
            handle._done.set()
            return
        if not pipeline:
            handle.returncode = 1
            handle.last_error = "parse_launch returned NULL"
            logger.error("channel_id=%s Gst.parse_launch returned NULL pipeline_desc=%s", channel_id, pipeline_desc[:350])
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
            handle.last_error = err_str[:1024]  # RTSP 실패 등 last_error에 저장 (manager → DB)
            logger.error(
                "Gst pipeline ERROR channel_id=%s: %s",
                channel_id,
                err_str[:500],
                extra={"channel_id": channel_id},
            )
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
        err_msg = "set_state PLAYING failed (check RTSP URL, network, codec)"
        handle.last_error = err_msg
        logger.error("Gst pipeline channel_id=%s: %s", channel_id, err_msg, extra={"channel_id": channel_id})
        _publish("FAILED", message=err_msg, last_error=err_msg)
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
        uri = (spec.source_uri or "").strip()
        source_hint = "rtmp" if uri.lower().startswith("rtmp://") else ("rtsp" if uri.lower().startswith("rtsp://") else "videotestsrc")
        logger.info(
            "channel_id=%s starting Gst pipeline source=%s uri_host=%s (no frame pull)",
            spec.channel_id,
            source_hint,
            _uri_host_for_log(uri),
        )
        logger.debug("channel_id=%s pipeline_desc=%s", spec.channel_id, pipeline_desc[:400])

        handle = _GstPipelineHandle(self._loop)
        job_id = (spec.params or {}).get("job_id")

        params = spec.params or {}
        overlay_mode = params.get("overlay_mode")
        overlay_label = params.get("overlay_label")

        def run() -> None:
            _run_pipeline_thread(
                pipeline_desc,
                spec,
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
