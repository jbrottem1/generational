"""Animation provider interface — future video / motion backends.

Never hardcode providers: the Animation Engine plans against
`AnimationProvider` and capability keys only. Real backends (OpenAI,
Runway, Google Veo, Kling, Pika, Luma, PixVerse, Stable Video, ...)
implement this interface and register in `providers/animation/` — nothing
in the engine changes when a backend swaps in.

The Animation Engine does NOT call providers to render final video. It
emits provider-agnostic instruction briefs; adapters later execute them.
"""

from __future__ import annotations

from abc import abstractmethod

from providers.base import Provider

# Additive-only capability vocabulary for animation backends.
ANIMATION_CAPABILITIES = (
    "video",
    "animation",
    "lip_sync",
    "motion",
    "camera",
    "character",
    "effects",
)

# Reserved provider ids — adapters register under these names.
ANIMATION_PROVIDER_IDS = (
    "openai",
    "runway",
    "google_veo",
    "kling",
    "pika",
    "luma",
    "pixverse",
    "stable_video",
    "mock_animation",
)


class AnimationProvider(Provider):
    """One animation / cinematic backend. `supports()` declares capabilities;
    `plan()` turns a brief into a provider-specific instruction payload."""

    provider_id: str = "base"
    capabilities: "tuple[str, ...]" = ()

    def supports(self, capability: str) -> bool:
        return capability in self.capabilities

    @abstractmethod
    def plan(self, brief: dict) -> "dict | None":
        """Return a provider instruction dict, or None if unsupported."""
