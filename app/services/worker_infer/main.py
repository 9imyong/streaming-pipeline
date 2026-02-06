"""Inference Worker 진입점. 추론 요청 소비, ai.events 발행."""
import logging
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Inference Worker starting")
    # consume frame/snapshot -> pipeline.detect() -> emit_ai_events.emit()
    while True:
        import time
        time.sleep(60)


if __name__ == "__main__":
    main()
