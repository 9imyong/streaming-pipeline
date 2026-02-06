# 리팩토링 프로젝트 구조 (Kafka 기반, Celery 미사용)

## 1. 디렉터리 구조 제안

```
app/
├── __init__.py
├── main.py                    # 현재: legacy 로드. 이후 Gateway만 로드하거나 분리 진입점.
│
├── gateway/                   # [서비스 1] API Gateway (외부 진입점)
│   ├── __init__.py
│   ├── main.py                # FastAPI 앱, /v1/streams 라우트
│   ├── routes/
│   │   ├── streams.py         # POST/DELETE/GET /v1/streams, 202 Accepted
│   │   └── health.py
│   ├── deps.py                # DB/Kafka 클라이언트 주입
│   └── middleware/            # request_id, rate_limit, error_mapper
│
├── orchestrator/              # [서비스 2] Stream Orchestrator (Lease/할당)
│   ├── __init__.py
│   ├── main.py                # Kafka consumer loop (stream.commands)
│   ├── consumer.py            # stream.commands 소비, lease 획득, worker 지시
│   ├── lease.py               # lease 획득/갱신/만료 로직
│   └── publisher.py           # worker 전달 (Kafka 또는 direct)
│
├── stream_worker/             # [서비스 3] Stream Worker (채널당 subprocess 1개)
│   ├── __init__.py
│   ├── main.py                # 진입점: Kafka 소비 또는 Orchestrator 구독
│   ├── channel_manager.py    # 채널별 subprocess 생성/종료, heartbeat
│   ├── pipeline_runner.py    # ffmpeg/gst 실행 래퍼
│   └── events.py             # stream.events 발행 (STARTED/FAILED/HEARTBEAT)
│
├── inference_worker/          # [서비스 4] AI Inference Worker (선택)
│   ├── __init__.py
│   ├── main.py                # 프레임 소비, 추론, ai.events 발행 (snapshot_url만)
│   └── detector.py            # 스켈레톤
│
├── domain/                    # 공유 도메인 (모든 서비스에서 import)
│   ├── __init__.py
│   ├── stream_state_machine.py  # 상태 + 허용 전이 정의
│   ├── stream.py              # Stream 엔티티/값 객체
│   ├── events.py
│   └── errors.py
│
├── schemas/                   # Kafka 메시지 스키마 (JSON 직렬화)
│   ├── __init__.py
│   ├── stream_commands.py     # stream.commands 페이로드
│   ├── stream_events.py       # stream.events 페이로드
│   └── ai_events.py           # ai.events 페이로드 (snapshot_url만)
│
├── infrastructure/            # 공유 인프라
│   ├── kafka/
│   │   ├── __init__.py
│   │   ├── client.py          # Producer/Consumer 설정, partition key=channel_id
│   │   └── topics.py          # 토픽명 상수
│   ├── persistence/
│   │   ├── stream_repository.py   # streams 테이블 CRUD, lease 갱신
│   │   ├── job_repository.py      # jobs 테이블, idempotency_key
│   │   └── models.py              # SQLAlchemy 또는 raw SQL 모델
│   └── runners/
│       ├── ffmpeg.py          # ffmpeg subprocess 래퍼
│       └── gstreamer.py       # gst subprocess 래퍼
│
├── core/                      # 설정, 로깅 (기존 유지)
│   ├── config.py
│   └── logging.py
│
└── application/               # 유스케이스 (Gateway에서 호출)
    ├── start_stream.py        # Job 생성 + stream.commands 발행
    ├── stop_stream.py
    └── ports/
        ├── stream_repository.py
        └── event_bus.py
```

## 2. 배포 단위 (Kubernetes / KIND)

| 서비스 | 진입점 | 비고 |
|--------|--------|------|
| Gateway | `uvicorn app.gateway.main:app` | Deployment, Ingress |
| Orchestrator | `python -m app.orchestrator.main` | Deployment, 단일 또는 소수 레플리카 (lease 조정자) |
| Stream Worker | `python -m app.stream_worker.main` | Deployment, HPA, 여러 레플리카 (채널 분산) |
| Inference Worker | `python -m app.inference_worker.main` | Deployment, GPU 노드 (선택) |

## 3. Control DB 테이블 (요약)

- **streams**: channel_id (PK), desired_state, status, worker_id, lease_expires_at, pipeline_params (JSON), last_error, updated_at
- **jobs**: job_id (PK), channel_id, command, idempotency_key (UNIQUE), status, created_at

Partition key: Kafka 메시지/키는 `channel_id` 사용하여 동일 채널이 같은 파티션으로.

## 4. 폴더 구조 적용 현황

위 1번 구조대로 디렉터리/파일이 생성되어 있음. (기존 `api/`, `worker/`는 레거시 호환용으로 유지 가능.)

## 5. 구현된 스켈레톤 위치

| 항목 | 경로 |
|------|------|
| 상태 머신 | `app/domain/stream_state_machine.py` |
| Kafka 스키마 | `app/schemas/stream_commands.py`, `stream_events.py`, `ai_events.py` |
| JSON 예시 | `app/schemas/kafka_message_examples.json` |
| Stream Worker | `app/stream_worker/channel_manager.py`, `pipeline_runner.py`, `main.py` |
| Gateway | `app/gateway/main.py`, `routes/streams.py` |
| Orchestrator | `app/orchestrator/main.py`, `lease.py` |
| 멱등/lease/backoff 주석 | Gateway streams.py, channel_manager.py, orchestrator/main.py, lease.py |
