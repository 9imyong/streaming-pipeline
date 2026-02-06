"""Subprocess wrapper: 로그/종료 처리, signal 전파."""
import logging
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


def run_process(
    cmd: list[str],
    *,
    cwd: Optional[str] = None,
    env: Optional[dict] = None,
) -> subprocess.Popen:
    """subprocess 기동. start_new_session=True, stderr 로깅."""
    logger.info("Starting process: %s", cmd)
    return subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        start_new_session=True,
        cwd=cwd,
        env=env,
    )
