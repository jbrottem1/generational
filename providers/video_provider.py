"""Video generation provider interface + the mock provider the Render Engine
uses until a real backend (Runway, Kling, Veo, stock APIs, ...) is wired in.

Swap providers with `set_video_provider()` — engine code only ever calls
`get_video_provider()` and never imports a vendor SDK.
"""

from __future__ import annotations

import uuid
from abc import abstractmethod

from providers.base import Provider


class VideoProvider(Provider):
    @abstractmethod
    def generate(self, prompt: str, duration_sec: float, metadata: dict) -> "dict | None":
        ...


class MockVideoProvider(VideoProvider):
    """Deterministic placeholder clips — no API key, no network, no files."""

    name = "mock_video"

    def is_available(self) -> bool:
        return True

    def generate(self, prompt: str, duration_sec: float, metadata: dict) -> dict:
        asset_id = f"vid_{uuid.uuid4().hex[:10]}"
        return {
            "asset_id": asset_id,
            "path": f"mock://assets/video/{asset_id}.mp4",
            "placeholder": True,
            "provider": self.name,
            "prompt": prompt,
            "duration_sec": float(duration_sec),
            "width": metadata.get("width", 1080),
            "height": metadata.get("height", 1920),
        }


_provider: "VideoProvider | None" = None


def get_video_provider() -> VideoProvider:
    """The active video provider (mock until a real one is registered)."""
    global _provider
    if _provider is None or not _provider.is_available():
        return MockVideoProvider()
    return _provider


def set_video_provider(provider: "VideoProvider | None") -> None:
    """Swap in a real backend (or None to fall back to the mock)."""
    global _provider
    _provider = provider
