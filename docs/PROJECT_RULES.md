# Project Rules (CCTV AI 스트리밍 인프라)

## 0. 최상위 원칙 (절대 규칙)

- 이 프로젝트는 CCTV AI 스트리밍 인프라다
- 장시간 실행되는 stateful 시스템이다
- channel_id가 모든 흐름의 기준 키다
- 이벤트 기반(Kafka) 아키텍처다
- Cursor는 구조를 "개선"할 수는 있지만 "재설계"하면 안 된다

---

## 1. 폴더별 역할 규칙 (침범 금지)

| 폴더 | 역할 | 금지 |
|------|------|------|
| **app/gateway** | HTTP 요청/응답만. FastAPI 라우팅, validation, auth, rate-limit | Kafka/DB 직접 접근, ffmpeg/gstreamer 실행, 장시간 로직 |
| **app/application** | 유스케이스 orchestration, 포트(interface) 정의 | Kafka, Redis, DB, subprocess 직접 사용 |
| **app/domain** | 상태 머신, 비즈니스 규칙의 단일 진실 | 외부 라이브러리 의존, 시간/환경 의존 로직 |
| **app/services/orchestrator** | Kafka stream.commands 소비, 워커 할당, lease 관리, 상태 전이 트리거 | 스트리밍 실행, AI 추론 |
| **app/services/worker_stream** | channel_id당 파이프라인 1개 실행, GStreamer/ffmpeg 제어, heartbeat 발행 | DB 상태 결정, 다른 채널 제어 |
| **app/services/worker_infer** | 프레임 소비, AI 추론, ai.events 발행 | 스트리밍 파이프라인 제어 |
| **app/infrastructure** | Kafka/DB/Redis/GStreamer/OS 연동. application이 정의한 interface만 구현 | application/domain 구조 변경, services로의 import |

---

## 2. 파일 수정 규칙 (Cursor 행동 제한)

- domain/* 변경 시 반드시 application/usecase 영향 검토
- infrastructure/* 변경 시 domain/application 변경 금지
- 서비스 간 import 금지 (worker_stream → orchestrator 등). **infrastructure → services import 금지**
- 새 파일 생성 시 반드시 적절한 폴더에 배치

---

## 3. Git 커밋 컨벤션 (필수)

### 포맷

```
<type>(<scope>): <subject>

[optional body]
```

### type 목록 (고정)

| type | 의미 |
|------|------|
| feat | 새로운 기능 |
| fix | 버그 수정 |
| refactor | 동작 변경 없는 구조 개선 |
| perf | 성능 개선 |
| docs | 문서 변경 |
| test | 테스트 추가/수정 |
| chore | 빌드/설정/의존성 |
| infra | Docker, Kafka, DB, Compose |

### scope 규칙 (디렉터리 대응)

| scope | 대응 디렉터리 |
|-------|----------------|
| api | app/gateway (HTTP 진입점) |
| domain | app/domain |
| orchestrator | app/services/orchestrator |
| worker-stream | app/services/worker_stream |
| worker-infer | app/services/worker_infer |
| infrastructure | app/infrastructure |
| docker | docker/ |
| docs | docs/ |

### 커밋 메시지 예시

```
feat(api): publish START/STOP commands to Kafka

refactor(worker-stream): replace stub runner with gstreamer pipeline

fix(orchestrator): prevent duplicate START on expired lease

infra(docker): split build/runtime stages and remove gstreamer from infer image

docs(architecture): add stream lifecycle and lease flow
```

---

## 4. Cursor용 커밋 규칙 (중요)

- 하나의 작업 = 하나의 커밋
- 커밋은 항상 빌드 가능한 상태여야 한다
- Stub 제거는 반드시 커밋 메시지에 명시한다  
  예: `refactor(worker-stream): remove StubStreamRunner`
- 대규모 변경은 커밋 여러 개로 쪼갠다

---

## 5. Cursor 출력 요구사항 (강제)

각 작업 완료 시 반드시 아래를 출력할 것:

1. 변경된 파일 목록
2. 커밋 메시지 제안
3. 간단한 스모크 테스트 방법

---

## 6. 절대 금지 패턴 (즉시 중단 대상)

- "이게 더 좋아 보입니다"라며 구조 변경
- domain에서 Kafka/DB import
- worker에서 다른 channel 제어
- 비동기 시스템을 동기 처리로 변경
- infrastructure에서 services import
