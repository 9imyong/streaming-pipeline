"""Health/readiness 라우트. (현재는 app/main.py 에서 직접 등록)"""
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def live():
    return {"status": "ok"}


@router.get("/ready")
def ready():
    return {"status": "ok"}
