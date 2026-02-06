"""Inference 요청/응답 추상화 (Stream Worker → Inference Worker)."""
from abc import ABC, abstractmethod
from typing import Any


class InferenceClient(ABC):
    @abstractmethod
    async def detect(self, channel_id: str, frame_url_or_bytes: Any) -> list[dict[str, Any]]:
        """추론 요청, detections 반환."""
        ...
