"""Music / audio bed provider interface."""

from __future__ import annotations

from abc import abstractmethod

from providers.base import Provider


class MusicProvider(Provider):
    @abstractmethod
    def select_track(self, mood: str, duration_sec: float, niche: str) -> "dict | None":
        ...
