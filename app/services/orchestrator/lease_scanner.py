"""
Lease 만료 스캐너. 주기적으로 만료된 lease 조회 → FAILED 전이 후 START 재발행.
- 재시도 쿨다운·횟수 제한으로 무한 재할당 방지.
"""
import asyncio
import logging
import time
import uuid
from typing import Any

from app.application.ports.lease_store import LeaseStore
from app.application.ports.stream_repository import StreamRepository
from app.domain.stream_state_machine import DesiredState, StreamState, validate_transition
from app.infrastructure.messaging.kafka.schemas import command_payload
from app.infrastructure.messaging.kafka.topics import STREAM_COMMANDS
from app.infrastructure.logging.stream_extra import stream_log_extra
from app.infrastructure.observability.stream_metrics import (
    streams_failed_total_counter,
    streams_reassign_total_counter,
)

logger = logging.getLogger(__name__)

SCAN_INTERVAL_SECONDS = 10
REASSIGN_COOLDOWN_SECONDS = 30
MAX_RESTART_COUNT_FOR_REASSIGN = 10


def _short_id() -> str:
    return str(time.time_ns())[-10:] + "-" + str(uuid.uuid4())[:8]


async def _release_only(
    stream_repo: StreamRepository,
    lease_store: LeaseStore,
    channel_id: str,
    row: dict[str, Any],
) -> None:
    """desired != RUNNING 인 만료 채널: lease만 해제하고 FAILED 전이."""
    worker_id = row.get("assigned_worker_id")
    if worker_id:
        await lease_store.release(channel_id, worker_id)
    current = (row.get("status") or StreamState.PENDING.value).lower()
    try:
        validate_transition(StreamState(current), StreamState.FAILED)
        await stream_repo.transition_status(channel_id, current, StreamState.FAILED.value)
    except Exception:
        pass


async def run_lease_expiry_scanner(
    stream_repo: StreamRepository,
    lease_store: LeaseStore,
    producer: Any,
) -> None:
    """
    백그라운드 루프: list_expired() → 만료 채널에 대해 lease 해제, FAILED 전이, START 재발행.
    producer.send(STREAM_COMMANDS, channel_id, payload)로 START 발행.
    """
    last_reassign: dict[str, float] = {}

    while True:
        try:
            await asyncio.sleep(SCAN_INTERVAL_SECONDS)
            expired = await lease_store.list_expired()
            if not expired:
                continue
            now = time.monotonic()
            for channel_id in expired:
                row = await stream_repo.get(channel_id)
                if not row:
                    continue
                desired = (row.get("desired_state") or "").lower()
                if desired != DesiredState.RUNNING.value:
                    await _release_only(stream_repo, lease_store, channel_id, row)
                    continue
                if last_reassign.get(channel_id, 0) + REASSIGN_COOLDOWN_SECONDS > now:
                    logger.debug("reassign cooldown channel_id=%s", channel_id)
                    continue
                restart_count = int(row.get("restart_count") or 0)
                if restart_count >= MAX_RESTART_COUNT_FOR_REASSIGN:
                    await stream_repo.set_last_error(
                        channel_id,
                        "lease_expired_max_reassign_exceeded",
                    )
                    await _release_only(stream_repo, lease_store, channel_id, row)
                    logger.warning(
                        "reassign skipped max restart channel_id=%s restart_count=%s",
                        channel_id,
                        restart_count,
                    )
                    continue
                current = (row.get("status") or StreamState.PENDING.value).lower()
                try:
                    validate_transition(StreamState(current), StreamState.FAILED)
                except Exception:
                    logger.debug("transition to FAILED not allowed channel_id=%s status=%s", channel_id, current)
                    continue
                worker_id = row.get("assigned_worker_id")
                if worker_id:
                    await lease_store.release(channel_id, worker_id)
                await stream_repo.set_last_error(channel_id, "lease_expired")
                ok = await stream_repo.transition_status(channel_id, current, StreamState.FAILED.value)
                if not ok:
                    continue
                streams_failed_total_counter.inc()
                last_reassign[channel_id] = now
                job_id = f"reassign-{channel_id}-{_short_id()}"
                payload = command_payload(
                    "START",
                    channel_id,
                    job_id=job_id,
                    idempotency_key=job_id,
                    params=row.get("pipeline_params") or {},
                )
                await producer.send(STREAM_COMMANDS, channel_id, payload)
                streams_reassign_total_counter.inc()
                logger.info(
                    "lease expired reassign channel_id=%s restart_count=%s",
                    channel_id,
                    restart_count + 1,
                    extra=stream_log_extra(channel_id, event_type="lease_expired", restart_count=restart_count + 1),
                )
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            logger.exception("lease scanner iteration error")
