"""관리/이벤트 라우트. (기존 VAControl, request_event 등 이전 대상)"""
from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])
