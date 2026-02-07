# Runbook — 장애 시 이렇게 대응합니다

한 페이지 요약: **장애 유형별 확인 순서 → 관측성 확인 → 수동 복구 커맨드.**

---

## 1. 장애 유형별 대응

| 장애 | 확인 순서 | 수동 복구 (필요 시) |
|------|-----------|----------------------|
| **Kafka 장애** | API/Orchestrator/Worker 로그에 connection/timeout → `GET /v1/observability` 응답 여부 | `docker compose restart kafka` 후 `restart api orchestrator stream-worker` |
| **Worker 다운** | 동일: lease 만료 후 Orchestrator가 자동 재할당(아래 타임라인). `GET /v1/observability` 에 `last_errors` 확인 | 재할당 안 되면 `docker compose restart stream-worker` 후 해당 채널 재시작 요청(`POST /v1/streams/`) |
| **DB 재시작** | API/Orchestrator 5xx 또는 "stream not found" → MySQL 로그 | `docker compose restart mysql` 후 DB healthy 되면 `api`·`orchestrator` 재시작 |

---

## 2. 재할당 로직 타임라인 (초 단위)

Worker가 죽으면 **Orchestrator가 자동으로 같은 채널을 다시 할당**한다.

| 시점 | 동작 |
|------|------|
| **0s** | Worker 프로세스 종료 → HEARTBEAT 중단 |
| **~30s** | Lease TTL(30s) 만료. DB에서 `lease_expires_at < NOW()` 로 만료 처리 |
| **~30–40s** | Orchestrator Lease 스캐너(10s 주기)가 만료 채널 조회 → `status=FAILED` 전이 → `stream.commands` 에 START 재발행 |
| **~40s~** | 다른(또는 재기동된) Worker가 START 수신 → lease 획득 → 파이프라인 기동 |

**제한:** 채널당 `restart_count` 가 10 이상이면 재할당 스킵(무한 재시도 방지). 재할당 후에도 같은 채널이 30s 쿨다운 내에 다시 만료되면 한 번만 재발행.

---

## 3. 관측성 확인 (장애 시 먼저 볼 것)

- **상태·재시작 수:** `GET /v1/observability`  
  - `counts`: `streams_running`, `streams_failed`, `restarts_total`  
  - `last_errors`: 채널별 마지막 에러 1줄(DB 캐시)
- **단일 채널:** `GET /v1/streams/{channel_id}` → `status`, `last_error`, `worker_id`
- **로그 검색:** 구조화 필드 `channel_id`, `worker_id`, `event_type`, `restart_count` 로 "어디서/왜/몇 번 재시작" 확인

---

## 4. 수동 복구 커맨드

```bash
# 스택 기동 (DB 초기화는 최초 1회)
docker compose -f docker/docker-compose.yml up -d mysql kafka api orchestrator stream-worker
# DB 스키마 없으면:
docker exec -i streaming-mysql mysql -uroot -pdevpass streaming_pipeline_dev < app/infrastructure/persistence/migrations/001_streams_jobs_mysql.sql

# 장애 후 서비스만 재시작
docker compose -f docker/docker-compose.yml restart api
docker compose -f docker/docker-compose.yml restart orchestrator
docker compose -f docker/docker-compose.yml restart stream-worker

# 로그 (원인 파악)
docker compose logs -f orchestrator   # lease 만료·재할당
docker compose logs -f stream-worker  # FAILED, restart_count
docker compose logs -f api             # 5xx, command 발행
```

---

## 5. 로컬 개발 / 헬스 / 롤백

- **로컬:** `make dev-up` (또는 `scripts/dev_up.sh`). API: `http://localhost:8000` (또는 compose 포트).
- **헬스:** Liveness `GET /health/live`, Readiness `GET /health/ready`.
- **롤백:** docker — 이전 이미지로 `up`; k8s — `kubectl rollout undo deployment/<name>`.
