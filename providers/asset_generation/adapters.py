"""Adapter stubs for real AI generation backends — one class per vendor.

Every provider-specific detail (availability check, prompt dialect,
selection profile, and eventually the real API call) lives HERE and only
here — the engine never mentions a vendor by name. Each adapter reports
unavailable until its API key is configured, so the deterministic mock
serves Demo Mode; wiring a real backend means implementing `generate()`
in its adapter and setting the key — nothing else in the system changes.

Profiles are indicative selection signals (0-100 / USD / latency_ms),
tuned as real usage data arrives. Availability is keyed on environment
variables so no credentials are ever stored in the repo.

Phase 2: adapters for OpenAI Images, Runway, Flux, Kling, Pika, Luma,
Veo, Stable Diffusion, Midjourney (placeholder), plus prepared stubs for
animation / audio / motion-graphics media classes.
"""

from __future__ import annotations

import os

from providers.generation_provider import GenerationProvider


class _StubAdapter(GenerationProvider):
    """Shared plumbing: available only when the API key env var is set;
    `generate()` reports not-implemented instead of raising. Subclasses
    set class attributes only — no duplicated availability/generate logic."""

    api_key_env: str = ""

    def is_available(self) -> bool:
        return bool(self.api_key_env and os.environ.get(self.api_key_env))

    def generate(self, prompt_spec: dict, request: dict) -> dict:
        return {
            "error": (
                f"{self.name} adapter is registered but its API call "
                "is not implemented yet"
            ),
            "provider": self.name,
        }


# ------------------------------------------------------------------ images


class OpenAIImageAdapter(_StubAdapter):
    name = "openai_images"
    label = "OpenAI (gpt-image)"
    api_key_env = "OPENAI_API_KEY"
    asset_classes = ("image",)
    capabilities = ("image-gen", "photorealistic", "illustration")
    profile = {
        "quality": 90, "cost_per_asset": 0.08, "speed": 70,
        "consistency": 75, "latency_ms": 8000,
    }
    prompt_style = {
        "dialect": "natural_language",
        "supports_negative_prompt": False,
        "prefers": "full descriptive sentences; style and lighting stated explicitly",
    }


class GoogleImagenAdapter(_StubAdapter):
    name = "google_imagen"
    label = "Google Imagen"
    api_key_env = "GOOGLE_API_KEY"
    asset_classes = ("image",)
    capabilities = ("image-gen",)
    profile = {
        "quality": 88, "cost_per_asset": 0.06, "speed": 75,
        "consistency": 72, "latency_ms": 7000,
    }
    prompt_style = {"dialect": "natural_language", "supports_negative_prompt": True}


class FluxAdapter(_StubAdapter):
    name = "flux"
    label = "Flux (Black Forest Labs)"
    api_key_env = "BFL_API_KEY"
    asset_classes = ("image",)
    capabilities = ("image-gen", "fast-image")
    profile = {
        "quality": 89, "cost_per_asset": 0.05, "speed": 80,
        "consistency": 78, "latency_ms": 5000,
    }
    prompt_style = {"dialect": "tagged", "supports_negative_prompt": False}


class StableDiffusionAdapter(_StubAdapter):
    name = "stable_diffusion"
    label = "Stable Diffusion (Stability API)"
    api_key_env = "STABILITY_API_KEY"
    asset_classes = ("image",)
    capabilities = ("image-gen", "local-compatible")
    profile = {
        "quality": 82, "cost_per_asset": 0.03, "speed": 85,
        "consistency": 80, "latency_ms": 4000,
    }
    prompt_style = {
        "dialect": "tagged",
        "supports_negative_prompt": True,
        "prefers": "comma-separated tags; quality boosters appended; negatives essential",
    }


class MidjourneyAdapter(_StubAdapter):
    """Placeholder adapter — Midjourney has no public API today.
    Registered for selection scoring and future wiring; remains
    unavailable until MIDJOURNEY_API_KEY is set and generate() is implemented."""

    name = "midjourney"
    label = "Midjourney (placeholder)"
    api_key_env = "MIDJOURNEY_API_KEY"
    asset_classes = ("image",)
    capabilities = ("image-gen", "placeholder")
    profile = {
        "quality": 93, "cost_per_asset": 0.10, "speed": 40,
        "consistency": 62, "latency_ms": 25000,
    }
    prompt_style = {
        "dialect": "tagged",
        "supports_negative_prompt": True,
        "parameter_suffix": True,   # --ar / --style style parameters
    }


class AdobeFireflyAdapter(_StubAdapter):
    name = "adobe_firefly"
    label = "Adobe Firefly"
    api_key_env = "ADOBE_API_KEY"
    asset_classes = ("image",)
    capabilities = ("image-gen", "brand-safe")
    profile = {
        "quality": 86, "cost_per_asset": 0.07, "speed": 65,
        "consistency": 74, "latency_ms": 9000,
    }
    prompt_style = {"dialect": "natural_language", "supports_negative_prompt": False}


# ------------------------------------------------------------------- video


