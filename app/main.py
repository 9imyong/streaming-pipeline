"""
FastAPI 엔트리. legacy 앱을 로드하고 /health 라우트 추가.
실행: uvicorn app.main:app (프로젝트 루트에서 PYTHONPATH=. 또는 도커에서 PYTHONPATH=/app)
"""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from legacy.main import app

# 헬스 라우트 추가 (9IMYONG: liveness / readiness)
@app.get("/health/live")
def health_live():
    """Liveness: 프로세스 살아있음."""
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready():
    """Readiness: Redis/DB 등 필수 의존성 OK (추후 구현)."""
    return {"status": "ok"}
