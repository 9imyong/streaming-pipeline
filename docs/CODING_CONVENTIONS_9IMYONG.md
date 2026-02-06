# Coding Conventions (9IMYONG) — AI Model Serving · Infra · SRE

## 목표
- 운영 안정성(재현 가능, 관측 가능, 장애 복구 가능)을 최우선으로 한다.
- 과한 추상화/DDD를 지양하고, "읽히는 코드 + 명확한 책임 분리"를 따른다.
- 테스트는 "스모크 + 핵심 경계 조건" 위주로, 배포/운영 리스크를 낮춘다.

---

## 1) 프로젝트 구조 원칙

### 1.1 레이어 분리 (권장)
- `api/` : HTTP 라우팅, 요청/응답 스키마, 미들웨어, DI(최소)
- `application/` : 유스케이스(흐름 제어), 트랜잭션 경계
- `domain/` : 상태머신/규칙/엔티티 (DB/IO 모름)
- `infra/` : DB, Kafka, Redis, 외부 SDK, 파일/스토리지
- `worker/` : 소비(consume) 루프, 배치/직렬화, GPU 리소스 제어
- `observability/` : logging/metrics/tracing, health

**규칙**
- `api`는 `infra`를 직접 호출하지 않는다. (가능하면 `application`만 호출)
- `domain`은 외부 의존성 금지 (logging도 최소, side-effect 금지)
- IO(Kafka/DB/HTTP)는 `infra`에서만 한다.

---

## 2) 네이밍 & 파일 규칙

### 2.1 네이밍
- 함수/변수: `snake_case`
- 클래스/타입: `PascalCase`
- 상수: `UPPER_SNAKE_CASE`
- bool 변수/함수: `is_`, `has_`, `can_`, `should_` 접두사

### 2.2 파일/모듈
- `*_service.py` 같은 범용 이름 금지 → 역할이 드러나게:
  - `job_repository.py`, `kafka_consumer.py`, `ocr_pipeline.py`
- "handler"는 이벤트/메시지 단위로 쪼갠다:
  - `handle_job_created.py`, `handle_ocr_requested.py`

---

## 3) 타입 힌트 & 데이터 모델

### 3.1 타입 힌트 필수 범위
- public 함수, 유스케이스, repo/port interface는 타입 힌트 필수
- `Any` 사용 시 이유를 주석으로 남긴다

### 3.2 DTO/스키마 규칙
- API 입출력은 Pydantic 모델 사용
- 내부 도메인은 dataclass(또는 간단한 클래스) 선호
- "외부에서 들어온 값"은 가능한 빨리 검증/정규화하고, 이후 레이어는 신뢰한다.

---

## 4) 에러 처리 규칙 (운영 관점)

### 4.1 에러 분류
- `ValidationError` : 입력 문제 (400)
- `ConflictError` : 멱등성/중복 (409)
- `NotFoundError` : 리소스 없음 (404)
- `ExternalError` : 외부 의존성 실패 (502/503)
- `InternalError` : 코드/상태 불일치 (500)

### 4.2 예외 처리 위치
- `domain`에서 예외 발생 가능하나, 메시지는 짧고 명확히
- `api`에서 HTTP로 매핑 (error_mapper)
- `worker`는 재시도/데드레터/알림 정책을 명확히

---

## 5) 로깅 컨벤션 (구조화 로그)

### 5.1 공통 필드 (필수)
- `event` : 고정된 이벤트 이름 (예: `job_created`, `ocr_started`)
- `request_id` / `trace_id` : 가능하면 포함
- `job_id` : 비동기 파이프라인이면 필수
- `duration_ms` : 처리시간 측정 가능한 곳은 반드시

**예시**
- `logger.info("job_created", job_id=..., input_uri=..., model=...)`
- `logger.error("ocr_failed", job_id=..., err=..., retry=...)`

### 5.2 로그 레벨
- **INFO**: 상태 전이, 주요 이벤트 1줄
- **WARNING**: 재시도, 성능 저하 징후
- **ERROR**: 실패(재현 가능 정보 포함)
- **DEBUG**: 로컬 개발에서만 (prod off)

---

## 6) 관측성(Observability) 규칙

### 6.1 Metrics 최소 세트
- **API**: 요청 수, 지연(ms), 상태코드
- **Worker**: 처리 성공/실패, 큐 lag, 배치 크기, 처리시간
- **GPU**: 사용률, 메모리, 동시성(세마포어), OOM 카운트

### 6.2 Health / Readiness
- **liveness**: 프로세스 살아있음
- **readiness**: Kafka/DB 연결 가능 + 필수 의존성 OK
- worker도 readiness 제공(consumer loop 준비 여부)

---

## 7) 비동기/메시징(Kafka) 컨벤션

### 7.1 토픽/메시지
- 토픽은 목적 기반 네이밍: `ocr.request`, `ocr.result`, `job.events`
- 스키마 버전 포함 권장: 메시지에 `schema_version`, `created_at`, `producer` 포함

### 7.2 멱등성(필수)
- `job_id` 기반 처리
- DB 상태 전이로 "이미 처리됨" 방지
- consumer는 at-least-once를 기본으로 가정하고 설계한다.

---

## 8) GPU/모델 파이프라인 컨벤션

### 8.1 초기화 위치
- 모델 로드는 요청마다 X
- 프로세스 시작 시(lifespan) 1회 로드
- 배치/직렬화 제어는 worker에만 둔다

### 8.2 동시성
- GPU 1장 기준 기본값: concurrency=1 (안정형)
- 확장형은 배치 or 다중 워커를 명시적으로 선택

---

## 9) 테스트 전략 (실무형)

**원칙**
- "배포 직전 신뢰 확보" 수준의 스모크 테스트 + 핵심 경계조건
- 외부 의존성은 가능한 컨테이너로 띄워 통합 테스트(선택)

**권장 테스트**
- Usecase 단위 테스트: 상태 전이/멱등성
- API 스모크: `/health`, `/metrics`, 대표 endpoint 1~2개
- Worker 스모크: 메시지 1건 처리 성공/실패 케이스

---

## 10) 코드 스타일 툴링 (권장 기본값)

- **Formatter**: `ruff format` (또는 black)
- **Lint**: `ruff`
- **Type check**: `mypy` (핵심 모듈부터 점진 적용)
- **Import sort**: ruff로 통합

(프로젝트가 커지면 pre-commit 적용)

---

## 11) Git 커밋 컨벤션

**형식**
- `feat`: 기능
- `fix`: 버그
- `docs`: 문서/README
- `refactor`: 리팩토링(동작 변화 없음)
- `perf`: 성능 개선
- `test`: 테스트
- `chore`: 빌드/CI/설정/패키지

**예시**
- `feat(worker): add batching for OCR requests`
- `fix(kafka): prevent localhost metadata in advertised listeners`
- `docs(readme): 프로필 README 개편 및 AI 모델 서빙·Infra·SRE 방향성 명확화`

---

## 12) PR 규칙 (리뷰 받기 쉽게)

**PR 본문 템플릿**
- 무엇을/왜 했는지 (문제-해결)
- 변경 범위(파일/모듈)
- 위험 요소(롤백/호환성)
- 테스트 방법(스모크 커맨드)
- 관측성(로그/메트릭 추가 여부)

---

## 부록) "지양하는 패턴"
- 범용 `service.py`, `utils.py`에 기능 무한 추가
- 레이어를 무시한 직접 호출(api → db)
- try/except로 에러 삼키기 (로그/메트릭 없이)
- 요청마다 모델 로드/파이프라인 생성