class GoogleVeoAdapter(_StubAdapter):
    name = "google_veo"
    label = "Google Veo"
    api_key_env = "GOOGLE_API_KEY"
    asset_classes = ("video", "animation")
    capabilities = ("video-gen", "cinematic", "animation")
    profile = {
        "quality": 92, "cost_per_asset": 1.50, "speed": 35,
        "consistency": 70, "latency_ms": 45000,
    }
    prompt_style = {
        "dialect": "cinematic",
        "supports_negative_prompt": True,
        "prefers": "camera movement and lens described first, then subject and mood",
    }


class RunwayAdapter(_StubAdapter):
    name = "runway"
    label = "Runway"
    api_key_env = "RUNWAY_API_KEY"
    asset_classes = ("video", "animation", "motion_graphics")
    capabilities = ("video-gen", "animation", "motion-graphics")
    profile = {
        "quality": 88, "cost_per_asset": 1.00, "speed": 45,
        "consistency": 68, "latency_ms": 35000,
    }
    prompt_style = {"dialect": "cinematic", "supports_negative_prompt": False}


class KlingAdapter(_StubAdapter):
    name = "kling"
    label = "Kling"
    api_key_env = "KLING_API_KEY"
    asset_classes = ("video", "animation")
    capabilities = ("video-gen", "animation")
    profile = {
        "quality": 85, "cost_per_asset": 0.70, "speed": 40,
        "consistency": 66, "latency_ms": 40000,
    }
    prompt_style = {"dialect": "cinematic", "supports_negative_prompt": True}


class LumaAdapter(_StubAdapter):
    name = "luma"
    label = "Luma Dream Machine"
    api_key_env = "LUMA_API_KEY"
    asset_classes = ("video", "three_d", "animation")
    capabilities = ("video-gen", "three-d", "animation")
    profile = {
        "quality": 84, "cost_per_asset": 0.60, "speed": 50,
        "consistency": 64, "latency_ms": 30000,
    }
    prompt_style = {"dialect": "cinematic", "supports_negative_prompt": False}


class PikaAdapter(_StubAdapter):
    name = "pika"
    label = "Pika"
    api_key_env = "PIKA_API_KEY"
    asset_classes = ("video", "animation", "motion_graphics")
    capabilities = ("video-gen", "animation", "motion-graphics")
    profile = {
        "quality": 80, "cost_per_asset": 0.45, "speed": 60,
        "consistency": 60, "latency_ms": 20000,
    }
    prompt_style = {"dialect": "cinematic", "supports_negative_prompt": True}


# -------------------------------------------------------- future media


class ElevenLabsAudioAdapter(_StubAdapter):
    """Prepared stub for sound effects / music / voice generation.
    Not wired to live APIs — registers the audio media class for selection."""

    name = "elevenlabs_audio"
    label = "ElevenLabs Audio (prepared)"
    api_key_env = "ELEVENLABS_API_KEY"
    asset_classes = ("audio",)
    capabilities = ("sfx", "music", "voice")
    profile = {
        "quality": 88, "cost_per_asset": 0.12, "speed": 70,
        "consistency": 80, "latency_ms": 6000,
    }
    prompt_style = {"dialect": "natural_language", "supports_negative_prompt": False}


class MotionGraphicsAdapter(_StubAdapter):
    """Prepared stub for motion-graphics / kinetic-typography backends."""

    name = "motion_graphics_stub"
    label = "Motion Graphics (prepared)"
    api_key_env = "MOTION_GRAPHICS_API_KEY"
    asset_classes = ("motion_graphics",)
    capabilities = ("motion-graphics", "kinetic-typography")
    profile = {
        "quality": 75, "cost_per_asset": 0.20, "speed": 55,
        "consistency": 70, "latency_ms": 15000,
    }
    prompt_style = {"dialect": "tagged", "supports_negative_prompt": True}


# --------------------------------------------------------------- local


class LocalDiffusionAdapter(GenerationProvider):
    """Local model support — a diffusion model running on the user's own
    hardware. Offline and free; availability is keyed on an explicit
    endpoint env var (e.g. a local ComfyUI / A1111 / MLX server)."""

    name = "local_diffusion"
    label = "Local Diffusion Model"
    api_endpoint_env = "LOCAL_DIFFUSION_ENDPOINT"
    asset_classes = ("image",)
    offline = True
    local = True
    capabilities = ("image-gen", "offline", "local")
    profile = {
        "quality": 70, "cost_per_asset": 0.0, "speed": 55,
        "consistency": 82, "latency_ms": 12000,
    }
    prompt_style = {"dialect": "tagged", "supports_negative_prompt": True}

    def is_available(self) -> bool:
        return bool(os.environ.get(self.api_endpoint_env))

    def generate(self, prompt_spec: dict, request: dict) -> dict:
        return {
            "error": (
                "local_diffusion adapter is registered but its API call "
                "is not implemented yet"
            ),
            "provider": self.name,
        }


# Every adapter class shipped today. The registry instantiates and
# registers them at import time; future vendors append one class here (or
# register from their own module) — never touch engine code.
ADAPTER_CLASSES = (
    OpenAIImageAdapter,
    GoogleImagenAdapter,
    FluxAdapter,
    StableDiffusionAdapter,
    MidjourneyAdapter,
    AdobeFireflyAdapter,
    GoogleVeoAdapter,
    RunwayAdapter,
    KlingAdapter,
    LumaAdapter,
    PikaAdapter,
    ElevenLabsAudioAdapter,
    MotionGraphicsAdapter,
    LocalDiffusionAdapter,
)
