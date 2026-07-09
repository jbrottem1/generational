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
  three_d — additive-only).
- `asset_types`: optional narrowing to specific catalog asset types
  (empty tuple = every type within its classes).
- `profile`: the selection signals the Provider Selection Engine scores —
  quality, cost per asset, speed, and consistency (all 0-100 except cost,
  which is USD per asset).
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
# classes (audio-reactive visuals, spatial/VR scenes, ...) append here.
GENERATION_ASSET_CLASSES = (
    "image",
    "video",
    "three_d",
)

# The selection signals every provider profile carries.
PROVIDER_PROFILE_FIELDS = (
    "quality",          # 0-100 typical output quality
    "cost_per_asset",   # USD per generated asset (0.0 = free)
    "speed",            # 0-100 (higher = faster generation)
    "consistency",      # 0-100 ability to reproduce characters/styles
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

    def supports(self, asset_class: str, asset_type: str = "") -> bool:
        if asset_class not in self.asset_classes:
            return False
        if asset_type and self.asset_types and asset_type not in self.asset_types:
            return False
        return True

    def estimate_cost(self, request: dict) -> float:
        """Predicted USD cost of fulfilling one request (default: profile)."""
        return float(self.profile.get("cost_per_asset", 0.0))

    @abstractmethod
    def generate(self, prompt_spec: dict, request: dict) -> dict:
        """Generate one asset from a compiled PROMPT_SPEC_FIELDS dict.

        Returns a JSON-safe dict with at least {uri, provider, format,
        width, height} (videos add duration_sec) — or {"error": "..."}
        when generation fails. Implementations NEVER raise into the
        engine; they report failures in the returned dict.
        """
