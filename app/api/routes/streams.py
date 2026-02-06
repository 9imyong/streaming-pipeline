"""스트림 시작/중지, 상태 라우트. (기존 fastapi main 의 CCTVLIST, live, HLS 등 이전 대상)"""
from fastapi import APIRouter

router = APIRouter(prefix="/streams", tags=["streams"])
# TODO: 기존 /CCTVLIST/, /live/{START_STOP}, /hls/* 등을 이 router 로 이전
