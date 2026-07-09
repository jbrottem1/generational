"""Animation configuration — every operational knob in one place.

Same convention as Asset Generation / Market Intelligence: one dataclass,
JSON overrides from `data/animation/config.json`, `configure()` for runtime
overrides, `reset_animation_config()` for tests.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field

_DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "animation",
)
_CONFIG_FILE = "config.json"

QUALITY_TIERS = ("draft", "standard", "premium", "cinematic")
CAMERA_STYLES = (
    "documentary", "cinematic", "handheld", "static", "dynamic", "anime", "explainer",
)
ANIMATION_STYLES = (
    "live_action_hybrid", "2d", "3d", "anime", "cartoon", "motion_graphics",
    "educational", "cinematic",
)
MOTION_INTENSITIES = ("subtle", "moderate", "high", "extreme")


@dataclass
class AnimationConfig:
    """Operational configuration of the Animation Engine."""

    animation_quality: str = "standard"          # QUALITY_TIERS
    motion_intensity: str = "moderate"           # MOTION_INTENSITIES
    camera_style: str = "cinematic"              # CAMERA_STYLES
    animation_style: str = "cinematic"           # ANIMATION_STYLES
    fps: int = 30
    target_platform: str = "youtube_shorts"
    target_duration_sec: float = 0.0             # 0 → derive from scenes
    target_aspect_ratio: str = "9:16"
    motion_smoothing: float = 0.65               # 0-1 bezier smoothing bias
    enable_lip_sync: bool = True
    enable_facial: bool = True
    enable_vfx: bool = True
    enable_motion_graphics: bool = True
    parallel_planning: bool = True
    max_scenes_per_package: int = 500            # multi-hour safe upper bound
    default_transition: str = "cut"
    provider_priority: list = field(
        default_factory=lambda: [
            "runway", "google_veo", "kling", "pika", "luma",
            "pixverse", "stable_video", "openai", "mock_animation",
        ]
    )

    def to_dict(self) -> dict:
        return asdict(self)


_config: "AnimationConfig | None" = None


def _load_overrides() -> dict:
    path = os.path.join(_DEFAULT_DIR, _CONFIG_FILE)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def get_animation_config() -> AnimationConfig:
    global _config
    if _config is None:
        overrides = _load_overrides()
        known = {key: value for key, value in overrides.items() if key in AnimationConfig.__dataclass_fields__}
        _config = AnimationConfig(**known)
    return _config


def configure(**overrides) -> AnimationConfig:
    """Apply runtime overrides and return the active config."""
    global _config
    base = get_animation_config().to_dict()
    base.update({key: value for key, value in overrides.items() if key in AnimationConfig.__dataclass_fields__})
    _config = AnimationConfig(**base)
    return _config


def reset_animation_config() -> None:
    global _config
    _config = None
