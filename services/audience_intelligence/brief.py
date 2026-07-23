"""Pre-production Creative Brief — guides existing systems; does not replace them."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.audience_intelligence.builder import analyze_topic
from services.audience_intelligence.memory import BRIEF_DIR, ensure_dirs, search_lessons, seed_bootstrap_lessons


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_creative_brief(
    *,
    topic: str,
    niche: str = "",
    platform: str = "youtube_shorts",
    audience: str = "general_public",
    length_sec: int = 45,
    narrator: str = "professor",
    production_id: str = "",
) -> dict[str, Any]:
    """Generate a Creative Brief from topic analysis + creative memory lessons."""
    seed_bootstrap_lessons()
    report = analyze_topic(topic, category=niche or "general")
    payload = report.to_dict() if hasattr(report, "to_dict") else dict(report)
    creative = payload.get("creative") or {}
    engagement = payload.get("engagement") or {}
    psych = payload.get("psychological_drivers") or {}

    lessons = search_lessons(topic, platform=platform, niche=niche, limit=8)
    niche_lessons = search_lessons(niche or topic, platform=platform, niche=niche, limit=6)
    # Dedup by lesson_id
    seen = set()
    merged = []
    for lesson in lessons + niche_lessons:
        lid = lesson.get("lesson_id")
        if lid in seen:
            continue
        seen.add(lid)
        merged.append(lesson)

    hook_lessons = [l for l in merged if l.get("category") in ("hook_patterns", "curiosity_gaps")]
    visual_lessons = [l for l in merged if l.get("category") in ("visual_pacing", "camera_movement_styles", "scene_density")]
    narr_lessons = [l for l in merged if l.get("category") == "narration_styles"]
    thumb_lessons = [l for l in merged if l.get("category") == "thumbnail_characteristics"]
    caption_lessons = [l for l in merged if l.get("category") == "caption_styles"]

    opening = creative.get("suggested_opening_hook") or ""
    if hook_lessons and (not opening or len(opening) < 12):
        opening = f"Stop — most people misunderstand {topic.split()[0] if topic else 'this'}. Here's the part that changes everything."

    # Map pacing from engagement + lessons
    pacing = "fast_open_then_pause_reveal"
    if float(engagement.get("retention_probability") or 50) < 55:
        pacing = "aggressive_cut_rate_first_15s"
    if any("2–3.5" in str(l.get("statement") or "") or "2-3.5" in str(l.get("statement") or "") for l in visual_lessons):
        visual_density = "change_every_2_to_3_5_seconds_in_open"
    else:
        visual_density = "medium_high_documentary_layers"

    camera_style = "motivated_push_in_and_orbit"
    if any("zoom" in str(l.get("statement") or "").lower() for l in visual_lessons):
        camera_style = "fast_push_in_on_hook_then_orbit_reveal"

    narration_rec = f"{narrator} educational science — stress hook + punchline; calmer body copy"
    if narr_lessons:
        narration_rec = f"{narr_lessons[0].get('statement')} (confidence={narr_lessons[0].get('confidence')})"

    caption_rec = "Punch hook keywords in first 3s; keep lines ≤2 on-screen"
    if caption_lessons:
        caption_rec = str(caption_lessons[0].get("statement"))

    thumb_strategy = creative.get("best_thumbnail_style") or "bold_subject_plus_short_claim"
    if thumb_lessons:
        thumb_strategy = str(thumb_lessons[0].get("statement"))

    weak_points = []
    if float(psych.get("curiosity_potential") or 50) < 65:
        weak_points.append("Curiosity gap may be weak — confront a wrong belief in 0–3s")
    if float(engagement.get("retention_probability") or 50) < 60:
        weak_points.append("Retention risk mid-video — schedule a pattern interrupt ~40–50%")
    if not weak_points:
        weak_points.append("Watch for slideshow lock — keep motion + world continuity alive every beat")

    brief = {
        "package_type": "audience_intelligence_creative_brief",
        "version": "2.0.0",
        "generated_at": _now(),
        "topic": topic,
        "niche": niche,
        "platform": platform,
        "audience": audience,
        "length_sec": length_sec,
        "production_id": production_id,
        "recommended_opening_hook": opening or creative.get("suggested_opening_hook"),
        "ideal_pacing": pacing,
        "recommended_visual_density": visual_density,
        "suggested_camera_style": camera_style,
        "narration_recommendations": narration_rec,
        "caption_recommendations": caption_rec,
        "thumbnail_strategy": thumb_strategy,
        "predicted_viewer_expectations": {
            "human_attention_score": payload.get("human_attention_score"),
            "retention_probability": engagement.get("retention_probability"),
            "shareability": engagement.get("shareability"),
            "format": creative.get("recommended_video_format"),
            "length_sec": creative.get("recommended_video_length_sec"),
            "persona": (payload.get("audience_profile") or {}).get("persona_summary"),
        },
        "potential_weak_points": weak_points,
        "psychological_hooks": creative.get("psychological_hooks") or [],
        "supporting_lessons": [
            {
                "lesson_id": l.get("lesson_id"),
                "statement": l.get("statement"),
                "confidence": l.get("confidence"),
                "category": l.get("category"),
                "evidence_count": len(l.get("evidence") or []),
            }
            for l in merged[:8]
        ],
        "audience_intelligence_report": {
            "human_attention_score": payload.get("human_attention_score"),
            "confidence": payload.get("confidence"),
            "reasoning": payload.get("reasoning"),
        },
        "guides_systems": [
            "script_generation",
            "scene_builder",
            "world_builder",
            "cinematic_director",
            "voice_studio",
            "publishing_intelligence",
        ],
        "does_not_replace": [
            "psychology_engine",
            "research_engine",
            "creative_performance_lab",
            "publishing_intelligence",
            "renderer",
        ],
        "note": "Advisory brief only — existing production systems remain authoritative",
    }

    ensure_dirs()
    slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in topic)[:48] or "brief"
    path = BRIEF_DIR / f"{slug}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(brief, indent=2) + "\n", encoding="utf-8")
    brief["path"] = str(path)
    return brief


def attach_brief_to_candidate(candidate: dict[str, Any], brief: dict[str, Any]) -> dict[str, Any]:
    """Additive attach — does not overwrite psychology / CPL packages."""
    out = dict(candidate)
    out["audience_intelligence_brief"] = brief
    # Soft hints for systems that already read preferred_* keys
    out.setdefault("preferred_hook_strategy", "curiosity_gap")
    out.setdefault("force_strong_hook", True)
    out.setdefault("prefer_motion", True)
    out.setdefault("cinematic_priority", True)
    if brief.get("recommended_opening_hook"):
        out.setdefault("hook", brief["recommended_opening_hook"])
        out.setdefault("suggested_opening_hook", brief["recommended_opening_hook"])
    return out
