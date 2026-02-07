# Next.js 운영 UI 가이드

## 개요

- **앱 위치**: `web/` (프로젝트 루트)
- **기술**: Next.js 14 (App Router), TypeScript, TailwindCSS, hls.js, SWR
- **환경변수**: `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_HLS_BASE_URL`

## 페이지

| 경로 | 설명 |
|------|------|
| `/` | 홈 안내 + /channels, /events 링크 |
| `/channels` | 채널 목록, 멀티 채널 HLS 그리드, Start/Stop |
| `/events` | 실시간 이벤트 로그 (SSE 연동 시 표시) |

## HLS 경로 규칙

- **m3u8**: `{HLS_BASE_URL}/{channel_id}/index.m3u8`
- **세그먼트**: `{HLS_BASE_URL}/{channel_id}/segment_00001.ts` (hlssink2 출력 규칙)
- **권장**: nginx가 `/hls/*` 를 디스크에서 직접 서빙 (CORS, Range, Cache 헤더 안정화)

## API 연동

- `GET /v1/streams` — 목록
- `GET /v1/streams/:id` — 상세
- `POST /v1/streams` — Start (body: channel_id, source_rtsp, output)
- `DELETE /v1/streams/:id` — Stop

(선택) 실시간 이벤트: `GET /v1/events/stream` (SSE) 추가 시 `/events` 페이지에서 구독.

## 로컬 실행

```bash
cd web
cp .env.example .env.local
npm install
npm run dev
```

브라우저: http://localhost:3000

## Docker

```bash
docker compose -f docker/docker-compose.yml up -d web
```

운영 UI: http://localhost:3000  
Streamlit(dev-only): `docker compose --profile dev up -d streamlit` → http://localhost:8501
