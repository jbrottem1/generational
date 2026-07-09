"""Configuration for the Post-Production Engine — all editing behavior is tunable."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

# Editing style presets.
EDITING_STYLES = ("fast_paced", "documentary", "educational", "comedy", "cinematic", "retention")

# Pacing profiles — how aggressively to trim dead space and apply jump cuts.
PACING_PROFILES = ("aggressive", "balanced", "conservative")

# Caption themes.
CAPTION_THEMES = ("bold_pop", "clean_minimal", "karaoke_highlight", "documentary_lower_third")

# Transition styles.
TRANSITION_STYLES = ("minimal", "dynamic", "cinematic")

# Color presets.
COLOR_PRESETS = ("neutral", "vibrant", "cinematic_warm", "documentary_cool", "brand")

# Platform loudness targets (LUFS integrated).
LOUDNESS_TARGETS = {
    "youtube": -14.0,
    "youtube_shorts": -14.0,
    "tiktok": -14.0,
    "instagram_reels": -14.0,
    "facebook": -16.0,
    "linkedin": -16.0,
    "x": -14.0,
    "default": -14.0,
}

# Supported export platforms.
SUPPORTED_PLATFORMS = (
    "youtube",
    "youtube_shorts",
    "tiktok",
    "instagram_reels",
    "facebook",
    "linkedin",
    "x",
)

# Export resolution presets.
EXPORT_PRESETS = {
    "1080p_vertical": {
        "resolution": {"width": 1080, "height": 1920},
        "aspect_ratio": "9:16",
        "orientation": "vertical",
    },
    "1080p_horizontal": {
        "resolution": {"width": 1920, "height": 1080},
        "aspect_ratio": "16:9",
        "orientation": "horizontal",
    },
    "1080p_square": {
        "resolution": {"width": 1080, "height": 1080},
        "aspect_ratio": "1:1",
        "orientation": "square",
    },
    "1440p_vertical": {
        "resolution": {"width": 1440, "height": 2560},
        "aspect_ratio": "9:16",
        "orientation": "vertical",
    },
    "4k_horizontal": {
        "resolution": {"width": 3840, "height": 2160},
        "aspect_ratio": "16:9",
        "orientation": "horizontal",
    },
    "4k_vertical": {
        "resolution": {"width": 2160, "height": 3840},
        "aspect_ratio": "9:16",
        "orientation": "vertical",
    },
    "archive_master": {
        "resolution": {"width": 3840, "height": 2160},
        "aspect_ratio": "16:9",
        "orientation": "horizontal",
        "hdr": True,
    },
    "proxy_720p": {
        "resolution": {"width": 1280, "height": 720},
        "aspect_ratio": "16:9",
        "orientation": "horizontal",
    },
}


@dataclass
class PostProductionConfig:
    """All tunable post-production behavior."""

    editing_style: str = "retention"
    pacing_profile: str = "balanced"
    caption_theme: str = "bold_pop"
    transition_style: str = "dynamic"
    color_preset: str = "vibrant"
    target_platforms: list = field(default_factory=lambda: ["youtube_shorts"])
    enable_jump_cuts: bool = True
    enable_dead_space_removal: bool = True
    enable_music_ducking: bool = True
    enable_motion_graphics: bool = True
    intro_length_sec: float = 1.5
    outro_length_sec: float = 3.0
    cta_timing_sec: float = 2.0
    dead_space_threshold_sec: float = 0.4
    min_scene_duration_sec: float = 1.0
    default_provider: str = "mock"
    batch_size: int = 10
    enable_caching: bool = True
    brand_lut: str = ""
    multi_language: list = field(default_factory=lambda: ["en"])


_config = PostProductionConfig()


def get_post_production_config() -> PostProductionConfig:
    return _config


def configure(**kwargs) -> PostProductionConfig:
    global _config
    valid = {k: v for k, v in kwargs.items() if hasattr(_config, k)}
    _config = replace(_config, **valid)
    return _config


def reset_post_production_config() -> PostProductionConfig:
    global _config
    _config = PostProductionConfig()
    return _config
