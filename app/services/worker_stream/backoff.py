"""
재시작 정책. exponential backoff + jitter, 최대 재시작 횟수로 무한 재시작 방지.
"""
import random

# 무한 재시작 방지: 이 횟수 초과 시 FAILED 처리 후 중단
MAX_RESTARTS = 10

# 초 단위. delay = min(cap, base * 2^attempt) * jitter
BASE_DELAY = 1.0
CAP_DELAY = 60.0


def next_delay(restart_count: int, base: float = BASE_DELAY, cap: float = CAP_DELAY) -> float:
    """다음 재시작까지 대기 시간(초). jitter 0.5~1.5 적용."""
    if restart_count <= 0:
        return 0.0
    exp = min(cap, base * (2 ** min(restart_count, 10)))
    return exp * (0.5 + random.random())


def should_stop_restarting(restart_count: int, max_restarts: int = MAX_RESTARTS) -> bool:
    """재시작 중단 여부. True면 더 이상 재시작하지 않고 FAILED 처리."""
    return restart_count >= max_restarts
