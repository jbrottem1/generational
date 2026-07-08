"""Publishing provider interface."""

from __future__ import annotations

from abc import abstractmethod

from providers.base import Provider


class PublishingProvider(Provider):
    @abstractmethod
    def enqueue(self, render_package: dict, platforms: list) -> dict:
        ...
