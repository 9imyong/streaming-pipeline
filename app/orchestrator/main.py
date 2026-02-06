"""
Orchestrator 진입점.
- stream.commands 토픽 소비 (START/STOP/RESTART).
- START 수신 시: DB desired_state 반영 → Lease 획득 → 해당 워커에 RUN_PIPELINE 지시.
- Lease: streams.worker_id, streams.lease_expires_at 갱신. 조건부 업데이트로 동시성 제어.
- 워커 heartbeat(stream.events HEARTBEAT) 수신 시 lease_expires_at 갱신.
- lease 만료된 채널은 status=LOST 전이 후 재할당(takeover).
"""
import logging
import os
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TODO: Kafka consumer loop for stream.commands
# TODO: On START: lease_acquire(channel_id) -> (worker_id, lease_expires_at)
#        - DB: UPDATE streams SET worker_id=?, lease_expires_at=? WHERE channel_id=? AND (lease_expires_at < NOW() OR worker_id IS NULL)
#        - 성공한 워커에게 명령 전달 (Kafka worker.commands 또는 HTTP)
# TODO: On HEARTBEAT (from stream.events): stream_repo.renew_lease(channel_id, worker_id)
# TODO: Background: 만료된 lease 검사 -> status=LOST, 재할당용 START 재발행


def main() -> None:
    logger.info("Orchestrator starting (skeleton)")
    # consumer = get_consumer(STREAM_COMMANDS, group_id="orchestrator")
    # for msg in consumer: ...
    #   cmd = parse(msg); lease_acquire(cmd.channel_id); send_to_worker(...)
    while True:
        import time
        time.sleep(60)


if __name__ == "__main__":
    main()
