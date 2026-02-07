# Stream Worker: StubStreamRunner 제거 → GStreamerStreamRunner 교체

## 1. 변경 파일 목록

| 파일 | 변경 내용 |
|------|-----------|
| `app/infrastructure/runners/gstreamer.py` | Python Gst 파이프라인 구현. videotestsrc→x264enc→fakesink(기본)/hlssink2(옵션). bus ERROR/EOS/STATE_CHANGED → stream.events STARTED/FAILED/STOPPED. Process-like handle 반환, graceful shutdown |
| `app/services/worker_stream/runner.py` | StubStreamRunner(sleep) 제거. StreamRunner 인터페이스만 유지 |
| `app/services/worker_stream/manager.py` | 러너가 lifecycle 이벤트 발행 시 중복 방지 (`publishes_lifecycle_events`). terminate/kill 호출 시 ProcessLookupError·AttributeError 처리 |
| `app/services/worker_stream/main.py` | GstreamerStreamRunner(worker_id, event_bus, loop) 주입 |
| `pyproject.toml` | PyGObject 의존성 추가 (Python Gst 바인딩) |
| `docker/worker-stream.Dockerfile` | GStreamer 런타임 + Python Gst용 gir 패키지 추가 (gir1.2-gstreamer-1.0, gir1.2-gst-plugins-base-1.0, libgirepository1.0-1, libcairo2) |
| `scripts/smoke_test.sh` | curl 실패 시 안내 메시지, 완료 시 worker stream.events 로그 확인 안내 |

---

## 2. 커밋 메시지 4개 제안

**Commit 1** (infra runner)
```
feat(worker-stream): add GStreamerStreamRunner with Python Gst pipeline

- Python Gst로 파이프라인 구성/제어, 프레임 미추출
- MVP: videotestsrc -> x264enc -> fakesink (옵션 hlssink2)
- bus ERROR/EOS/STATE_CHANGED 감지
  - PLAYING -> STARTED, ERROR -> FAILED(last_error), EOS/종료 -> STOPPED
- channel_id당 파이프라인 1개, stop 시 set_state(NULL) graceful shutdown
- Process-like handle (terminate, wait, returncode, publishes_lifecycle_events)
```

**Commit 2** (Stub 제거 + 인터페이스)
```
refactor(worker-stream): remove StubStreamRunner, keep StreamRunner interface

- StubStreamRunner(sleep) 제거
- 구현은 infrastructure/runners/gstreamer.GstreamerStreamRunner 사용
```

**Commit 3** (Manager + Main 연동)
```
feat(worker-stream): wire GstreamerStreamRunner, avoid duplicate lifecycle events

- main: GstreamerStreamRunner(worker_id, event_bus, loop) 주입
- manager: runner가 STARTED/STOPPED/FAILED 발행 시 중복 발행 스킵
- terminate/kill 호출 시 AttributeError/ProcessLookupError 방지
```

**Commit 4** (의존성 + Docker + 스모크)
```
chore(worker-stream): PyGObject, GStreamer runtime in Docker, smoke hint

- pyproject.toml: PyGObject 의존성 추가
- worker-stream.Dockerfile: GStreamer + gir 패키지 (Python Gst 바인딩)
- scripts/smoke_test.sh: curl 실패 메시지, worker stream.events 로그 안내
```

---

## 3. Smoke 테스트 (curl + 로그)

### 전제
- `docker compose -f docker/docker-compose.yml up -d mysql kafka api orchestrator` (필요 시 worker-stream도 up)
- DB 초기화: `docker exec -i streaming-mysql mysql -uroot -pdevpass streaming_pipeline_dev < app/infrastructure/persistence/migrations/001_streams_jobs_mysql.sql`

### curl

```bash
# START
curl -s -w "\n%{http_code}" -X POST http://localhost:8000/v1/streams/ \
  -H "Content-Type: application/json" \
  -d '{"channel_id":"ch1","source_rtsp":"rtsp://example/stream"}'
```

**기대**: JSON 본문에 `job_id` 포함, 마지막 줄 `202`

```bash
# STOP
curl -s -o /dev/null -w "%{http_code}\n" -X DELETE http://localhost:8000/v1/streams/ch1
```

**기대**: `202`

**또는 한 번에**
```bash
make smoke
```

### 기대 로그 출력

**Worker (stream.events 발행)**
- START 후:
  - `channel_id=ch1 starting Gst pipeline (no frame pull)`
  - Kafka `stream.events` 토픽에 `event=STARTED` 메시지 (key=ch1)
- STOP 후:
  - 파이프라인 종료 시 `stream.events`에 `event=STOPPED` (message=eos 또는 reason=command_stop)
- 에러 시:
  - `stream.events`에 `event=FAILED`, `last_error` 포함

**API**
- `command_bus.publish` 또는 KafkaCommandBus 로그로 `stream.commands` 발행 확인

**스모크 성공 시 터미널 출력 예**
```
Smoke test: http://localhost:8000 (channel=ch1)
OK: START 202
OK: STOP 202
smoke_test done. Check logs: api 'command_bus.publish'; orchestrator 'handle_start'/'handle_stop'; worker stream.events STARTED/STOPPED
```
