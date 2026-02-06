"""
추론 파이프라인: 모델 로드(lifespan 1회), 배치/직렬화.
- 스트리밍 파이프라인 유지 금지. 프레임/이미지 입력 → 검출 결과만 반환.
- INFERENCE_MOCK=1 또는 미설정 시 mock(stub) 사용. 실제 모델은 별도 전환.
"""
import logging
import os
from typing import Any, List

logger = logging.getLogger(__name__)

_model: Any = None


def _is_mock() -> bool:
    """환경 변수로 mock 모드 여부. 기본 True(개발 시 mock)."""
    return os.environ.get("INFERENCE_MOCK", "1").strip() in ("1", "true", "yes")


def load_model() -> None:
    """lifespan에서 1회 호출. INFERENCE_MOCK이면 stub, 아니면 실제 모델 로드."""
    global _model
    if _model is not None:
        return
    if _is_mock():
        _model = "stub"
        logger.info("inference model loaded (mock/stub)")
        return
    # 실제 모델 로드 (YOLO/Detector 등)
    _model = "stub"  # TODO: 실제 로드로 교체
    logger.info("inference model loaded")


def detect(image_url: str | None = None, image_bytes: bytes | None = None) -> List[dict[str, Any]]:
    """
    이미지 URL 또는 바이트로 검출. 반환값은 직렬화 가능한 dict 목록.
    이미지 바이트는 Kafka로 보내지 않음. 저장 후 URL만 이벤트에 포함.
    """
    if _model is None:
        load_model()
    # 스텁: 실제로는 모델 추론 후 bbox, class, score 등 반환
    return [{"class_name": "person", "score": 0.9, "bbox": [0.1, 0.1, 0.5, 0.8]}]
