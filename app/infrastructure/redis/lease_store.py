"""
Redis 기반 LeaseStore. CCTV 채널 중복 실행 방지, 워커 장애 시 TTL 만료로 자동 takeover.
- Kafka·DB 접근 금지. lease 로직만 담당.
"""
import logging
from typing import List

from app.application.ports.lease_store import LeaseStore
from app.infrastructure.redis.client import get_redis

logger = logging.getLogger(__name__)

KEY_PREFIX = "lease:stream:"


def _key(channel_id: str) -> str:
    """lease 키: 동일 채널은 항상 같은 키로 race condition 시 SET NX 일관성 보장."""
    return f"{KEY_PREFIX}{channel_id}"


# Lua: 갱신은 소유자(worker_id)일 때만 수행. 다른 워커가 선점했으면 0 반환.
LUA_RENEW = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("pexpire", KEYS[1], ARGV[2])
else
    return 0
end
"""

# Lua: 해제도 소유자일 때만. 다른 워커 lease는 건드리지 않음.
LUA_RELEASE = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""


class RedisLeaseStore(LeaseStore):
    """
    Redis Lease. 키 형식 lease:stream:{channel_id}, 값 worker_id.
    TTL 만료 시 키 삭제되어 다른 워커가 acquire 가능(takeover).
    """

    async def acquire(self, channel_id: str, worker_id: str, ttl_seconds: int) -> bool:
        """
        lease 획득: SET NX PX 사용. 키가 없을 때만 설정해 race condition 방지.
        이미 다른 워커가 소유 중이면 False. TTL 만료 후에는 새 워커가 획득 가능.
        """
        redis = await get_redis()
        if not redis:
            return False
        key = _key(channel_id)
        ttl_ms = ttl_seconds * 1000
        # NX = set if not exists. 성공 시 True 반환.
        ok = await redis.set(key, worker_id, nx=True, px=ttl_ms)
        if ok:
            logger.debug("lease acquired channel_id=%s worker_id=%s ttl=%ds", channel_id, worker_id, ttl_seconds)
        return bool(ok)

    async def renew(self, channel_id: str, worker_id: str, ttl_seconds: int) -> bool:
        """
        lease 갱신: 소유자(worker_id)일 때만 TTL 연장. Lua로 원자적 수행해
        갱신 직전 다른 워커가 선점하는 race 방지.
        """
        redis = await get_redis()
        if not redis:
            return False
        key = _key(channel_id)
        ttl_ms = ttl_seconds * 1000
        result = await redis.eval(LUA_RENEW, 1, key, worker_id, str(ttl_ms))
        return bool(result)

    async def release(self, channel_id: str, worker_id: str) -> bool:
        """
        lease 해제: 소유자일 때만 키 삭제. Lua로 원자 처리해
        잘못된 워커가 다른 워커의 lease를 지우지 않도록 함.
        """
        redis = await get_redis()
        if not redis:
            return False
        key = _key(channel_id)
        result = await redis.eval(LUA_RELEASE, 1, key, worker_id)
        return bool(result)

    async def list_expired(self) -> List[str]:
        """
        Redis에서는 TTL 만료 시 키가 자동 삭제되므로 "만료된 채널 목록"을
        별도 조회할 수 없음. 재할당은 acquire 시 키가 없으면 성공하므로
        START 재전송 또는 오케스트레이터 로직으로 처리. 여기서는 빈 목록 반환.
        """
        return []
