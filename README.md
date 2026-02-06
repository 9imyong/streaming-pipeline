CCTV AI Streaming Platform

Event-Driven, Lease-based, Fault-Tolerant CCTV AI Streaming System

이 프로젝트는 CCTV 채널별 AI 기반 스트리밍을 비동기로 실행하는 플랫폼이다.
API 요청을 즉시 처리하고, 장시간 실행되는 스트리밍 파이프라인은 이벤트 기반 비동기 구조로 분리하여 안정성·확장성·운영 편의성을 확보한다.

✨ 핵심 특징

비동기 스트리밍 제어

API는 즉시 응답 (202 Accepted)

스트리밍은 Kafka 기반 비동기 실행

채널당 프로세스 1개 원칙

ffmpeg / GStreamer subprocess로 채널 격리

Lease 기반 중복 실행 방지

동일 CCTV 채널의 중복 스트리밍 원천 차단

장시간 실행 워크로드 대응

워커 장애 시 자동 takeover

재시작(backoff) 및 무한 루프 방지

AI 이벤트 Kafka 발행

탐지 결과를 ai.events 토픽으로 전달

Kubernetes 친화적 구조

KIND / 실 클러스터 동일 구조 운영 가능

Celery 미사용

상태ful 스트리밍 워크로드에 부적합하여 배제

🏗 전체 아키텍처 개요
Client
  ↓
API Gateway
  ↓ (Kafka: stream.commands)
Stream Orchestrator
  ↓ (lease + assign)
Stream Worker (ffmpeg / gstreamer)
  ↓
HLS / RTSP / MJPEG Output

[Optional]
Stream Worker → Inference Worker → Kafka(ai.events)

컴포넌트 역할
컴포넌트	역할
API Gateway	스트리밍 시작/중지 요청 수신
Kafka	비동기 명령/이벤트 전달
Orchestrator	워커 할당 및 중복 실행 방지
Stream Worker	채널별 스트리밍 실행
Inference Worker	AI 추론 및 이벤트 발행
DB(MySQL/Postgres)	상태 머신 + lease 관리
📂 프로젝트 구조
streaming-platform/
├── app/
│   ├── api/                 # API Gateway
│   ├── core/                # 설정/로깅/관측
│   ├── domain/              # 스트리밍 도메인 규칙
│   ├── application/         # 유스케이스 계층
│   ├── infrastructure/      # Kafka / DB / ffmpeg 구현
│   ├── services/
│   │   ├── orchestrator/    # 워커 할당자
│   │   ├── worker_stream/   # 스트리밍 실행 워커
│   │   └── worker_infer/    # AI 추론 워커
│   └── tests/
│
├── docker/                  # 서비스별 Dockerfile
├── deployments/k8s/         # KIND / K8s 배포 YAML
├── scripts/                 # 로컬/KIND 자동화 스크립트
└── README.md

🔄 스트리밍 처리 흐름

Client

POST /v1/streams 요청

API Gateway

요청 검증

스트림 Job 생성

stream.commands 토픽에 START 발행

Stream Orchestrator

채널 상태 확인

Lease 획득

Stream Worker 할당

Stream Worker

ffmpeg / gstreamer subprocess 실행

HLS / RTSP / MJPEG 출력

Heartbeat 이벤트 발행

Inference Worker (선택)

프레임 샘플링

AI 추론

ai.events 발행

🔐 상태 머신 & Lease 모델
Stream 상태

PENDING

ASSIGNED

RUNNING

FAILED

STOPPED

핵심 원칙

desired_state와 actual_state 분리

Lease 만료 시 다른 워커가 takeover 가능

START 요청은 멱등적

📡 Kafka 토픽 설계
토픽	용도
stream.commands	START / STOP / RESTART
stream.events	STARTED / FAILED / HEARTBEAT
ai.events	AI 탐지 이벤트

공통 규칙

Partition Key: channel_id

at-least-once 전제

event_id / command_id 기반 중복 처리

🚫 Celery를 사용하지 않는 이유

스트리밍은 종료되지 않는 작업

채널은 상태ful 리소스

Celery는 단기·Stateless 작업에 최적화됨

👉 본 프로젝트에서는 Kafka + Lease 기반 이벤트 아키텍처를 채택

🚀 로컬 개발 (KIND)
# KIND 클러스터 생성
scripts/kind_create.sh

# 이미지 로드
scripts/kind_load_images.sh

# 배포
scripts/deploy_k8s.sh

📊 Observability

Logs: channel_id / worker_id 포함 구조화 로그

Metrics: active_streams, restart_count, heartbeat

Tracing: API → Orchestrator → Worker 흐름 추적

🧠 설계 철학

“웹 서버가 아니라 스트리밍 인프라다.”

실행과 제어를 분리한다

상태를 명시적으로 관리한다

장애를 전제로 설계한다

확장은 워커 단위로 한다

📌 향후 확장

KEDA 기반 자동 스케일

Helm Chart 제공

ClickHouse / Elastic 이벤트 적재

멀티 테넌시(site_id 단위 분리)

📄 License

Internal / Private Project