"""Orchestrator 진입점. stream.commands 소비 루프."""
import logging
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Orchestrator starting")
    # from app.infrastructure.messaging.kafka.consumer import consume_commands
    # consume_commands() -> assigner.assign() -> publisher.send_to_worker()
    while True:
        import time
        time.sleep(60)


if __name__ == "__main__":
    main()
