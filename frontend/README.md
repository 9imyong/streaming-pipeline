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
| `NEXT_PUBLIC_USE_MOCK` | `false`(기본) = 실제 API, `true` = mock 데이터 |
| `NEXT_PUBLIC_POLL_INTERVAL_MS` | 폴링 간격(ms, 기본 2000) |

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

## MVP 1차 (Streams 중심) — 작업지시서 대비

| # | 항목 | 상태 |
|---|------|------|
| 1 | Bootstrap + App Shell, 라우트(dashboard/streams/…/settings) | ✅ |
| 2 | API Client + Stub (client, endpoints, types, mock, env) | ✅ |
| 3 | Streams 리스트 MVP (테이블, 검색, status 필터, 정렬, 폴링) | ✅ |
| 4 | Stream 상세 + Start/Stop/Retry, toast, 이벤트 placeholder | ✅ |
| 5 | Dashboard 요약 카드 4개 | ✅ |
| 6 | 체크리스트(아래) | ✅ |

## 체크리스트 (작업지시서 §6)

- [x] frontend/ 폴더만으로 독립 실행 가능
- [x] env로 mock/real 전환 가능 (`NEXT_PUBLIC_USE_MOCK`)
- [x] 폴링 주기 env로 조절 가능 (`NEXT_PUBLIC_POLL_INTERVAL_MS`)
- [x] 에러/로딩/빈 상태 UI 기본 제공 (skeleton/empty/error)

## 2차: Jobs / Workers / Events / Metrics MVP + 관측성

- [x] Jobs: 검색·status 필터·페이지네이션, 상세(payload/result/error_code/stack)
- [x] Workers: status 필터, DOWN만 보기
- [x] Events: stream_id/level/type 필터, limit 200, ERROR 강조, row 클릭 → payload 모달
- [x] Metrics: active_streams, jobs_rate, p95_latency_ms, error_rate 카드
- [x] Stream 상세: 최근 이벤트 20개 embed, 관련 Jobs 링크
- [x] 폴링(detail 1~2s, events 3~5s) / 에러 retry / x-request-id·duration 로깅
