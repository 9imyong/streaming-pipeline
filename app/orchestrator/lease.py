"""
Lease 획득/갱신/만료 로직.
- 중복 실행 방지: 한 채널에 한 워커만 lease를 가짐.
- 조건부 업데이트: lease_expires_at < NOW() OR worker_id IS NULL 일 때만 UPDATE.
- 갱신: HEARTBEAT 수신 시 lease_expires_at = NOW() + lease_ttl.
- 만료: 주기적으로 lease_expires_at < NOW() 인 행을 status=LOST로 전이, 재할당 대상으로 만듦.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class LeaseInfo:
    worker_id: str
    channel_id: str
    lease_expires_at: datetime


def lease_ttl_seconds() -> int:
    """Heartbeat 주기보다 충분히 길게 (예: 3배)."""
    return 90


# ----- DB 계약 (인프라에서 구현) -----
# acquire_lease(channel_id, worker_id) -> bool
#   UPDATE streams SET worker_id=?, lease_expires_at=NOW()+? WHERE channel_id=? AND (lease_expires_at < NOW() OR worker_id IS NULL)
#   RETURN affected_rows == 1
# renew_lease(channel_id, worker_id) -> bool
#   UPDATE streams SET lease_expires_at=NOW()+? WHERE channel_id=? AND worker_id=?
# expire_leases() -> list[channel_id]
#   SELECT channel_id FROM streams WHERE lease_expires_at < NOW() AND status = 'running'
#   UPDATE streams SET status='lost' WHERE channel_id IN (...)
#   RETURN channel_ids  # 재할당용 START 재발행
