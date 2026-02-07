# Streaming Pipeline — Frontend (Next.js + shadcn/ui)

운영 대시보드: 스트림/잡/워커 상태, 메트릭, 이벤트 뷰.

## 기술 스택

- Next.js 14 (App Router), TypeScript, TailwindCSS
- shadcn/ui (Radix + Tailwind)
- TanStack Table, React Query
- Zod, hls.js (선택)

## 실행

```bash
cp .env.example .env.local
npm install
npm run dev
```

브라우저: http://localhost:3000 (루트 → `/dashboard` 리다이렉트)

## 환경 변수

| 변수 | 설명 |
|------|------|
| `NEXT_PUBLIC_API_BASE_URL` | API 서버 (예: http://localhost:8000). 비우거나 없으면 mock 모드 |
| `NEXT_PUBLIC_POLL_INTERVAL_MS` | 폴링 간격(ms, 기본 2000) |
| `NEXT_PUBLIC_USE_MOCK` | `true` 시 항상 mock 데이터 사용 |

## 구조

- `src/app/(dashboard)/` — 대시보드 레이아웃 하위: dashboard, streams, jobs, workers, events, metrics, settings
- `src/components/layout/` — App Shell, SideNav, TopBar
- `src/components/ui/` — shadcn 스타일 (Button, Card, Badge, Table, Skeleton)
- `src/components/streams/` — StreamTable, StreamDetailView, StreamStatusBadge
- `src/components/jobs/` — JobTable, JobStatusBadge
- `src/components/workers/` — WorkerTable
- `src/components/events/` — EventsTable
- `src/components/dashboard/` — DashboardSummary, RecentEvents
- `src/components/common/` — Loading, ErrorState, EmptyState
- `src/lib/api/` — client, endpoints, types, mock
- `src/lib/query/` — query-client (React Query 옵션)
