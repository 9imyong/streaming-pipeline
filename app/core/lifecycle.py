"""
Startup/shutdown 시 리소스 초기화·정리.
- 등록된 콜백만 실행. Kafka/DB/ffmpeg 연결은 각 서비스·infrastructure에서 수행.
- 비즈니스 로직·상태 머신 없음.
"""
import logging
from typing import Callable, Coroutine

logger = logging.getLogger(__name__)

# 앱별로 등록하는 startup/shutdown 콜백 (예: Gateway에서 repo 주입, Worker에서 consumer 기동)
_startup_callbacks: list[Callable[[], Coroutine[None, None, None]]] = []
_shutdown_callbacks: list[Callable[[], Coroutine[None, None, None]]] = []


def on_startup(cb: Callable[[], Coroutine[None, None, None]]) -> None:
    """startup 시 실행할 async 콜백 등록."""
    _startup_callbacks.append(cb)


def on_shutdown(cb: Callable[[], Coroutine[None, None, None]]) -> None:
    """shutdown 시 실행할 async 콜백 등록."""
    _shutdown_callbacks.append(cb)


async def run_startup() -> None:
    """등록된 startup 콜백 순서대로 실행."""
    for cb in _startup_callbacks:
        try:
            await cb()
        except Exception as e:
            logger.exception("Startup callback failed: %s", e)
            raise


async def run_shutdown() -> None:
    """등록된 shutdown 콜백 역순 실행."""
    for cb in reversed(_shutdown_callbacks):
        try:
            await cb()
        except Exception as e:
            logger.exception("Shutdown callback failed: %s", e)


def create_lifespan_context(app: object) -> None:
    """
    FastAPI lifespan에 넣을 수 있는 콜백 등록용.
    실제 lifespan은 app에서:
      @asynccontextmanager
      async def lifespan(app):
          await run_startup()
          yield
          await run_shutdown()
    """
    pass  # 등록은 on_startup / on_shutdown 으로 별도 호출
