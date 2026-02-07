"""
Worker 선택 로직. 결정만 함. subprocess/실행 없음.
- Orchestrator가 실행되는 컨테이너가 아니라, 할당 대상 워커 ID를 반환해야 함.
- 단일 워커: 환경 변수 ASSIGNED_WORKER_ID(또는 WORKER_POOL)로 지정. 없으면 stream-worker-1.
- 여러 워커 시 WORKER_POOL=id1,id2 형태 + 라운드로빈 확장 가능.
"""
import logging
import os

logger = logging.getLogger(__name__)


def assign_worker(channel_id: str, _candidates: list[str] | None = None) -> str:
    """
    channel_id에 할당할 worker_id 반환.
    Orchestrator 쪽 env: ASSIGNED_WORKER_ID 또는 WORKER_POOL(쉼표 구분, 첫 번째 사용).
    stream-worker 컨테이너의 WORKER_ID와 일치해야 함.
    """
    # Orchestrator는 "누구에게 할당할지"만 지정. 본인(orch) 호스트명이 아님.
    pool = os.environ.get("ASSIGNED_WORKER_ID") or os.environ.get("WORKER_POOL", "stream-worker-1")
    worker_id = (pool.split(",")[0].strip() if pool else "stream-worker-1") or "stream-worker-1"
    logger.info("assign_worker channel_id=%s -> worker_id=%s (env ASSIGNED_WORKER_ID=%s)", channel_id, worker_id, os.environ.get("ASSIGNED_WORKER_ID", "(not set)"))
    return worker_id
