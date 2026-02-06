"""Gateway health 라우트. GET /health, /health/live, /health/ready."""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    """단순 헬스 체크."""
    return {"status": "ok"}


@router.get("/health/live")
def live():
    """Liveness: 프로세스 살아있음."""
    return {"status": "ok"}


@router.get("/health/ready")
def ready():
    """Readiness: 의존성 준비 여부 (선택)."""
    return {"status": "ok"}
