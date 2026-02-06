"""Gateway health 라우트 (gateway/main.py에서 include 가능)."""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health/live")
def live():
    return {"status": "ok"}


@router.get("/health/ready")
def ready():
    return {"status": "ok"}
