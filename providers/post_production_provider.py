"""Post-production provider interface — swappable editing backends."""

from __future__ import annotations

from abc import ABC, abstractmethod

POST_PRODUCTION_PROVIDER_FIELDS = (
    "name",
    "label",
    "capabilities",
    "supported_formats",
    "supported_platforms",
    "max_resolution",
    "supports_hdr",
    "supports_batch",
)


class PostProductionProvider(ABC):
    """Abstract editing backend — FFmpeg, Premiere, DaVinci, CapCut, Runway, etc."""

    name: str = ""
    label: str = ""

    @abstractmethod
    def capabilities(self) -> list:
        """Operations this provider supports."""

    @abstractmethod
    def assemble(self, package: dict) -> dict:
        """Assemble the edit timeline into a renderable project."""

    @abstractmethod
    def export(self, package: dict, preset_id: str) -> dict:
        """Export the assembled project to the given preset."""

    @abstractmethod
    def validate(self, package: dict) -> dict:
        """Provider-side validation of the post-production package."""

    def profile(self) -> dict:
        return {
            "name": self.name,
            "label": self.label,
            "capabilities": self.capabilities(),
            "supported_formats": ["mp4", "mov"],
            "supported_platforms": ["youtube_shorts", "tiktok", "instagram_reels"],
            "max_resolution": {"width": 3840, "height": 2160},
            "supports_hdr": False,
            "supports_batch": True,
        }
