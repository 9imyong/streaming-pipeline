"""
Redis 실시간 스트리밍 heartbeat 캐시. DB 부하 감소, 대시보드/운영 조회 최적화.
- 영속 저장·비즈니스 판단·상태 머신 대체 금지.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from app.infrastructure.redis.client import get_redis

logger = logging.getLogger(__name__)

KEY_PREFIX = "hb:stream:"
# TTL: heartbeat 미수신 시 10~20초 후 자동 삭제. 운영 조회 시 "살아있음" 판단에 사용.
DEFAULT_TTL_SECONDS = 15


def _key(channel_id: str) -> str:
    return f"{KEY_PREFIX}{channel_id}"


class HeartbeatCache:
    """
    채널별 heartbeat 상태 캐시. 키 hb:stream:{channel_id}, 값 JSON.
    worker_id, uptime, fps, last_ts 등. TTL 10~20초로 휘발성 유지.
    """

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds

    async def set(
        self,
        channel_id: str,
        worker_id: str,
        *,
        uptime_sec: Optional[float] = None,
        fps: Optional[float] = None,
        last_ts: Optional[float] = None,
        frame_count: Optional[int] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        heartbeat 갱신: SETEX 사용. 매 heartbeat마다 호출하면 TTL이 갱신되어
        "최근에 살아있음" 상태 유지. 영속 저장 없음.
        """
        redis = await get_redis()
        if not redis:
            return
        key = _key(channel_id)
        payload: Dict[str, Any] = {
            "worker_id": worker_id,
            "uptime_sec": uptime_sec,
            "fps": fps,
            "last_ts": last_ts,
            "frame_count": frame_count,
        }
        if extra:
            payload["extra"] = extra
        payload = {k: v for k, v in payload.items() if v is not None}
        value = json.dumps(payload, ensure_ascii=False)
        await redis.setex(key, self._ttl, value)
        logger.debug("heartbeat set channel_id=%s worker_id=%s", channel_id, worker_id)

    async def get(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        조회용: 단일 채널 heartbeat. 없거나 TTL 만료 시 None.
        대시보드/운영 조회에서 "실시간 상태" 표시용.
        """
        redis = await get_redis()
        if not redis:
            return None
        key = _key(channel_id)
        raw = await redis.get(key)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    async def get_many(self, channel_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        조회용: 여러 채널 한 번에. 키 없음/만료는 결과에 포함하지 않음.
        운영 조회·대시보드 리스트에 적합.
        """
        redis = await get_redis()
        if not redis:
            return {}
        if not channel_ids:
            return {}
        keys = [_key(cid) for cid in channel_ids]
        values = await redis.mget(keys)
        out: Dict[str, Dict[str, Any]] = {}
        for cid, raw in zip(channel_ids, values or []):
            if not raw:
                continue
            try:
                out[cid] = json.loads(raw)
            except json.JSONDecodeError:
                continue
        return out

    async def delete(self, channel_id: str) -> None:
        """
        워커 종료 시 캐시 정리. STOP/장애 시 호출해 더 이상 살아있지 않음을 반영.
        """
        redis = await get_redis()
        if not redis:
            return
        key = _key(channel_id)
        await redis.delete(key)
        logger.debug("heartbeat delete channel_id=%s", channel_id)

    async def delete_many(self, channel_ids: List[str]) -> None:
        """워커가 여러 채널을 한꺼번에 내려갈 때 일괄 정리."""
        redis = await get_redis()
        if not redis:
            return
        if not channel_ids:
            return
        keys = [_key(cid) for cid in channel_ids]
        await redis.delete(*keys)
