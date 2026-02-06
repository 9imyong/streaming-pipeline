# Architecture

---

## 목표 아키텍처 (한 줄)

**Gateway(API) → Job 생성(멱등) → Queue(Kafka) → Stream Orchestrator가 채널 할당(Lease) → Stream Worker가 채널별 파이프라인(ffmpeg/gst) 실행 → Output(HLS/RTSP/MJPEG) 제공 + 상태/로그/메트릭 수집**

---

## 목표: 컴포넌트 구성

### 1) API Gateway (외부 진입점)

**역할**: 인증 / 레이트리밋 / 요청 검증 / Job 생성 후 즉시 **202 Accepted** 반환

| 메서드 | 엔드포인트 | 설명 |
|--------|------------|------|
| POST | `/v1/streams` | 채널 스트림 시작 요청 |
| DELETE | `/v1/streams/{channel_id}` | 중지 |
| GET | `/v1/streams/{channel_id}` | 상태 조회 |
| GET | `/v1/streams/{channel_id}/manifest.m3u8` | HLS면 프록시/리다이렉트 |

### 2) Control DB (MySQL/Postgres)

**목적**: 상태 머신 + 멱등성 + 복구

**테이블 핵심**

- **streams**: `channel_id`, `desired_state`, `status`, `worker_id`, `lease_expires_at`, `pipeline_params`, `last_error`, `updated_at`
- **jobs**: `job_id`, `channel_id`, `command`, `idempotency_key`, `status`, `created_at`

### 3) Queue / Event Bus (Kafka 추천)

**이유**: 비동기 버퍼, 컨슈머 스케일, 재처리(오프셋)

| 토픽 | 용도 |
|------|------|
| `stream.commands` | START / STOP / RESTART / UPDATE |
| `stream.events` | STARTED / STOPPED / FAILED / HEARTBEAT |
| (선택) `stream.metrics` | 간단 이벤트성 메트릭 |

### 4) Stream Orchestrator (할당/조정 서비스)

**역할**: “이 채널을 어느 워커가 맡을지” 결정

- START 명령 수신 → DB에 `desired_state` 기록 → **Lease 획득(할당)** → 워커에게 실행 지시
- 워커 heartbeat 보고 **lease 갱신/만료** 처리
- 워커 죽으면 lease 만료 후 **다른 워커에게 재할당**
- 이 컴포넌트가 없으면 워커 수가 늘어날수록 **같은 채널을 여러 워커가 실행하는 중복** 발생

### 5) Stream Worker (실행기)

- **채널 단위 실행**: 채널당 subprocess 1개 (ffmpeg 또는 gst-launch/파이썬 GStreamer)
- **기능**
  - 할당된 채널에 대해 파이프라인 실행
  - 주기적으로 상태(프레임 수, 재연결 횟수, cpu/gpu, last_pts 등) **heartbeat** 보고
  - 프로세스 죽으면 정책에 따라 재시작(backoff) 후 이벤트 발행

### 6) AI Inference (선택)

| 방식 | 설명 |
|------|------|
| **Separate Inference Worker (추천)** | Stream Worker가 프레임(또는 샘플링)을 큐로 보내고, Inference Worker가 결과 반환 → Stream Worker가 overlay/메타데이터 삽입. 장애 격리·스케일 유리 |
| Inline | 한 프로세스에서 디코드+추론+인코드. 빠르지만 GPU 병목 시 스트림 함께 흔들림 |
| Sidecar | 같은 Pod 내 분리. K8s에서 절충안 |

### 7) Output Storage / Origin (HLS 기준)

- **(간단)** 워커 로컬 디스크 + Nginx로 서빙 (단일 노드)
- **(운영)** S3/MinIO/Object Storage 또는 NFS/PVC
- RTSP relay / MJPEG면 워커가 직접 port 서빙하거나 중계 서버

### 8) Observability

- **Logs**: 구조화 로그 + `request_id` / `channel_id` / `job_id` 필수
- **Metrics**: Prometheus (`streams_active`, `restart_total`, lag, `gpu_util` 등)
- **Tracing**: OTel (Gateway → Orchestrator → Worker)

---

## 목표: 전체 처리 흐름 (시퀀스)

1. **Client** → `POST /v1/streams` `{ channel_id, source_rtsp, ai_profile, output: "hls" }`
2. **Gateway**
   - `idempotency_key` 확인 (같은 요청 중복 방지)
   - DB에 **jobs** 생성 + **streams.desired_state = RUNNING**
   - Kafka **stream.commands**에 `START(channel_id, job_id, params)` 발행
   - 즉시 **202 Accepted** + `job_id` 반환
3. **Orchestrator** (컨슈머)
   - DB에서 stream row 조회
   - **Lease 획득** (예: `lease_expires_at` 갱신을 조건부 업데이트)
   - 워커 할당(`worker_id` 결정)
   - `stream.commands` 또는 direct RPC로 **RUN_PIPELINE(channel_id, params)** 전달
4. **Worker**
   - 채널 subprocess 실행 (ffmpeg/gst)
   - AI 필요 시 Inference Worker에 프레임 전달/결과 수신
   - HLS 세그먼트 생성·저장/서빙
   - **stream.events**에 STARTED/HEARTBEAT 발행 + DB status 갱신
5. **Client**는 `GET /v1/streams/{channel_id}` 로 상태 확인 후 HLS URL로 재생

---

## 현재 구조 (참고)

- **개요**: 영상 스트리밍 AI 파이프라인 서버. CCTV RTSP 수신 → GStreamer/HLS 변환 → AI 검출(Celery 워커).
- **레이어**: api/, application/, domain/, infrastructure/, worker/
- **흐름**: API → Redis 태스크 목록 + Celery 발행 → Worker에서 GStreamer 기동 → HLS `/data/playlist/streaming/{video_id}/` 서빙
- **진입점**: `app.main`에서 `legacy` 앱 로드, `/health` 추가

상세는 `docs/diagrams/`, `docs/CODING_CONVENTIONS_9IMYONG.md` 참고.
