"""Voice provider interface — AI, recorded, and clone modes."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass

from providers.base import Provider


class VoiceMode:
    AI = "ai"
    RECORDED = "recorded"
    CLONE = "clone"


@dataclass
class NarrationResult:
    asset_id: str
    duration_sec: float
    path: str
    mode: str
    placeholder: bool = True
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class VoiceProvider(Provider):
    mode: str = VoiceMode.AI

    @abstractmethod
    def synthesize(self, text: str, profile: dict, settings: dict) -> NarrationResult:
        """Generate or resolve narration audio for the given text."""
