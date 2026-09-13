# 프론트엔드 운영 가이드 (Streaming Pipeline Console)

운영용 대시보드(Next.js) 사용법과 장애 시 확인 순서를 정리한 문서입니다.

---

## 1. 화면별 사용법

### 1.1 Streams (스트림 목록)

- **경로**: `/streams`
- **역할**: 채널(스트림) 목록 조회, 상태별 필터, 행별 Start/Stop
- **상태**: CREATED, ASSIGNED, RUNNING, FAILED, STOPPED
- **권한**: VIEWER는 조회만, OPERATOR/ADMIN은 Start·Stop 가능
- **대량 데이터**: 100건 단위 표시, 1,000건 이상 시 경고 배너. 필터로 범위 축소 권장

### 1.2 Stream 상세 (`/streams/[channel_id]`)

- **Status**: Worker, Current job, Desired state, Last error
- **HLS Preview**: RUNNING 스트림의 실시간 미리보기 (hls.js)
- **FAILED 진단**: 상태가 FAILED일 때 전용 섹션
  - 마지막 상태 전이 이벤트
  - 실패 요약 (오류 메시지, 시각, Job/Worker)
  - 운영자 행동 가이드 (GPU/RTSP/Worker 등 패턴별 안내)
- **State Timeline**: STATE_CHANGED 이벤트 기반 상태 전이 타임라인
- **Command History**: COMMAND_SENT 이벤트로 “누가/언제/어떤 스트림” 명령 실행 이력
- **Recent events**: 해당 스트림 이벤트 목록 (SSE 실시간 + 폴링 폴백)

### 1.3 Jobs (잡 목록)

- **경로**: `/jobs`, 쿼리 `?stream_id=ch-01` 로 스트림별 필터
- **역할**: 스트림별·타입별 작업 이력, 상태(PENDING/PROCESSING/DONE/FAILED)
- **대량 데이터**: 500건 단위, 1,000건 이상 시 경고 배너

### 1.4 Workers (워커 목록)

- **경로**: `/workers`
- **역할**: 워커 상태(IDLE/BUSY/DOWN), GPU 사용량, 담당 스트림 수
- **장애 시**: DOWN 워커 확인 → Streams에서 해당 워커에 할당된 스트림 재할당 여부 확인

### 1.5 Events (이벤트 로그)

- **경로**: `/events`
- **역할**: 전역 이벤트 로그, Stream ID/Level/Type 필터
- **실시간**: SSE 연결 시 실시간 수신, 끊기면 폴링 폴백. 연결 상태 뱃지(CONNECTED/RECONNECTING/OFFLINE)
- **ERROR/WARN**: 토스트로 알림

### 1.6 Metrics (운영 요약)

- **경로**: `/metrics`
- **역할**: active_streams, jobs_rate, p95_latency, error_rate 등 요약 지표

### 1.7 Settings (설정)

- **경로**: `/settings`
- **권한**: ADMIN만 메뉴 노출·변경 가능 (OPERATOR/VIEWER는 메뉴 숨김)
- **설정 항목**: API Base URL, API Key(localStorage), Poll interval(ms), Role(Mock)
- **Role Mock**: VIEWER(조회만) / OPERATOR(Start·Stop) / ADMIN(Settings 변경) — 실제 Auth 연동 전 UI 제어용

---

## 2. 장애 발생 시 확인 순서

1. **Metrics**  
   - error_rate, failed_streams 수치 확인  
   - 지표 급증 시 Streams·Events로 원인 스트림/이벤트 좁히기

2. **Streams**  
   - FAILED/STOPPED 상태 스트림 확인  
   - 특정 스트림 선택 → **Stream 상세** 이동

3. **Stream 상세 (FAILED일 때)**  
   - **FAILED 진단** 섹션: 마지막 전이 이벤트, 실패 요약, 운영자 행동 가이드  
   - **State Timeline**: CREATED → ASSIGNED → RUNNING → FAILED 경로 확인  
   - **Command History**: 최근 Stop/Start 등 명령 이력  
   - **Related jobs**: 해당 스트림 Job 상세에서 error_code/error_message 확인

4. **Workers**  
   - DOWN 또는 과부하(BUSY 다수) 워커 확인  
   - GPU 메모리 부족 등 가이드와 연계

5. **Events**  
   - ERROR/WARN 레벨 필터로 실패 원인 이벤트 검색  
   - stream_id, job_id, worker_id로 실패 구간 추적

---

## 3. 자주 보는 화면 정리

| 목적                 | 화면           | 비고                    |
|----------------------|----------------|-------------------------|
| 전체 스트림 상태     | Streams        | 상태 필터, 100건 단위   |
| 한 스트림 원인 파악  | Stream 상세    | FAILED 진단·Timeline·Command History |
| 작업 이력            | Jobs           | stream_id 필터          |
| 워커 상태            | Workers        | DOWN/BUSY 확인         |
| 실시간 이벤트        | Events         | SSE 상태 뱃지 확인     |
| 요약 지표            | Metrics        | error_rate, failed_streams |

---

## 4. 기술 요약

- **인증**: API Key (Settings 저장, x-api-key 헤더)
- **실시간**: Events는 SSE 우선, 끊기면 폴링 폴백
- **폴링**: 탭 비활성 시 15초 간격, 활성 시 Settings Poll interval(기본 2초)
- **대량 데이터**: Streams/Jobs는 limit 기반, 1,000건 이상 시 경고 UI
