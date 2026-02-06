"""
API Gateway용 Redis Rate Limit. START/STOP 요청 폭주·악의적 클라이언트 방어.
- Kafka·스트리밍 로직 침범 금지. API 미들웨어에서만 사용.
"""
import logging
import time
from typing import Optional

from app.infrastructure.redis.client import get_redis

logger = logging.getLogger(__name__)

KEY_PREFIX = "rl:"

# Lua: INCR 후 윈도우 첫 요청이면 EXPIRE 설정. 원자적이라 race condition 방지.
LUA_INCR_WITH_EXPIRE = """
local c = redis.call("incr", KEYS[1])
if c == 1 then
    redis.call("expire", KEYS[1], ARGV[1])
end
return c
"""


class RateLimitExceeded(Exception):
    """제한 초과 시 반환. 미들웨어에서 429 등으로 변환."""
    def __init__(self, scope: str, limit: int, window_sec: int, retry_after_sec: Optional[int] = None):
        self.scope = scope
        self.limit = limit
        self.window_sec = window_sec
        self.retry_after_sec = retry_after_sec
        super().__init__(f"rate limit exceeded: {scope} (limit={limit}/{window_sec}s)")


class RateLimiter:
    """
    토큰/IP 기준 rate limit. Redis 카운터 + Fixed window.
    초당/분당 제한값 설정 가능. 운영에서 limit·window 조정하기 쉬운 구조.
    """

    def __init__(
        self,
        limit_per_second: Optional[int] = None,
        limit_per_minute: Optional[int] = None,
        key_prefix: str = KEY_PREFIX,
    ) -> None:
        """
        limit_per_second: 초당 최대 요청 수 (None이면 검사 안 함).
        limit_per_minute: 분당 최대 요청 수 (None이면 검사 안 함).
        둘 다 설정 시 둘 다 통과해야 허용.
        """
        self._limit_sec = limit_per_second
        self._limit_min = limit_per_minute
        self._prefix = key_prefix

    def _key(self, scope_type: str, scope_id: str, window_sec: int, now: float) -> str:
        """고정 윈도우: window_sec 단위로 잘라서 같은 윈도우면 같은 키."""
        window_start = int(now / window_sec) * window_sec
        return f"{self._prefix}{scope_type}:{scope_id}:{window_sec}:{window_start}"

    async def check(
        self,
        scope_type: str,
        scope_id: str,
        *,
        limit_per_second: Optional[int] = None,
        limit_per_minute: Optional[int] = None,
    ) -> None:
        """
        제한 검사. 초과 시 RateLimitExceeded 발생.
        scope_type: "ip" | "token" 등. scope_id: IP 주소 또는 토큰 값.
        인자로 넘긴 limit이 우선, 없으면 생성자 값 사용.
        """
        now = time.time()
        limit_sec = limit_per_second if limit_per_second is not None else self._limit_sec
        limit_min = limit_per_minute if limit_per_minute is not None else self._limit_min
        redis = await get_redis()
        if not redis:
            return
        if limit_sec is not None:
            await self._check_window(redis, scope_type, scope_id, 1, limit_sec, now)
        if limit_min is not None:
            await self._check_window(redis, scope_type, scope_id, 60, limit_min, now)

    async def _check_window(
        self,
        redis,
        scope_type: str,
        scope_id: str,
        window_sec: int,
        limit: int,
        now: float,
    ) -> None:
        key = self._key(scope_type, scope_id, window_sec, now)
        # EXPIRE는 window_sec + 1 정도로 해서 경계에서 키 유지
        expire = window_sec + 1
        count = await redis.eval(LUA_INCR_WITH_EXPIRE, 1, key, str(expire))
        if count > limit:
            raise RateLimitExceeded(
                scope=f"{scope_type}:{scope_id}",
                limit=limit,
                window_sec=window_sec,
                retry_after_sec=expire,
            )
