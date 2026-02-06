# Runbook

## 로컬 개발
```bash
make dev-up    # 또는 scripts/dev_up.sh
# API: http://localhost:1223 (또는 docker-compose 포트)
make dev-down  # scripts/dev_down.sh
```

## 헬스 체크
- Liveness: `GET /health/live`
- Readiness: `GET /health/ready` (DB/Redis 연결 확인 시)

## 로그/메트릭
- 구조화 로그: `event`, `job_id`, `request_id`, `duration_ms` 등 (CODING_CONVENTIONS_9IMYONG)
- Prometheus/Grafana: docker-compose 또는 deployments/k8s

## 장애 대응
1. Celery 워커 미동작: `docker compose logs celery_worker_1`, Redis 연결 확인
2. HLS 404: `/data/playlist/streaming/{video_id}/` 경로 및 볼륨 마운트 확인
3. GPU OOM: 워커 동시성 조정, 모델 배치 크기 확인

## 롤백
- docker: `docker compose -f docker/docker-compose.prod.yml down && 이전 이미지로 up`
- k8s: `kubectl rollout undo deployment/api` 등
