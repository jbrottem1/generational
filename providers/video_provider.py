"""Video generation provider interface."""

from __future__ import annotations

from abc import abstractmethod

from providers.base import Provider


class VideoProvider(Provider):
    @abstractmethod
    def generate(self, prompt: str, duration_sec: float, metadata: dict) -> "dict | None":
        ...
