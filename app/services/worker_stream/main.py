"""Stream Worker 진입점. 채널별 subprocess 실행."""
import logging
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Stream Worker starting")
    # from app.services.worker_stream.manager import ChannelManager
    # consumer loop -> manager.start_channel / stop_channel
    # heartbeat_loop -> heartbeat.emit()
    while True:
        import time
        time.sleep(60)


if __name__ == "__main__":
    main()
