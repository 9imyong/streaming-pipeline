"""
추론 파이프라인: 모델 로드(lifespan 1회), 배치/직렬화.
- 스트리밍 파이프라인 유지 금지. 프레임/이미지 입력 → 검출 결과만 반환.
"""
import logging
from typing import Any, List

logger = logging.getLogger(__name__)

_model: Any = None


def load_model() -> None:
    """lifespan에서 1회 호출. 실제 구현은 모델 파일 로드."""
    global _model
    if _model is not None:
        return
    # 스텁: 실제로는 YOLO/Detector 로드
    _model = "stub"
    logger.info("inference model loaded (stub)")


def detect(image_url: str | None = None, image_bytes: bytes | None = None) -> List[dict[str, Any]]:
    """
    이미지 URL 또는 바이트로 검출. 반환값은 직렬화 가능한 dict 목록.
    이미지 바이트는 Kafka로 보내지 않음. 저장 후 URL만 이벤트에 포함.
    """
    if _model is None:
        load_model()
    # 스텁: 실제로는 모델 추론 후 bbox, class, score 등 반환
    return [{"class_name": "person", "score": 0.9, "bbox": [0.1, 0.1, 0.5, 0.8]}]
