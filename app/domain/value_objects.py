"""값 객체: channel_id, worker_id 등 (타입/검증)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ChannelId:
    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class WorkerId:
    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class JobId:
    value: str

    def __str__(self) -> str:
        return self.value
