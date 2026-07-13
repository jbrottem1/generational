"""Generation provider interface — how the Universal Asset Generation
Engine (Agent 14) talks to every AI generation backend.

Never hardcode providers: the engine plans, selects, and generates against
`GenerationProvider` only. Real backends (OpenAI, Google, Runway, Kling,
Luma, Pika, Flux, Stable Diffusion, Midjourney, Adobe, local models,
future providers) implement this interface and register in
`providers/asset_generation/` — nothing in the engine changes when a
backend swaps in, and no provider-specific logic exists outside adapters.

A provider declares:
- `asset_classes`: which media classes it can generate (image / video /
  three_d / animation / audio / motion_graphics — additive-only).
- `asset_types`: optional narrowing to specific catalog asset types
  (empty tuple = every type within its classes).
- `profile`: the selection signals the Provider Selection Engine scores —
  quality, cost per asset, speed, consistency, and optional latency_ms.
- `offline` / `local`: whether it runs without network / on local
  hardware — the selection engine uses these for offline and local-model
  routing.
- `prompt_style`: dialect hints the Prompt Compiler uses to optimize the
  compiled prompt for this specific backend.
"""

from __future__ import annotations

from abc import abstractmethod

from providers.base import Provider

# The media classes the engine can generate. Additive-only — future
# classes append here. Phase 2 prepared: animation, audio (sfx/music/
# voice), and motion graphics alongside image / video / three_d.
GENERATION_ASSET_CLASSES = (
    "image",
    "video",
    "three_d",
    "animation",
    "audio",
    "motion_graphics",
)

# The selection signals every provider profile carries.
PROVIDER_PROFILE_FIELDS = (
    "quality",          # 0-100 typical output quality
    "cost_per_asset",   # USD per generated asset (0.0 = free)
    "speed",            # 0-100 (higher = faster generation)
    "consistency",      # 0-100 ability to reproduce characters/styles
    "latency_ms",       # typical end-to-end latency in milliseconds (0 = unknown)
)


class GenerationProvider(Provider):
    """One AI generation backend. `supports()` declares coverage;
    `generate()` turns one compiled prompt spec into one asset reference."""

    name: str = "generation_base"
    label: str = ""
    asset_classes: "tuple[str, ...]" = ()
    asset_types: "tuple[str, ...]" = ()   # () = all types in its classes
    offline: bool = False                 # runs without network access
    local: bool = False                   # runs on local hardware
    profile: dict = {}                    # PROVIDER_PROFILE_FIELDS values
    prompt_style: dict = {}               # compiler dialect hints
    # Optional capability tags for registry discovery (additive).
    capabilities: "tuple[str, ...]" = ()

    def supports(self, asset_class: str, asset_type: str = "") -> bool:
        if asset_class not in self.asset_classes:
            return False
        if asset_type and self.asset_types and asset_type not in self.asset_types:
            return False
        return True

    def estimate_cost(self, request: dict) -> float:
        """Predicted USD cost of fulfilling one request (default: profile)."""
        return float(self.profile.get("cost_per_asset", 0.0))

    def estimate_latency_ms(self, request: dict = None) -> int:
        """Predicted latency in ms (profile.latency_ms, else derived from speed)."""
        explicit = self.profile.get("latency_ms")
        if explicit is not None and int(explicit) > 0:
            return int(explicit)
        # Map speed 0-100 → latency 30s → 1s when latency_ms is unset.
        speed = float(self.profile.get("speed", 50))
        return int(max(1000, 30_000 - (speed / 100.0) * 29_000))

    def describe(self) -> dict:
        """Uniform self-description for the provider registry catalog."""
        return {
            "name": self.name,
            "label": self.label or self.name,
            "asset_classes": list(self.asset_classes),
            "asset_types": list(self.asset_types),
            "offline": bool(self.offline),
            "local": bool(self.local),
            "available": bool(self.is_available()),
            "profile": {
                field: self.profile.get(field, 0 if field != "cost_per_asset" else 0.0)
                for field in PROVIDER_PROFILE_FIELDS
            },
            "prompt_style": dict(self.prompt_style or {}),
            "capabilities": list(self.capabilities),
            "latency_ms": self.estimate_latency_ms(),
        }

    @abstractmethod
    def generate(self, prompt_spec: dict, request: dict) -> dict:
        """Generate one asset from a compiled PROMPT_SPEC_FIELDS dict.

        Returns a JSON-safe dict with at least {uri, provider, format,
        width, height} (videos add duration_sec; audio adds duration_sec /
        sample_rate) — or {"error": "..."} when generation fails.
        Implementations NEVER raise into the engine; they report failures
        in the returned dict.
        """
