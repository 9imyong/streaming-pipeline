"""
START/STOP command 핸들러. 결정만 하고 실행은 하지 않음.
- lease 획득/해제, streams.assigned_worker_id 갱신.
- ffmpeg/gstreamer/subprocess 호출 금지.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from app.application.ports.lease_store import LeaseStore
from app.application.ports.stream_repository import StreamRepository
from app.domain.stream_state_machine import StreamState, DesiredState, validate_transition

logger = logging.getLogger(__name__)

LEASE_TTL_SECONDS = 30


async def handle_start(
    stream_repo: StreamRepository,
    lease_store: LeaseStore,
    assign_worker_fn: Callable[[str], str],
    payload: dict[str, Any],
) -> None:
    """
    START 명령: 워커 선택 → lease 획득 → DB에 assigned_worker_id 반영.
    실제 프로세스 기동은 Worker가 stream.commands 수신 후 자기에게 할당된 것만 실행.
    """
    channel_id = payload.get("channel_id") or ""
    if not channel_id:
        logger.warning("handle_start missing channel_id")
        return

    row = await stream_repo.get(channel_id)
    if not row:
        logger.warning("handle_start stream not found channel_id=%s", channel_id)
        return

    desired = (row.get("desired_state") or "").lower()
    if desired == DesiredState.STOPPED.value:
        # 이미 중지 요청됨. 할당하지 않음
        logger.info("handle_start skip desired=stopped channel_id=%s", channel_id)
        return

    current = row.get("status") or StreamState.PENDING.value
    try:
        validate_transition(StreamState(current), StreamState.ASSIGNED)
    except Exception:
        logger.debug("handle_start transition not allowed channel_id=%s status=%s", channel_id, current)
        return

    worker_id = assign_worker_fn(channel_id)
    acquired = await lease_store.acquire(channel_id, worker_id, LEASE_TTL_SECONDS)
    if not acquired:
        logger.info("handle_start lease not acquired channel_id=%s (another worker or still held)", channel_id)
        return

    # lease_store.acquire (DbLeaseStore)가 이미 assigned_worker_id, lease_expires_at, status=assigned 설정
    ok = await stream_repo.transition_status(channel_id, StreamState.PENDING.value, StreamState.ASSIGNED.value)
    if not ok:
        expires = datetime.now(timezone.utc) + timedelta(seconds=LEASE_TTL_SECONDS)
        await stream_repo.set_assigned_worker(channel_id, worker_id, expires)
    logger.info("handle_start assigned channel_id=%s worker_id=%s", channel_id, worker_id)


async def handle_stop(
    stream_repo: StreamRepository,
    lease_store: LeaseStore,
    payload: dict[str, Any],
) -> None:
    """
    STOP 명령: lease 해제 → 상태 stopped 반영. Worker는 lease 상실 시 자체 종료.
    """
    channel_id = payload.get("channel_id") or ""
    if not channel_id:
        logger.warning("handle_stop missing channel_id")
        return

    row = await stream_repo.get(channel_id)
    if not row:
        logger.debug("handle_stop no stream row channel_id=%s", channel_id)
        return
    worker_id = row.get("assigned_worker_id")
    if worker_id:
        await lease_store.release(channel_id, worker_id)
        logger.info("handle_stop released lease channel_id=%s worker_id=%s", channel_id, worker_id)

    current = (row or {}).get("status") or StreamState.PENDING.value
    await stream_repo.transition_status(channel_id, current, StreamState.STOPPED.value)
