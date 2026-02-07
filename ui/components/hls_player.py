"""
HLS(m3u8) 재생 컴포넌트. hls.js 사용. st.video()는 m3u8 미지원 브라우저 대비.
- url은 Streamlit에서만 주입. JS 내 임의 변경 금지(기본 수준).
"""
import streamlit.components.v1 as components


def render_hls(url: str, height: int = 360, autoplay: bool = True) -> None:
    """
    video 태그 + hls.js로 m3u8 재생.
    HLS native 지원 브라우저면 video.src=url, 아니면 hls.js attachMedia + loadSource.
    """
    if not url or not url.strip():
        return
    # XSS 완화: url을 이스케이프해 JS에 주입
    url_escaped = url.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
    html = f"""
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
</head>
<body style="margin:0;">
  <video id="hls-video" width="100%" height="{height}" controls {'autoplay' if autoplay else ''} muted playsinline></video>
  <script>
(function() {{
  var url = "{url_escaped}";
  var video = document.getElementById("hls-video");
  if (!url) return;
  if (video.canPlayType("application/vnd.apple.mpegurl") || video.canPlayType("application/x-mpegURL")) {{
    video.src = url;
  }} else if (window.Hls && Hls.isSupported()) {{
    var hls = new Hls();
    hls.loadSource(url);
    hls.attachMedia(video);
  }} else {{
    video.src = url;
  }}
}})();
  </script>
</body>
</html>
"""
    components.html(html, height=height + 40, scrolling=False)
