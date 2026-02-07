"""
Streamlit Ops Console. API Gateway만 호출 (Kafka/DB 직접 접근 금지).
- 채널 목록/상태, START/STOP, last_error/restart_count, HLS 재생, AI 최신 결과.
- 환경변수: API_BASE_URL, HLS_BASE_URL. 5초마다 자동 refresh.
"""
import os
import streamlit as st
import httpx

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    def st_autorefresh(interval: int): pass

from components.hls_player import render_hls

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")
HLS_BASE_URL = os.environ.get("HLS_BASE_URL", "http://localhost/hls").rstrip("/")
REFRESH_MS = 5000

st.set_page_config(page_title="Streaming Ops", layout="wide")
st_autorefresh(interval=REFRESH_MS)


@st.cache_data(ttl=2)
def _fetch_streams():
    try:
        r = httpx.get(f"{API_BASE_URL}/v1/streams", timeout=5.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


@st.cache_data(ttl=2)
def _fetch_stream(channel_id: str):
    try:
        r = httpx.get(f"{API_BASE_URL}/v1/streams/{channel_id}", timeout=5.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


@st.cache_data(ttl=2)
def _fetch_ai_latest(channel_id: str):
    try:
        r = httpx.get(f"{API_BASE_URL}/v1/streams/{channel_id}/ai/latest", timeout=5.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def main():
    st.title("Streaming Ops Console")
    st.caption(f"API: {API_BASE_URL} | HLS: {HLS_BASE_URL or '(not set)'} | Refresh every {REFRESH_MS//1000}s")

    # ----- 채널 추가 폼 -----
    with st.expander("➕ Add channel", expanded=True):
        with st.form("add_channel_form"):
            c1, c2 = st.columns(2)
            with c1:
                new_channel_id = st.text_input("Channel ID", placeholder="e.g. ch1, cam-01", key="new_channel_id")
                new_source_rtsp = st.text_input("Source RTSP URL", placeholder="rtsp://host/path", key="new_source_rtsp")
                new_output = st.selectbox("Output", ["hls", "rtsp", "mjpeg"], index=0, key="new_output")
            with c2:
                new_ai_profile = st.text_input("AI profile (optional)", placeholder="", key="new_ai_profile")
                new_overlay_mode = st.selectbox(
                    "Overlay mode (optional)",
                    ["NONE", "SIMPLE", "OSD"],
                    index=0,
                    key="new_overlay_mode",
                )
                new_overlay_label = st.text_input("Overlay label (optional)", placeholder="", key="new_overlay_label")
            submitted = st.form_submit_button("Add channel")
            if submitted:
                if not (new_channel_id and new_channel_id.strip()) or not (new_source_rtsp and new_source_rtsp.strip()):
                    st.error("Channel ID and Source RTSP URL are required.")
                else:
                    try:
                        body = {
                            "channel_id": new_channel_id.strip(),
                            "source_rtsp": new_source_rtsp.strip(),
                            "output": new_output,
                        }
                        if new_ai_profile and new_ai_profile.strip():
                            body["ai_profile"] = new_ai_profile.strip()
                        if new_overlay_mode and new_overlay_mode != "NONE":
                            body["overlay_mode"] = new_overlay_mode
                        if new_overlay_label and new_overlay_label.strip():
                            body["overlay_label"] = new_overlay_label.strip()
                        r = httpx.post(
                            f"{API_BASE_URL}/v1/streams/",
                            json=body,
                            timeout=10.0,
                        )
                        if r.status_code in (200, 202):
                            _fetch_streams.clear()
                            _fetch_stream.clear()
                            _fetch_ai_latest.clear()
                            st.success(f"Channel added: {body['channel_id']} (job_id: {r.json().get('job_id', '—')})")
                            st.rerun()
                        else:
                            st.error(r.text or str(r.status_code))
                    except Exception as e:
                        st.error(str(e))

    streams = _fetch_streams()
    if not streams:
        st.info("No streams yet. Add one above or wait for the list to refresh.")
        return

    # 채널 리스트 테이블
    st.subheader("Channels")
    table = [
        {
            "channel_id": s.get("channel_id"),
            "status": s.get("status"),
            "desired_state": s.get("desired_state"),
            "worker_id": s.get("assigned_worker_id") or "—",
            "restart_count": s.get("restart_count", 0),
            "updated_at": (s.get("updated_at") or "—")[:19] if s.get("updated_at") else "—",
            "last_error": ((s.get("last_error") or "—")[:80]),
        }
        for s in streams
    ]
    st.dataframe(table, width="stretch", hide_index=True)

    # 채널 선택
    channel_ids = [s["channel_id"] for s in streams]
    selected = st.selectbox("Select channel", channel_ids, key="channel_select")
    if not selected:
        return

    # 소스 URL 수정 (채널에 저장된 URL이 example이면 여기서 실제 URL로 바꾼 뒤 START)
    info = _fetch_stream(selected)
    params = (info or {}).get("pipeline_params") or {}
    current_url = params.get("source_rtsp", "").strip() or ""
    new_url = st.text_input(
        "Source RTSP/RTMP URL",
        value=current_url,
        key=f"edit_source_rtsp_{selected}",
        placeholder="rtsp://... 또는 rtmp://...:1935/...",
        help="저장된 URL이 example이면 실제 주소로 수정 후 'Update URL'을 누르세요. 그 다음 START.",
    )
    if st.button("Update URL", key=f"btn_update_url_{selected}"):
        if not new_url or not new_url.strip():
            st.warning("URL을 입력하세요.")
        else:
            try:
                r = httpx.patch(
                    f"{API_BASE_URL}/v1/streams/{selected}",
                    json={"source_rtsp": new_url.strip()},
                    timeout=10.0,
                )
                if r.status_code == 200:
                    st.success("소스 URL이 저장되었습니다. START를 누르면 이 URL로 시작합니다.")
                    _fetch_stream.clear()
                else:
                    st.error(r.text or str(r.status_code))
            except Exception as e:
                st.error(str(e))

    # START / STOP / 채널 삭제
    col1, col2, col3, _ = st.columns([1, 1, 1, 3])
    with col1:
        if st.button("START", key="btn_start"):
            with st.spinner("Starting..."):
                try:
                    # 채널에 저장된 source_rtsp 사용 (없으면 사용자 입력 요청)
                    info = _fetch_stream(selected)
                    params = (info or {}).get("pipeline_params") or {}
                    source_rtsp = params.get("source_rtsp", "").strip()
                    if not source_rtsp:
                        st.error("이 채널에 소스 URL이 없습니다. 채널을 삭제 후 'Add channel'에서 URL을 넣고 다시 추가하세요.")
                    else:
                        r = httpx.post(
                            f"{API_BASE_URL}/v1/streams/",
                            json={
                                "channel_id": selected,
                                "source_rtsp": source_rtsp,
                                "output": params.get("output", "hls"),
                            },
                            timeout=10.0,
                        )
                        if r.status_code in (200, 202):
                            st.success("START accepted")
                            _fetch_streams.clear()
                            _fetch_stream.clear()
                            _fetch_ai_latest.clear()
                        else:
                            st.error(r.text or str(r.status_code))
                except Exception as e:
                    st.error(str(e))
    with col2:
        if st.button("STOP", key="btn_stop"):
            with st.spinner("Stopping..."):
                try:
                    r = httpx.delete(f"{API_BASE_URL}/v1/streams/{selected}", timeout=10.0)
                    if r.status_code in (200, 202):
                        st.success("STOP accepted")
                        _fetch_streams.clear()
                        _fetch_stream.clear()
                        _fetch_ai_latest.clear()
                    else:
                        st.error(r.text or str(r.status_code))
                except Exception as e:
                    st.error(str(e))
    with col3:
        if st.button("채널 삭제", key="btn_delete"):
            with st.spinner("삭제 중..."):
                try:
                    r = httpx.delete(f"{API_BASE_URL}/v1/streams/{selected}/record", timeout=10.0)
                    if r.status_code == 200:
                        st.success("채널이 목록에서 삭제되었습니다.")
                        _fetch_streams.clear()
                        _fetch_stream.clear()
                        _fetch_ai_latest.clear()
                        st.rerun()
                    else:
                        st.error(r.text or str(r.status_code))
                except Exception as e:
                    st.error(str(e))

    # 상태 / last_error / restart_count
    info = _fetch_stream(selected)
    if info:
        st.subheader("Status")
        st.json({"status": info.get("status"), "worker_id": info.get("worker_id"), "desired_state": info.get("desired_state"), "last_error": info.get("last_error"), "restart_count": info.get("restart_count", 0)})

    # HLS 플레이어 — m3u8/ts는 HLS_BASE_URL(nginx 또는 API)에서 로드, hls.js로 재생 (FastAPI 스트리밍 아님)
    st.subheader("HLS Player")
    m3u8_url = f"{HLS_BASE_URL}/{selected}/index.m3u8" if HLS_BASE_URL else ""
    if m3u8_url:
        render_hls(m3u8_url, height=360, autoplay=True)
        st.caption(f"m3u8: `{m3u8_url}` (hls.js가 이 URL에서 로드, nginx 사용 시 80에서 서빙)")
    else:
        st.write("Set HLS_BASE_URL for playback.")

    # AI latest
    st.subheader("AI Latest")
    ai = _fetch_ai_latest(selected)
    if ai and (ai.get("ts") or ai.get("top_detections")):
        st.json({"ts": ai.get("ts"), "labels": ai.get("labels"), "top_detections": ai.get("top_detections", [])[:5]})
    else:
        st.write("No latest AI result (not yet published).")


if __name__ == "__main__":
    main()
