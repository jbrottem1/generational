"""Future animation provider adapter stubs — one class per vendor.

Every provider-specific detail lives HERE. Adapters report unavailable
until their API key is configured; the deterministic mock serves Demo Mode.
Wiring a real backend means implementing `plan()` / future `render()` and
setting the key — nothing else in the system changes.
"""

from __future__ import annotations

import os

from providers.animation_provider import AnimationProvider


class _StubAdapter(AnimationProvider):
    """Shared plumbing: available only when the API key env var is set."""

    api_key_env: str = ""

    def is_available(self) -> bool:
        return bool(self.api_key_env and os.environ.get(self.api_key_env))

    def plan(self, brief: dict) -> dict:
        return {
            "provider": self.provider_id,
            "capability": brief.get("capability", "video"),
            "status": "not_implemented",
            "placeholder": True,
            "error": f"{self.name} adapter is registered but not implemented yet",
            "instruction": brief.get("brief", {}),
            "refs": list(brief.get("refs") or []),
        }


class OpenAIAnimationAdapter(_StubAdapter):
    name = "openai"
    provider_id = "openai"
    api_key_env = "OPENAI_API_KEY"
    capabilities = ("video", "animation", "lip_sync", "motion")


class RunwayAdapter(_StubAdapter):
    name = "runway"
    provider_id = "runway"
    api_key_env = "RUNWAY_API_KEY"
    capabilities = ("video", "animation", "camera", "motion")


class GoogleVeoAdapter(_StubAdapter):
    name = "google_veo"
    provider_id = "google_veo"
    api_key_env = "GOOGLE_API_KEY"
    capabilities = ("video", "animation", "camera", "motion")


class KlingAdapter(_StubAdapter):
    name = "kling"
    provider_id = "kling"
    api_key_env = "KLING_API_KEY"
    capabilities = ("video", "animation", "motion")


class PikaAdapter(_StubAdapter):
    name = "pika"
    provider_id = "pika"
    api_key_env = "PIKA_API_KEY"
    capabilities = ("video", "animation", "motion")


class LumaAdapter(_StubAdapter):
    name = "luma"
    provider_id = "luma"
    api_key_env = "LUMA_API_KEY"
    capabilities = ("video", "animation", "camera", "motion")


class PixVerseAdapter(_StubAdapter):
    name = "pixverse"
    provider_id = "pixverse"
    api_key_env = "PIXVERSE_API_KEY"
    capabilities = ("video", "animation", "motion")


class StableVideoAdapter(_StubAdapter):
    name = "stable_video"
    provider_id = "stable_video"
    api_key_env = "STABILITY_API_KEY"
    capabilities = ("video", "animation", "motion")


ALL_ADAPTERS = (
    OpenAIAnimationAdapter,
    RunwayAdapter,
    GoogleVeoAdapter,
    KlingAdapter,
    PikaAdapter,
    LumaAdapter,
    PixVerseAdapter,
    StableVideoAdapter,
)
