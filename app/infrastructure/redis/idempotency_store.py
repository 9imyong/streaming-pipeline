"""
API 멱등성 보조용 Redis 저장소. 동일 START 요청 중복 처리·burst 방어.
- 영속 멱등성은 DB가 최종 책임. Kafka·상태 머신 변경 금지.
"""
import hashlib
import logging
from typing import Optional, Tuple

from app.infrastructure.redis.client import get_redis

logger = logging.getLogger(__name__)

KEY_PREFIX = "idem:start:"
# TTL: 짧게 유지. 1~5분. burst 구간만 보호.
DEFAULT_TTL_SECONDS = 120


def make_idempotency_key(channel_id: str, client_key: str) -> str:
    """
    키 생성 헬퍼. idem:start:{channel_id}:{hash} 형식.
    client_key는 클라이언트가 준 멱등 키 또는 요청 식별자. hash로 길이 제한.
    """
    h = hashlib.sha256(client_key.encode()).hexdigest()[:16]
    return f"{KEY_PREFIX}{channel_id}:{h}"


class IdempotencyStore:
    """
    Idempotency key → job_id 캐시. SET NX EX로 첫 요청만 저장, 이미 있으면 기존 job_id 반환.
    API 레이어에서 "이미 처리된 요청인가?" 판단 후 유스케이스 호출 여부 결정에 사용.
    """

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds

    async def get_or_set(
        self,
        idempotency_key: str,
        job_id: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        SET NX EX 사용: 키가 없을 때만 job_id 저장. 이미 키가 있으면 기존 값(job_id) 반환.
        반환: (저장_성공 여부, job_id). 성공 시 (True, job_id), 이미 있으면 (False, 기존_job_id).
        API에서 (False, existing_id)면 202 + 기존 job_id 응답.
        """
        redis = await get_redis()
        if not redis:
            return True, job_id
        # 키가 이미 있으면 기존 job_id 조회 후 반환 (멱등: 동일 요청으로 처리된 job)
        existing = await redis.get(idempotency_key)
        if existing is not None:
            return False, existing
        ok = await redis.set(idempotency_key, job_id, nx=True, ex=self._ttl)
        if ok:
            return True, job_id
        # NX 실패(동시 요청): 다시 읽어서 기존 job_id 반환
        existing = await redis.get(idempotency_key)
        return False, existing or job_id

    async def get(self, idempotency_key: str) -> Optional[str]:
        """이미 처리된 요청인지 조회만. 값은 job_id."""
        redis = await get_redis()
        if not redis:
            return None
        return await redis.get(idempotency_key)
