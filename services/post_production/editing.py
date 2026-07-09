"""Intelligent editing — pacing, jump cuts, dead space, engagement timing."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.post_production.config import PostProductionConfig

# Pacing multipliers per editing style (lower = tighter cuts).
_PACING_FACTORS = {
    "fast_paced": 0.85,
    "documentary": 1.0,
    "educational": 1.05,
    "comedy": 0.9,
    "cinematic": 1.1,
    "retention": 0.88,
}

# Dead space thresholds per pacing profile.
_DEAD_SPACE = {
    "aggressive": 0.25,
    "balanced": 0.4,
    "conservative": 0.6,
}


def compute_scene_cuts(
    render_package: dict,
    audio_package: dict | None = None,
    config: "PostProductionConfig | None" = None,
) -> list:
    """Apply intelligent editing decisions to render timeline segments."""
    from services.post_production.config import get_post_production_config

    config = config or get_post_production_config()
    timeline = render_package.get("timeline") or {}
    segments = timeline.get("segments") or []
    audio_package = audio_package or {}

    pacing_factor = _PACING_FACTORS.get(config.editing_style, 0.9)
    dead_threshold = _DEAD_SPACE.get(config.pacing_profile, 0.4)
    if config.dead_space_threshold_sec:
        dead_threshold = config.dead_space_threshold_sec

    scene_cues = {
        cue.get("scene_number", 0): cue
        for cue in audio_package.get("scene_cues", [])
    }

    cuts = []
    for segment in segments:
        scene_id = segment.get("scene_id", 0)
        orig_start = float(segment.get("start_time", 0.0))
        orig_end = float(segment.get("end_time", 0.0))
        duration = float(segment.get("duration", orig_end - orig_start))

        edited_start = orig_start
        edited_end = orig_end
        cut_type = "hold"
        reason = "no_adjustment"
        pacing_score = 80

        # Dead space removal — trim silence at scene boundaries.
        if config.enable_dead_space_removal and duration > dead_threshold + config.min_scene_duration_sec:
            trim = min(dead_threshold * pacing_factor, duration * 0.1)
            edited_start = orig_start + trim
            edited_end = orig_end - trim * 0.5
            cut_type = "trim"
            reason = "dead_space_removal"
            pacing_score = 85

        # Jump cuts for retention/fast-paced styles.
        if config.enable_jump_cuts and config.editing_style in ("fast_paced", "retention", "comedy"):
            cue = scene_cues.get(scene_id, {})
            if cue.get("energy", 0) > 70 or segment.get("motion_effect") == "zoom":
                cut_type = "jump_cut"
                reason = "engagement_pacing"
                pacing_score = 90

        # Comedy timing — hold slightly longer on punchlines.
        if config.editing_style == "comedy":
            cue = scene_cues.get(scene_id, {})
            if cue.get("purpose") == "payoff" or "punchline" in str(cue.get("notes", "")).lower():
                edited_end = min(edited_end + 0.3, orig_end)
                cut_type = "hold"
                reason = "comedy_timing"
                pacing_score = 88

        # Educational pacing — ensure minimum comprehension time.
        if config.editing_style == "educational":
            min_dur = max(config.min_scene_duration_sec, 2.0)
            if (edited_end - edited_start) < min_dur:
                edited_end = edited_start + min_dur
                cut_type = "hold"
                reason = "educational_pacing"
                pacing_score = 82

        cuts.append({
            "scene_id": scene_id,
            "original_start": round(orig_start, 3),
            "original_end": round(orig_end, 3),
            "edited_start": round(edited_start, 3),
            "edited_end": round(edited_end, 3),
            "cut_type": cut_type,
            "reason": reason,
            "pacing_score": pacing_score,
        })

    return cuts
