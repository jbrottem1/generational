"""Audio finalization — enriches render audio_mix_plan with post-production polish."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.post_production.config import PostProductionConfig


def finalize_audio_mix(
    render_package: dict,
    audio_package: dict | None = None,
    config: "PostProductionConfig | None" = None,
) -> dict:
    """Build final audio mix plan from render audio_mix_plan + audio_package."""
    from services.post_production.config import LOUDNESS_TARGETS, get_post_production_config

    config = config or get_post_production_config()
    source_plan = render_package.get("audio_mix_plan") or {}
    audio_package = audio_package or {}

    platforms = config.target_platforms or ["youtube_shorts"]
    platform_targets = {
        platform: {"integrated_lufs": LOUDNESS_TARGETS.get(platform, -14.0)}
        for platform in platforms
    }

    ducking = source_plan.get("ducking") or {}
    if not config.enable_music_ducking:
        ducking = {"enabled": False}

    return {
        "source_plan": "render.audio_mix_plan",
        "dialogue_level_db": source_plan.get("track_levels_db", {}).get("narration", -3.0),
        "music_level_db": source_plan.get("track_levels_db", {}).get("music", -18.0),
        "sfx_level_db": source_plan.get("track_levels_db", {}).get("sfx", -10.0),
        "ducking": ducking,
        "normalization": {
            "enabled": True,
            "target_lufs": LOUDNESS_TARGETS.get(platforms[0], -14.0),
            "true_peak_db": -1.0,
        },
        "loudness_target": source_plan.get("loudness_target") or {
            "integrated_lufs": -14.0,
            "true_peak_db": -1.0,
        },
        "fade_in_sec": 0.3,
        "fade_out_sec": 0.5,
        "effects": {
            "compression": {"enabled": True, "ratio": 3.0, "threshold_db": -18.0},
            "eq": {"enabled": True, "high_pass_hz": 80, "presence_boost_db": 2.0},
            "limiter": {"enabled": True, "ceiling_db": -1.0},
            "noise_reduction": {"enabled": True, "strength": 0.3},
        },
        "platform_targets": platform_targets,
    }
