"""Image generation provider interface + the mock provider the Render Engine
uses until a real backend (DALL·E, Flux, Midjourney, ...) is wired in.

Swap providers with `set_image_provider()` — engine code only ever calls
`get_image_provider()` and never imports a vendor SDK.
"""

from __future__ import annotations

import uuid
from abc import abstractmethod

from providers.base import Provider


class ImageProvider(Provider):
    @abstractmethod
    def generate(self, prompt: str, metadata: dict) -> "dict | None":
        """Returns {asset_id, path, placeholder} or None."""


class MockImageProvider(ImageProvider):
    """Deterministic placeholder images — no API key, no network, no files."""

    name = "mock_image"

    def is_available(self) -> bool:
        return True

    def generate(self, prompt: str, metadata: dict) -> dict:
        asset_id = f"img_{uuid.uuid4().hex[:10]}"
        return {
            "asset_id": asset_id,
            "path": f"mock://assets/images/{asset_id}.png",
            "placeholder": True,
            "provider": self.name,
            "prompt": prompt,
            "width": metadata.get("width", 1080),
            "height": metadata.get("height", 1920),
        }


_provider: "ImageProvider | None" = None


def get_image_provider() -> ImageProvider:
    """The active image provider (mock until a real one is registered)."""
    global _provider
    if _provider is None or not _provider.is_available():
        return MockImageProvider()
    return _provider


def set_image_provider(provider: "ImageProvider | None") -> None:
    """Swap in a real backend (or None to fall back to the mock)."""
    global _provider
    _provider = provider
