# 레이어별 역할 + 넣는 것 + 금지사항

## 1) app/api/

**역할**: HTTP 요청/응답만 담당(얇게)

**넣는 것**: 라우터, 미들웨어, DI(deps)

**금지**: DB 쿼리 직접 작성, ffmpeg/gst 실행, Kafka 로직 직접 작성  
→ 그런 건 `application/usecases` 또는 `infrastructure`로 내려야 함

---

## 2) app/core/

**역할**: 공통 기반(설정/로그/관측/라이프사이클)

**넣는 것**: Settings(Pydantic), 로깅 초기화, Prometheus/OTel 설정, startup/shutdown

**금지**: 비즈니스 규칙(도메인 로직)

---

## 3) app/domain/

**역할**: "CCTV 스트림"의 규칙(상태 머신/전이/멱등성 기준)

**넣는 것**:
- Stream 엔티티
- 상태 머신(예: PENDING→ASSIGNED→RUNNING…)
- 도메인 이벤트/에러

**금지**: Kafka/MySQL/ffmpeg 같은 외부 의존

---

## 4) app/application/

**역할**: 유스케이스(업무 흐름) 계층

**넣는 것**:
- **ports/**: DB/Kafka/runner 같은 외부 의존을 추상화
- **usecases/**: 실제 흐름(멱등성 검사 → 상태 저장 → command 발행)

**금지**: Kafka 라이브러리/DB 드라이버 직접 호출(그건 infra)

---

## 5) app/infrastructure/

**역할**: 외부 시스템 구현체 모음(카프카, DB, 프로세스 실행, 스토리지)

**넣는 것**:
- Kafka producer/consumer 래퍼
- repository/lease 구현(DB lease 추천)
- ffmpeg/gst 커맨드 빌더, subprocess 래퍼
- HLS 저장/업로드

**금지**: 비즈니스 규칙(그건 domain/application)

---

## 6) app/services/

**실행 바이너리 단위**로 나눈 폴더.

### a) services/orchestrator/

**역할**: stream.commands 소비 → worker 할당 + lease → 실행 지시  
**핵심**: 중복 실행 방지(lease), 워커 선택(assigner)

**금지**: 실제 ffmpeg/gst 실행(그건 stream worker)

### b) services/worker_stream/

**역할**: 채널별 subprocess 관리(채널당 1 프로세스)  
**핵심 파일**: manager.py  
- active_processes 딕셔너리 관리  
- 재시작(backoff)  
- heartbeat 발행(stream.events)

**금지**: "할당 결정"(그건 orchestrator)

### c) services/worker_infer/

**역할**: inference 요청 처리 + ai.events 발행  
**핵심**: 모델 로드(lifespan), 배치/직렬화 최적화, snapshot_url 발행

**금지**: 스트리밍 파이프라인 유지(그건 stream worker)

---

## 7) deployments/, docker/, scripts/

| 경로 | 용도 |
|------|------|
| **deployments/k8s** | KIND/실클러스터 공용 YAML |
| **docker/** | 서비스별 Dockerfile 분리(멀티 스테이지 가능) |
| **scripts/** | kind 클러스터 만들기 / 이미지 로드 / 배포 자동화 |
