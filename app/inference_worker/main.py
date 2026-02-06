"""
Inference Worker 진입점 (스켈레톤).
- Stream Worker가 보낸 프레임(또는 snapshot URL)을 소비.
- 추론 후 ai.events에 결과 발행. 이미지 바이트 대신 snapshot_url만 포함.
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


def main() -> None:
    logger.info("Inference Worker starting (skeleton)")
    # TODO: consume frame queue or snapshot URLs
    # TODO: run detector, publish to ai.events with snapshot_url only
    pass


if __name__ == "__main__":
    main()
