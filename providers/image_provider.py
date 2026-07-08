"""Image generation provider interface."""

from __future__ import annotations

from abc import abstractmethod

from providers.base import Provider


class ImageProvider(Provider):
    @abstractmethod
    def generate(self, prompt: str, metadata: dict) -> "dict | None":
        """Returns {asset_id, path, placeholder} or None."""
