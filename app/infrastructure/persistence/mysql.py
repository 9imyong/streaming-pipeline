"""
MySQL 접근. 연결 풀 제공. 비즈니스 로직 없음.
- 설정은 app.core.config 사용.
"""
import logging
from contextlib import contextmanager
from typing import Any, Generator

import pymysql
from pymysql.connections import Connection

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_connection_params: dict[str, Any] | None = None


def _get_params() -> dict[str, Any]:
    global _connection_params
    if _connection_params is None:
        s = get_settings()
        _connection_params = {
            "host": s.db_host,
            "port": s.db_port,
            "user": s.db_user,
            "password": s.db_password,
            "database": s.db_name,
            "charset": "utf8mb4",
            "cursorclass": pymysql.cursors.DictCursor,
        }
    return _connection_params.copy()


@contextmanager
def get_connection() -> Generator[Connection, None, None]:
    """컨텍스트 매니저로 커넥션 획득. commit/rollback은 호출부에서."""
    conn = pymysql.connect(**_get_params())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
