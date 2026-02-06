"""Clock/now 추상화. 테스트에서 시간 주입용."""
from datetime import datetime, timezone
from typing import Callable

# 테스트 시 override 가능
_get_now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)


def now() -> datetime:
    return _get_now()


def set_clock(fn: Callable[[], datetime]) -> None:
    global _get_now
    _get_now = fn
