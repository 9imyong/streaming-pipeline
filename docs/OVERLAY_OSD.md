# OSD 오버레이 확장

- `overlay_mode=OSD` 일 때 파이프라인에 삽입되는 element는 **고정 훅** 하나뿐이다.
- 코드: `app/infrastructure/runners/gstreamer.py` → `_overlay_segment()` 내 `mode == "OSD"` 분기.
- 현재 기본값: `timeoverlay` (타임스탬프만 표시). **Python 코드 변경 없이** element 문자열만 바꾸면 된다.
- DeepStream 또는 custom Gst plugin으로 교체 시: 해당 분기에서 `"timeoverlay ..."` 를 `"nvdsosd"` 또는 `"myplugin name=osd ..."` 등으로 교체.
- 파이프라인 구조는 `video ! [OSD element] ! x264enc ! ...` 이므로, 교체 element는 video sink 쪽으로 한 개만 연결되면 된다.
