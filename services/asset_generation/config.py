"""Asset generation configuration — every operational knob in one place.

Same convention as `services/market_intelligence/config.py`: one frozen-in
-shape dataclass, JSON overrides from `data/asset_generation/config.json`,
`configure()` for runtime overrides, `reset_asset_generation_config()`
for tests. Unknown JSON keys are ignored so old configs never crash new
code.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field

_DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "asset_generation",
)

_CONFIG_FILE = "config.json"

# Provider selection strategies the Selection Engine understands.
SELECTION_STRATEGIES = ("balanced", "quality", "cost", "speed", "consistency", "latency")

# Quality tier → minimum acceptable output pixel count (width × height).
QUALITY_TIER_MIN_PIXELS = {"draft": 0, "standard": 250_000, "premium": 1_000_000}


@dataclass
class AssetGenerationConfig:
    """Operational configuration of the Universal Asset Generation Engine."""

    # Provider selection.
    selection_strategy: str = "balanced"        # SELECTION_STRATEGIES
    provider_priority: dict = field(default_factory=dict)  # asset_class → ordered provider names
    offline_only: bool = False                  # restrict selection to offline providers

    # Cost limits (USD).
    max_cost_per_asset: float = 2.0
    max_cost_per_package: float = 25.0

    # Output defaults (used when a request doesn't specify its own).
    default_aspect_ratio: str = "9:16"
    default_resolutions: dict = field(
        default_factory=lambda: {
            "image": "1080x1920",
            "video": "1080x1920",
            "three_d": "1024x1024",
            "animation": "1080x1920",
            "audio": "0x0",
            "motion_graphics": "1080x1920",
        }
    )
    quality_tier: str = "standard"              # draft | standard | premium

    # Reliability.
    max_retries: int = 2                        # attempts per provider
    timeout_sec: int = 120

    # Safety & brand rules.
    safety_rules: list = field(
        default_factory=lambda: ["gore", "graphic violence", "nudity", "hate symbol"]
    )
    brand_rules: dict = field(
        default_factory=lambda: {"require_style": True, "banned_terms": []}
    )

    # Caching.
    cache_enabled: bool = True
    allow_placeholders: bool = True             # Demo Mode mock output allowed

    # Safety valve — never let one item explode into unlimited generation.
    max_assets_per_item: int = 80

    # Batch / queue (Phase 2).
    batch_concurrency: int = 4                  # max parallel workers for batch_generate
    usage_tracking_enabled: bool = True         # persist usage events to usage.json

    def to_dict(self) -> dict:
        return asdict(self)


_config: "AssetGenerationConfig | None" = None


def _load_overrides() -> dict:
    path = os.path.join(_DEFAULT_DIR, _CONFIG_FILE)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def get_asset_generation_config() -> AssetGenerationConfig:
    """The active configuration (defaults + JSON file overrides)."""
    global _config
    if _config is None:
        config = AssetGenerationConfig()
        for key, value in _load_overrides().items():
            if hasattr(config, key):
                setattr(config, key, value)
        _config = config
    return _config


def configure(**overrides) -> AssetGenerationConfig:
    """Apply runtime overrides (unknown keys are ignored)."""
    config = get_asset_generation_config()
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)
    return config


def reset_asset_generation_config() -> None:
    """Drop the cached config (tests + hot reloads)."""
    global _config
    _config = None
