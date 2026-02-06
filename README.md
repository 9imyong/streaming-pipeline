# CCTV AI Streaming Platform

Event-Driven, Lease-based, Fault-Tolerant CCTV AI Streaming System

이 프로젝트는 CCTV 채널별 AI 기반 스트리밍을 비동기로 실행하는 플랫폼이다.  
API 요청은 즉시 처리하고, 장시간 실행되는 스트리밍 파이프라인은 이벤트 기반 구조로 분리하여
안정성, 확장성, 운영 편의성을 확보한다.

---

## 1. 주요 특징

- API 요청 즉시 응답 (비동기 스트리밍)
- 채널당 프로세스 1개 원칙 (ffmpeg / GStreamer)
- Lease 기반 중복 실행 방지
- 워커 장애 시 자동 takeover
- Kafka 기반 이벤트 처리
- AI 탐지 이벤트 Kafka 발행
- Kubernetes(KIND 포함) 환경 고려
- Celery 미사용 (상태ful 스트리밍에 부적합)

---

## 2. 전체 아키텍처 개요

Client  
→ API Gateway  
→ Kafka (stream.commands)  
→ Stream Orchestrator  
→ Stream Worker (ffmpeg / gstreamer)  
→ HLS / RTSP / MJPEG Output  

Optional:  
Stream Worker → Inference Worker → Kafka (ai.events)

---

## 3. 컴포넌트 역할

API Gateway  
- 스트리밍 시작/중지 요청 수신
- 요청 검증 및 즉시 응답

Kafka  
- 비동기 명령 및 이벤트 전달

Stream Orchestrator  
- 워커 할당
- Lease 기반 중복 실행 방지

Stream Worker  
- 채널별 스트리밍 subprocess 실행
- 재시작 및 heartbeat 관리

Inference Worker  
- AI 추론 수행
- AI 이벤트 Kafka 발행

Database (MySQL / PostgreSQL)  
- 스트림 상태 머신 관리
- Lease(소유권) 관리

---

## 4. 프로젝트 구조

```
streaming-platform/
├── app/
│   ├── api/                 # API Gateway
│   ├── core/                # 설정, 로깅, 관측
│   ├── domain/              # 스트리밍 도메인 규칙
│   ├── application/         # 유스케이스 계층
│   ├── infrastructure/      # Kafka, DB, ffmpeg 구현
│   ├── services/
│   │   ├── orchestrator/    # 워커 할당자
│   │   ├── worker_stream/   # 스트리밍 실행 워커
│   │   └── worker_infer/    # AI 추론 워커
│   └── tests/
│
├── docker/                  # 서비스별 Dockerfile
├── deployments/k8s/         # KIND / Kubernetes 배포 YAML
├── scripts/                 # 로컬/KIND 자동화 스크립트
└── README.md
```

---

## 5. 스트리밍 처리 흐름

1. Client가 POST /v1/streams 요청
2. API Gateway가 요청 검증 후 Kafka에 START command 발행
3. Stream Orchestrator가 채널 상태 확인 및 워커 할당
4. Stream Worker가 ffmpeg / gstreamer subprocess 실행
5. 스트리밍 출력(HLS/RTSP/MJPEG) 제공
6. Inference Worker가 AI 추론 후 ai.events 발행 (선택)

---

## 6. 상태 머신 및 Lease 모델

Stream 상태 값
- PENDING
- ASSIGNED
- RUNNING
- FAILED
- STOPPED

설계 원칙
- desired_state와 actual_state 분리
- Lease 만료 시 다른 워커가 takeover 가능
- START 요청은 멱등적 처리

---

## 7. Kafka 토픽 설계

stream.commands  
- START / STOP / RESTART

stream.events  
- STARTED / FAILED / HEARTBEAT

ai.events  
- AI 탐지 결과 이벤트

공통 규칙
- Partition key는 channel_id
- at-least-once 전제
- event_id / command_id 기반 중복 처리

---

## 8 로컬 개발 (KIND)

```
scripts/kind_create.sh
scripts/kind_load_images.sh
scripts/deploy_k8s.sh
```

---

## 9 Observability

- Logs: channel_id, worker_id 포함 구조화 로그
- Metrics: active_streams, restart_count, heartbeat
- Tracing: API → Orchestrator → Worker 흐름 추적

---

## 10 설계 철학

이 시스템은 웹 애플리케이션이 아니라 스트리밍 인프라다.

- 실행과 제어를 분리한다
- 상태를 명시적으로 관리한다
- 장애를 전제로 설계한다
- 확장은 워커 단위로 수행한다

---

## 11 향후 확장

- KEDA 기반 자동 스케일
- Helm Chart 제공
- 이벤트 데이터 ClickHouse / Elastic 적재
- 멀티 테넌시(site_id 단위 분리)

---

## License

Internal / Private Project
