"""
Worker 선택 로직. 결정만 함. subprocess/실행 없음.
- 단일 워커 풀일 때는 환경 변수 WORKER_ID 또는 호스트명 사용.
- 여러 워커 시 라운드로빈/최소 부하 등은 확장 가능.
"""
import logging
import os

logger = logging.getLogger(__name__)


def assign_worker(channel_id: str, _candidates: list[str] | None = None) -> str:
    """
    channel_id에 할당할 worker_id 반환.
    현재는 단일 워커: WORKER_ID 환경 변수 또는 호스트명.
    _candidates: (미사용) 다중 워커 시 후보 목록.
    """
    worker_id = os.environ.get("WORKER_ID") or os.environ.get("HOSTNAME", "worker-1")
    logger.debug("assign_worker channel_id=%s -> worker_id=%s", channel_id, worker_id)
    return worker_id
