"""Module 10 — Export Pipeline: platform presets, codec, bitrate."""

from __future__ import annotations

from services.studio_render.models import EXPORT_PRESETS

PRESET_SPECS: dict[str, dict] = {
    "youtube_shorts": {
        "aspect": "9:16",
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "codec": "h264",
        "bitrate_kbps": 12_000,
        "audio_bitrate_kbps": 192,
        "hdr_ready": False,
    },
    "tiktok": {
        "aspect": "9:16",
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "codec": "h264",
        "bitrate_kbps": 10_000,
        "audio_bitrate_kbps": 192,
        "hdr_ready": False,
    },
    "instagram_reels": {
        "aspect": "9:16",
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "codec": "h264",
        "bitrate_kbps": 10_000,
        "audio_bitrate_kbps": 192,
        "hdr_ready": False,
    },
    "facebook_reels": {
        "aspect": "9:16",
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "codec": "h264",
        "bitrate_kbps": 9_000,
        "audio_bitrate_kbps": 160,
        "hdr_ready": False,
    },
    "youtube_longform": {
        "aspect": "16:9",
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "codec": "h264",
        "bitrate_kbps": 16_000,
        "audio_bitrate_kbps": 256,
        "hdr_ready": True,
    },
    "landscape_1080p": {
        "aspect": "16:9",
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "codec": "h264",
        "bitrate_kbps": 14_000,
        "audio_bitrate_kbps": 224,
        "hdr_ready": True,
    },
    "landscape_4k": {
        "aspect": "16:9",
        "width": 3840,
        "height": 2160,
        "fps": 30,
        "codec": "h264",
        "bitrate_kbps": 45_000,
        "audio_bitrate_kbps": 320,
        "hdr_ready": True,
    },
    "square_1080": {
        "aspect": "1:1",
        "width": 1080,
        "height": 1080,
        "fps": 30,
        "codec": "h264",
        "bitrate_kbps": 10_000,
        "audio_bitrate_kbps": 192,
        "hdr_ready": False,
    },
    "vertical_1080": {
        "aspect": "9:16",
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "codec": "h264",
        "bitrate_kbps": 12_000,
        "audio_bitrate_kbps": 192,
        "hdr_ready": False,
    },
    "vertical_4k": {
        "aspect": "9:16",
        "width": 2160,
        "height": 3840,
        "fps": 60,
        "codec": "h264",
        "bitrate_kbps": 50_000,
        "audio_bitrate_kbps": 320,
        "hdr_ready": True,
    },
}


def choose_primary_preset(candidate: dict) -> str:
    platform = str(
        candidate.get("platform")
        or candidate.get("publishing_platform")
        or (candidate.get("seo") or {}).get("platform")
        or ""
    ).lower()
    aspect = str(
        (candidate.get("visual_package") or {}).get("aspect_ratio")
        or candidate.get("aspect_ratio")
        or "9:16"
    )
    if "tiktok" in platform:
        return "tiktok"
    if "instagram" in platform or "reels" in platform:
        return "instagram_reels"
    if "facebook" in platform:
        return "facebook_reels"
    if "long" in platform or aspect in ("16:9", "16/9"):
        return "youtube_longform"
    if aspect in ("1:1", "1/1"):
        return "square_1080"
    return "youtube_shorts"


def build_export_plan(candidate: dict) -> dict:
    primary = choose_primary_preset(candidate)
    assert primary in EXPORT_PRESETS
    primary_spec = dict(PRESET_SPECS[primary])

    # Also prepare sibling platform variants for Shorts-family
    siblings = []
    if primary_spec["aspect"] == "9:16":
        for key in ("youtube_shorts", "tiktok", "instagram_reels", "facebook_reels"):
            if key != primary:
                siblings.append({"preset": key, **PRESET_SPECS[key]})

    return {
        "primary_preset": primary,
        "primary": {"preset": primary, **primary_spec},
        "variants": siblings,
        "auto_bitrate": True,
        "auto_codec": True,
        "hdr_pipeline": bool(primary_spec.get("hdr_ready")),
        "container": "mp4",
        "reason": f"Platform/aspect selected preset: {primary}",
    }
