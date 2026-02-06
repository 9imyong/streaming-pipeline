"""
구조화 로그 설정. event, request_id, channel_id, worker_id, job_id, duration_ms 등 포함 가능.
- dev: 사람이 읽기 쉬운 포맷
- prod: JSON 한 줄 (로그 수집/검색용)
비즈니스 로직 없음.
"""
import json
import logging
import sys
from typing import Any

from app.core.config import get_settings


class JsonFormatter(logging.Formatter):
    """LogRecord를 JSON 한 줄로 출력. extra 필드 포함."""

    _SKIP = {"name", "msg", "args", "created", "filename", "funcName", "levelname", "levelno", "lineno", "module", "msecs", "pathname", "process", "processName", "relativeCreated", "stack_info", "exc_info", "exc_text", "thread", "threadName", "message", "taskName"}

    def format(self, record: logging.LogRecord) -> str:
        obj: dict[str, Any] = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for k, v in record.__dict__.items():
            if k not in self._SKIP and v is not None:
                obj[k] = v
        if record.exc_info:
            obj["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(obj, ensure_ascii=False)


def _configure_stdlib_logging() -> None:
    """표준 logging 모듈 설정. dev/prod에 따라 포맷 변경."""
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.root.setLevel(level)

    if not logging.root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        logging.root.addHandler(handler)

    if settings.is_prod:
        formatter: logging.Formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )

    for h in logging.root.handlers:
        h.setFormatter(formatter)
        h.setLevel(level)


_configured = False


def get_logger(name: str) -> logging.Logger:
    """모듈별 로거. 구조화 필드는 extra로 전달."""
    global _configured
    if not _configured:
        _configure_stdlib_logging()
        _configured = True
    return logging.getLogger(name)


class StructuredAdapter(logging.LoggerAdapter):
    """고정 필드(channel_id, worker_id, request_id 등)를 매 메시지에 붙이는 어댑터."""

    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        extra = kwargs.get("extra") or {}
        extra.update(self.extra or {})
        kwargs["extra"] = extra
        return msg, kwargs


def bind_logger(
    logger: logging.Logger,
    *,
    channel_id: str | None = None,
    worker_id: str | None = None,
    request_id: str | None = None,
    job_id: str | None = None,
) -> StructuredAdapter:
    """고정 컨텍스트를 붙인 로거. 유스케이스/워커에서 사용."""
    extra: dict[str, Any] = {}
    if channel_id is not None:
        extra["channel_id"] = channel_id
    if worker_id is not None:
        extra["worker_id"] = worker_id
    if request_id is not None:
        extra["request_id"] = request_id
    if job_id is not None:
        extra["job_id"] = job_id
    return StructuredAdapter(logger, extra)
