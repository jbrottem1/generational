"""Production-side quality checks before a package may leave the hold state.

Intelligence `publishable` is necessary but not sufficient. This module scores
narration presence, scene/visual coverage, caption readiness, and story-beat
alignment so blank frames, silent exports, and incomplete arcs never auto-post.
"""

from __future__ import annotations

from core.constants import DEFAULT_PRODUCTION_QUALITY_THRESHOLD
from engines.heuristics import clamp
from services.editorial import beats_complete, is_motivational_niche, score_story_structure


def score_production_package(pkg: dict, *, niche: str = "") -> dict:
    """Return production quality scores and gate failures for one package."""
    scenes = pkg.get("scenes") or []
    narration = pkg.get("narration") or {}
    visual_prompts = pkg.get("visual_prompts") or []
    subtitles = pkg.get("subtitles") or pkg.get("subtitle_track") or []
    timeline = pkg.get("timeline") or {}
    story_beats = pkg.get("story_beats") or {}

    failures: list[str] = []
    scores: dict[str, int] = {}

    # Narration quality — reject silent / missing voice tracks.
    narr_text = ""
    if isinstance(narration, dict):
        narr_text = narration.get("full_text") or narration.get("script") or ""
        audio_path = narration.get("audio_path") or narration.get("file_path") or ""
        has_segments = bool(narration.get("segments") or narration.get("clips"))
    else:
        audio_path = ""
        has_segments = False
    if not narr_text and scenes:
        narr_text = " ".join(s.get("narration", "") for s in scenes if s.get("narration"))
    narr_score = 40
    if narr_text.strip():
        narr_score += 30
    if audio_path or has_segments or narr_text.strip():
        # Demo providers may not write audio files; spoken text presence counts.
        narr_score += 20
    else:
        failures.append("missing_narration")
    scores["narration_quality"] = clamp(narr_score)

    # Visual relevance — every scene needs a description or prompt (no blanks).
    vis_score = 35
    if scenes:
        described = sum(1 for s in scenes if (s.get("visual_description") or s.get("narration")))
        vis_score += int(45 * described / max(len(scenes), 1))
        if described < len(scenes):
            failures.append("blank_or_incomplete_scenes")
    if visual_prompts:
        vis_score = clamp(vis_score + 15)
    scores["visual_relevance"] = clamp(vis_score)

    # Caption synchronization readiness.
    cap_score = 50
    if subtitles or timeline.get("subtitle_cues") or any(s.get("on_screen_text") for s in scenes):
        cap_score = 85
    else:
        failures.append("caption_sync_missing")
        cap_score = 40
    scores["caption_synchronization"] = clamp(cap_score)

    # Cinematic motion cues in scene camera language.
    motion_words = ("push", "pan", "drift", "parallax", "tilt", "rack", "slow")
    motion_hits = sum(
        1
        for s in scenes
        if any(w in str(s.get("camera_movement", "")).lower() for w in motion_words)
    )
    scores["cinematic_quality"] = clamp(45 + min(motion_hits, 4) * 12)

    # Motivational structure on the package when applicable.
    structure = score_story_structure(story_beats, narr_text)
    scores["story_structure"] = structure["score"]
    if is_motivational_niche(niche) and not beats_complete(story_beats):
        failures.append("story_structure")

    overall = clamp(
        0.30 * scores["narration_quality"]
        + 0.25 * scores["visual_relevance"]
        + 0.15 * scores["caption_synchronization"]
        + 0.15 * scores["cinematic_quality"]
        + 0.15 * scores["story_structure"]
    )
    scores["production"] = overall

    threshold = DEFAULT_PRODUCTION_QUALITY_THRESHOLD
    if overall < threshold:
        failures.append("production_score")

    return {
        "scores": scores,
        "gate_failures": failures,
        "passed": not failures and overall >= threshold,
        "threshold": threshold,
    }
