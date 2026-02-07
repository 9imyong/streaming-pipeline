# MVP Observability 요구사항 vs 현재 구현 비교

| 요구사항 | 현재 구현 | 상태 |
|----------|-----------|------|
| **orchestrator / worker-stream에 Prometheus /metrics** | API에만 `GET /v1/observability` (JSON) | ❌ 갭 — orchestrator·worker는 HTTP 서버 없음 |
| **streams_running (gauge)** | `/v1/observability` counts.streams_running (JSON) | ⚠️ 형식만 다름 — Prometheus 텍스트 노출 필요 |
| **streams_failed_total (counter)** | counts.streams_failed (JSON) | ⚠️ 동일 |
| **streams_reassign_total (counter)** | 없음 | ❌ 갭 — lease 만료 재할당 시 inc 필요 |
| **worker_restarts_total (counter)** | restarts_total (DB 합계, JSON) | ⚠️ worker별 counter 노출 필요 |
| **FAILED 시 streams.last_error DB 저장** | `set_last_error()` 호출 (manager, lease_scanner, gstreamer). streams.last_error 컬럼은 001_streams_jobs_mysql.sql에 이미 존재. | ✅ 충족 |
| **구조화 로그: channel_id, worker_id, event_type, command_id, restart_count** | command_id 없음 | ❌ 갭 — command_id 추가 |
| **docker-compose metrics 포트 노출** | 없음 | ❌ 갭 |

## 조치

1. orchestrator·worker-stream에 Prometheus `/metrics` HTTP 서버 추가 (prometheus_client, 포트 9090/9091).
2. 지표 4종 등록: streams_running (gauge), streams_failed_total (counter), streams_reassign_total (counter), worker_restarts_total (counter). Orchestrator는 DB 기반 갱신 + 재할당 시 counter inc, Worker는 재시작 시 counter inc.
3. `stream_log_extra`에 `command_id` 인자 추가 및 호출부 전달.
4. docker-compose에 orchestrator 9090, stream-worker 9091 포트 노출.
