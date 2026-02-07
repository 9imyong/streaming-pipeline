# UI 전환 결정: Streamlit → Next.js

## 배경

- **기존**: Streamlit 기반 Ops Console (채널 목록, START/STOP, HLS 플레이어).
- **한계**: 잦은 리렌더/스크립트 재실행 모델, 멀티채널·실시간 이벤트 표시에 부적합.

## 결정

- **운영 메인 UI**: **Next.js** (App Router, React 18, TypeScript, hls.js).
  - 브라우저 네이티브 재생 경로(MSE) 활용.
  - 멀티채널 그리드, 실시간 상태/이벤트 표시에 적합.
- **Streamlit**: **dev-only** 유지.
  - 빠른 검증·내부 도구용.
  - prod 배포 대상에서 제외. `docker compose --profile dev up streamlit` 로만 기동.

## 디렉터리 구조

```
streaming-pipeline/
├── app/                    # FastAPI gateway (기존)
├── web/                    # Next.js 운영 UI
├── apps/
│   └── streamlit/          # Streamlit (dev-only)
├── docker/
│   ├── docker-compose.yml  # web 서비스 포함, streamlit은 profile=dev
│   └── ...
└── docs/ui/
    ├── UI_DECISION.md      # 본 문서
    └── NEXTJS_GUIDE.md     # Next.js UI 가이드·경로 규칙
```

## 참고

- 백엔드(API / Orchestrator / Workers)는 기존 유지.
- UI에 필요한 조회/구독 엔드포인트만 추가 가능(예: SSE `/v1/events/stream`).
