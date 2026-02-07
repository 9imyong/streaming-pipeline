# 개발·배포 워크플로우

개발 단계 → 이미지·컨테이너 → 서비스(KIND) 순으로 진행한다.

---

## 1단계: 이미지 세팅 전 — uv 로컬 개발

- **도구**: [uv](https://github.com/astral-sh/uv) (Python 패키지·가상환경 관리)
- **용도**: 코드 수정·실행·테스트. 이미지 빌드 없이 빠른 피드백.

### uv 설치

```bash
# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 프로젝트 셋업 및 실행

```bash
# 가상환경 생성 + 의존성 설치 (pyproject.toml 기준)
uv sync

# API 로컬 실행 (Kafka/Redis/DB는 로컬 또는 Docker만 띄우고)
uv run uvicorn app.gateway.main:app --reload --port 8000

# Orchestrator
uv run python -m app.services.orchestrator.main

# Stream Worker
uv run python -m app.services.worker_stream.main

# Inference Worker (mock)
uv run python -m app.services.worker_infer.main
```

### 테스트·린트

```bash
uv run pytest
uv run ruff check app/
```

### Smoke 검증 (HLS / RTSP 분리)

- **HLS**: videotestsrc → hlssink2 로 세그먼트·플레이리스트 생성 여부 확인.
- **RTSP**: rtspsrc → fakesink 로 SDP 수신·연결 여부 확인.

**로컬 (uv)**

```bash
# HLS smoke (기본 5초, /tmp/smoke_hls 에 index.m3u8 생성 확인)
uv run python -m app.smoke hls [--out-dir /tmp/smoke_hls] [--run-sec 5]

# RTSP smoke (URL 필수, 기본 5초·latency 300ms·timeout 15초)
uv run python -m app.smoke rtsp --url rtsp://host/path [--run-sec 5] [--latency-ms 300] [--timeout-ms 15000]
```

**Docker (stream-worker 이미지)**

```bash
# 프로젝트 루트에서
cd docker
./run-smoke.sh hls
./run-smoke.sh rtsp --url rtsp://host/path

# 또는 docker compose 직접
docker compose run --rm stream-worker python3 -m app.smoke hls
docker compose run --rm stream-worker python3 -m app.smoke rtsp --url rtsp://210.99.70.120:1935/live/cctv001.stream
```

- `run-smoke.sh` 는 stream-worker 이미지(GStreamer 포함) 안에서 smoke 실행. 이미지가 없으면 `docker compose build stream-worker` 후 실행.

---

## 2단계: 이미지 완료 후 — docker-compose + 코드 마운트

- **용도**: 이미지로 서비스 실행하되, **코드만 마운트**해서 수정 시 재빌드 없이 반영.
- **전제**: `docker compose build` 로 이미지 한 번 빌드된 상태.

### 스트리밍 스택 실행 (코드 마운트)

```bash
# 프로젝트 루트에서
docker compose -f docker/docker-compose.streaming.yml -f docker/docker-compose.streaming.dev.yml up -d

# API만
docker compose -f docker/docker-compose.streaming.yml -f docker/docker-compose.streaming.dev.yml up -d api kafka redis
```

- `docker-compose.streaming.dev.yml`: `app/` 을 컨테이너에 마운트.
- 코드 변경 후 해당 서비스만 재시작하면 적용 (필요 시 `docker compose restart api` 등).

### 이미지만 쓰고 마운트 없이 실행

```bash
docker compose -f docker/docker-compose.streaming.yml up -d
```

---

## 3단계: 서비스 단계 — KIND

- **용도**: Kubernetes 로컬 검증. 최종 배포와 동일한 방식으로 테스트.

### 순서

1. **KIND 클러스터 생성**
   ```bash
   ./scripts/kind_create.sh
   ```

2. **이미지 빌드 후 KIND에 로드**
   ```bash
   docker compose -f docker/docker-compose.streaming.yml build
   ./scripts/kind_load_images.sh
   ```

3. **K8s 매니페스트 적용**
   ```bash
   ./scripts/deploy_k8s.sh
   ```

4. **확인**
   ```bash
   kubectl get pods -n streaming-platform
   kubectl get svc -n streaming-platform
   ```

---

## 추론(Inference) 단계: Mock

- **현재**: 실제 모델 없이 **mock** 사용.
- **위치**: `app/services/worker_infer/pipeline.py` — `load_model()` / `detect()` 스텁.
- **환경 변수**: `INFERENCE_MOCK=1`(기본). `0`/`false`로 바꾸면 실제 모델 로드 경로로 전환 가능.
- 실제 모델 전환 시 같은 인터페이스로 `pipeline.py` 만 교체하면 됨.

---

## 요약

| 단계           | 도구              | 코드 반영 방식              | 추론        |
|----------------|-------------------|-----------------------------|------------|
| 이미지 세팅 전 | uv                | 로컬 실행                   | mock       |
| 이미지 완료 후 | docker-compose    | 볼륨 마운트로 변경 즉시 적용 | mock       |
| 서비스 단계    | KIND + kubectl    | 이미지 기반 배포            | mock → 교체 |
