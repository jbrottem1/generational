"""Music / audio bed provider interface + the mock provider the Render Engine
uses until a real licensed-music backend is wired in.

Swap providers with `set_music_provider()` — engine code only ever calls
`get_music_provider()` and never imports a vendor SDK.
"""

from __future__ import annotations

import uuid
from abc import abstractmethod

from providers.base import Provider


class MusicProvider(Provider):
    @abstractmethod
    def select_track(self, mood: str, duration_sec: float, niche: str) -> "dict | None":
        ...


class MockMusicProvider(MusicProvider):
    """Deterministic placeholder music beds — no API key, no network, no files."""

    name = "mock_music"

    def is_available(self) -> bool:
        return True

    def select_track(self, mood: str, duration_sec: float, niche: str) -> dict:
        asset_id = f"mus_{uuid.uuid4().hex[:10]}"
        return {
            "asset_id": asset_id,
            "path": f"mock://assets/music/{asset_id}.mp3",
            "placeholder": True,
            "provider": self.name,
            "mood": mood,
            "niche": niche,
            "duration_sec": float(duration_sec),
            "license": "placeholder — clear before publishing",
        }


_provider: "MusicProvider | None" = None


def get_music_provider() -> MusicProvider:
    """The active music provider (mock until a real one is registered)."""
    global _provider
    if _provider is None or not _provider.is_available():
        return MockMusicProvider()
    return _provider


def set_music_provider(provider: "MusicProvider | None") -> None:
    """Swap in a real backend (or None to fall back to the mock)."""
    global _provider
    _provider = provider
