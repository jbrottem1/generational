"""Output format presets — aspect ratios, resolutions, and duration bands.

Used by the render assembler and Studio settings. Defaults remain 9:16
vertical shorts so existing packages stay compatible.
"""

from __future__ import annotations

from typing import Any

# Aspect → default resolution (width, height)
RESOLUTION_PRESETS: dict[str, dict[str, Any]] = {
    "vertical": {
        "aspect_ratio": "9:16",
        "resolution": {"width": 1080, "height": 1920},
        "orientation": "vertical",
        "platforms": ["youtube_shorts", "tiktok", "instagram_reels", "facebook_reels"],
    },
    "landscape": {
        "aspect_ratio": "16:9",
        "resolution": {"width": 1920, "height": 1080},
        "orientation": "landscape",
        "platforms": ["youtube", "facebook", "linkedin", "x"],
    },
    "square": {
        "aspect_ratio": "1:1",
        "resolution": {"width": 1080, "height": 1080},
        "orientation": "square",
        "platforms": ["instagram", "facebook", "linkedin"],
    },
}

# Named duration targets (seconds) — pipeline supports all via timeline length
DURATION_PRESETS: dict[str, float] = {
    "1s": 1.0,
    "10s": 10.0,
    "30s": 30.0,
    "60s": 60.0,
    "5m": 300.0,
    "30m": 1800.0,
    "1h": 3600.0,
    "6h": 21600.0,
    "12h": 43200.0,
    "24h": 86400.0,
}

SUPPORTED_DURATION_SEC = tuple(DURATION_PRESETS.values())


def resolve_output_format(
    *,
    aspect: str = "",
    width: int = 0,
    height: int = 0,
    fps: int = 30,
) -> dict[str, Any]:
    """Build an OUTPUT_FORMAT-compatible dict from aspect or custom size."""
    key = (aspect or "vertical").strip().lower().replace(" ", "_")
    aliases = {
        "9:16": "vertical",
        "shorts": "vertical",
        "tiktok": "vertical",
        "reels": "vertical",
        "16:9": "landscape",
        "youtube": "landscape",
        "1:1": "square",
        "instagram": "square",
    }
    key = aliases.get(key, key)
    if width > 0 and height > 0:
        if width == height:
            orientation = "square"
            aspect_ratio = "1:1"
        elif height > width:
            orientation = "vertical"
            aspect_ratio = "9:16"
        else:
            orientation = "landscape"
            aspect_ratio = "16:9"
        preset = {
            "aspect_ratio": aspect_ratio,
            "resolution": {"width": int(width), "height": int(height)},
            "orientation": orientation,
            "platforms": RESOLUTION_PRESETS.get(orientation, RESOLUTION_PRESETS["vertical"])["platforms"],
        }
    else:
        preset = dict(RESOLUTION_PRESETS.get(key) or RESOLUTION_PRESETS["vertical"])

    return {
        "aspect_ratio": preset["aspect_ratio"],
        "resolution": dict(preset["resolution"]),
        "container": "mp4",
        "video_codec": "h264",
        "audio_codec": "aac",
        "fps": int(fps or 30),
        "orientation": preset["orientation"],
        "platforms": list(preset["platforms"]),
    }


def duration_band(duration_sec: float) -> str:
    """Nearest named duration band for reporting."""
    if duration_sec <= 0:
        return "unknown"
    best = min(DURATION_PRESETS.items(), key=lambda item: abs(item[1] - duration_sec))
    return best[0]
