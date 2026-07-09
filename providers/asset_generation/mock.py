"""Deterministic mock generation provider — no API key, no network.

Serves every asset class and type so the whole Universal Asset Generation
Engine runs end-to-end in Demo Mode today. Real backends replace it via
`register_generation_provider()` — nothing in the engine changes. The
mock is also the guaranteed offline fallback of last resort: whatever
providers are configured, generation can never dead-end.
"""

from __future__ import annotations

import hashlib

from providers.generation_provider import GENERATION_ASSET_CLASSES, GenerationProvider

_EXTENSIONS = {"image": "png", "video": "mp4", "three_d": "glb"}


class MockGenerationProvider(GenerationProvider):
    name = "mock_generation"
    label = "Mock Generation (Demo Mode)"
    asset_classes = GENERATION_ASSET_CLASSES
    asset_types = ()          # every type
    offline = True
    local = True
    profile = {
        "quality": 40,        # placeholders — real backends always outscore it
        "cost_per_asset": 0.0,
        "speed": 100,
        "consistency": 100,   # deterministic: identical input, identical output
    }
    prompt_style = {"dialect": "plain", "supports_negative_prompt": True}

    def is_available(self) -> bool:
        return True

    def generate(self, prompt_spec: dict, request: dict) -> dict:
        asset_class = request.get("asset_class", "image")
        asset_type = request.get("asset_type", "image")
        # Deterministic URI: the same compiled prompt always yields the
        # same reference, so caching, re-runs, and tests are reproducible.
        digest = hashlib.sha256(
            "|".join(
                (
                    str(request.get("asset_id", "")),
                    asset_type,
                    str(prompt_spec.get("prompt", "")),
                    str(prompt_spec.get("negative_prompt", "")),
                    str(prompt_spec.get("aspect_ratio", "")),
                    str(prompt_spec.get("resolution", "")),
                )
            ).encode("utf-8")
        ).hexdigest()[:16]
        width, height = _dimensions(prompt_spec)
        result = {
            "uri": f"mock://assets/generated/{asset_type}/{digest}.{_EXTENSIONS.get(asset_class, 'bin')}",
            "provider": self.name,
            "model": "mock-deterministic-v1",
            "format": _EXTENSIONS.get(asset_class, "bin"),
            "width": width,
            "height": height,
            "placeholder": True,
        }
        if asset_class == "video":
            result["duration_sec"] = float(request.get("duration_sec", 5.0) or 5.0)
        return result


def _dimensions(prompt_spec: dict) -> "tuple[int, int]":
    resolution = str(prompt_spec.get("resolution", "1024x1024"))
    try:
        width_text, height_text = resolution.lower().split("x", 1)
        return int(width_text), int(height_text)
    except (ValueError, AttributeError):
        return 1024, 1024
