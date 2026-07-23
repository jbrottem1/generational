"""V2 Creative Quality — craft scores for documentary-grade Shorts.

Extends Creative Excellence without new engines. Measures watchability:
visual / motion / storytelling / clarity / hook / retention / audio / polish.
"""

from __future__ import annotations

from typing import Any

# Mission-required post-production scores
V2_CRAFT_DIMENSIONS = (
    "visual_quality",
    "motion_quality",
    "storytelling",
    "educational_clarity",
    "hook",
    "viewer_retention",
    "audio_quality",
    "overall_professionalism",
)

DOCUMENTARY_STANDARD = (
    "animated_or_layered_environments",
    "foreground_background_motion",
    "cinematic_depth",
    "motivated_camera_moves",
    "realistic_or_motivated_lighting",
    "environmental_effects",
    "object_or_subject_interaction",
    "believable_persistent_world",
    "no_slideshow_lock",
)


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return float(max(low, min(high, value)))


def build_v2_quality_block(
    candidate: dict | None = None,
    *,
    production_report: dict | None = None,
    timeline: dict | None = None,
    craft: dict | None = None,
    dimensions: dict | None = None,
) -> dict[str, Any]:
    """Score V2 craft dimensions from existing candidate + ops report signals."""
    candidate = dict(candidate or {})
    report = dict(production_report or {})
    segs = dict(timeline or {})
    craft = dict(craft or {})
    dims = dict(dimensions or {})

    vp = candidate.get("visual_package") or {}
    scenes = list(vp.get("scenes") or candidate.get("scenes") or [])
    world = candidate.get("world_package") or candidate.get("environment_package") or {}
    cinematic = candidate.get("cinematic_direction_package") or {}
    voice = candidate.get("voice_package") or {}

    # Visual quality — fidelity signals + scene richness + world presence
    visual = float(report.get("visual_score") or 65)
    if world.get("world_id") or world.get("environment_packages"):
        visual += 6
    if scenes and all((s.get("environment") or s.get("background")) for s in scenes if isinstance(s, dict)):
        visual += 4
    if any(isinstance(s, dict) and (s.get("image_path") or s.get("path")) for s in scenes):
        visual += 5
    # Slideshow penalty: all scenes lack camera/motion metadata
    if scenes:
        moving = sum(
            1
            for s in scenes
            if isinstance(s, dict)
            and (
                s.get("camera")
                or s.get("camera_motion")
                or s.get("movement_score")
                or (s.get("cinematic_direction") or {}).get("camera")
            )
        )
        if moving == 0:
            visual -= 12
        else:
            visual += min(8, moving * 2)

    # Motion quality
    motion = float(report.get("animation_score") or craft.get("visual_movement") or 60)
    shot_list = cinematic.get("shot_list") or []
    if shot_list:
        scores = [float(s.get("movement_score") or 0) for s in shot_list if isinstance(s, dict)]
        if scores:
            motion = 0.55 * motion + 0.45 * (sum(scores) / len(scores))
        staticish = sum(1 for s in scores if s < 30)
        if staticish >= max(1, len(scores) // 2):
            motion -= 10

    # Storytelling — hook→payoff arc
    storytelling = _clamp(
        0.35 * float(segs.get("first_3_seconds") or 60)
        + 0.25 * float(segs.get("first_15_seconds") or 60)
        + 0.20 * float(segs.get("middle_pacing") or 60)
        + 0.20 * float(segs.get("ending") or craft.get("payoff") or 60)
    )

    # Educational clarity
    educational_clarity = _clamp(
        float(report.get("educational_accuracy") or dims.get("educational_value") or 75)
    )

    # Hook
    hook = _clamp(
        0.7 * float(report.get("hook_score") or segs.get("first_3_seconds") or 60)
        + 0.3 * float(craft.get("curiosity") or 60)
    )

    # Retention
    viewer_retention = _clamp(
        float(report.get("retention_prediction") or dims.get("viewer_retention") or segs.get("first_15_seconds") or 65)
    )

    # Audio
    audio = float(report.get("audio_score") or report.get("narration_score") or 70)
    if voice.get("provider") == "elevenlabs" and not voice.get("placeholder"):
        audio = max(audio, 82)
        audio += 4
    if voice.get("placeholder") or str(voice.get("provider") or "") in ("demo", "mock", ""):
        if not voice.get("path"):
            audio -= 15

    overall = _clamp(
        0.18 * visual
        + 0.16 * motion
        + 0.14 * storytelling
        + 0.12 * educational_clarity
        + 0.14 * hook
        + 0.14 * viewer_retention
        + 0.12 * audio
    )

    scores = {
        "visual_quality": round(_clamp(visual), 1),
        "motion_quality": round(_clamp(motion), 1),
        "storytelling": round(storytelling, 1),
        "educational_clarity": round(educational_clarity, 1),
        "hook": round(hook, 1),
        "viewer_retention": round(viewer_retention, 1),
        "audio_quality": round(_clamp(audio), 1),
        "overall_professionalism": round(overall, 1),
    }

    # Documentary standard checklist (boolean signals)
    standards: dict[str, bool] = {
        "animated_or_layered_environments": bool(world) or motion >= 70,
        "foreground_background_motion": motion >= 68,
        "cinematic_depth": bool(cinematic.get("shot_list")) or visual >= 72,
        "motivated_camera_moves": bool(shot_list) and motion >= 65,
        "realistic_or_motivated_lighting": any(
            isinstance(s, dict) and (s.get("lighting") or (s.get("cinematic_direction") or {}).get("lighting"))
            for s in scenes
        )
        or bool(cinematic),
        "environmental_effects": bool((world.get("ambience_handoff") or world.get("background_animations"))),
        "object_or_subject_interaction": bool(
            (world.get("continuity") or {}).get("scene_bindings")
            or any(isinstance(s, dict) and s.get("world_direction") for s in scenes)
        ),
        "believable_persistent_world": bool(world.get("world_id") or world.get("continuity")),
        "no_slideshow_lock": motion >= 62 and hook >= 65,
    }
    passed = sum(1 for v in standards.values() if v)

    weakest = min(scores.items(), key=lambda kv: kv[1])
    return {
        "version": "2.0.0",
        "initiative": "generational_v2_creative_quality",
        "scores": scores,
        "documentary_standard": standards,
        "documentary_standard_passed": passed,
        "documentary_standard_total": len(DOCUMENTARY_STANDARD),
        "resembles_documentary_not_slideshow": passed >= 6 and scores["overall_professionalism"] >= 72,
        "weakest_craft": {"dimension": weakest[0], "score": weakest[1]},
        "targets": {
            "watch_time": "raise via hook + motion + payoff",
            "viewer_retention": "raise via first 3/15s + mid pacing",
            "visual_appeal": "raise via world continuity + lighting + depth",
            "professional_polish": "raise via audio sync + captions + transitions",
            "educational_clarity": "raise via display zones + one-idea-per-beat",
        },
    }


def pick_v2_craft_recommendation(v2: dict[str, Any], *, floor: float = 85.0) -> dict[str, Any] | None:
    """Optional V2-specific recommendation when craft lag exceeds timeline lag."""
    scores = dict((v2 or {}).get("scores") or {})
    if not scores:
        return None
    impact = {
        "hook": 100,
        "motion_quality": 90,
        "visual_quality": 88,
        "viewer_retention": 86,
        "storytelling": 82,
        "audio_quality": 78,
        "educational_clarity": 74,
        "overall_professionalism": 70,
    }
    prescriptions = {
        "hook": "Open on a concrete myth visual + ≤12-word spoken challenge in 0–3s; no definitions.",
        "motion_quality": "Mandate motivated push-in/orbit on every beat; forbid still full-frame holds >2.5s in the open.",
        "visual_quality": "Replace flat plates with layered observatory/world depth (FG subject + BG activity + practical lights).",
        "viewer_retention": "Insert one mid-runtime pattern interrupt (fact graphic + cut acceleration) before the retention cliff.",
        "storytelling": "Lock a 0–15s promise → mid complication → one-sentence payoff; cut anything that doesn't serve that arc.",
        "audio_quality": "Prefer human ElevenLabs contour on hook/punchline; duck music under narration; kill silent gaps.",
        "educational_clarity": "One scientific claim per beat with a persistent diagram/object that doesn't teleport between zones.",
        "overall_professionalism": "Unify grade, caption style, and world continuity so it reads as one documentary unit.",
    }
    cands = []
    for dim, score in scores.items():
        if float(score) >= floor:
            continue
        gap = floor - float(score)
        w = impact.get(dim, 50)
        cands.append(
            {
                "element": dim,
                "current_score": round(float(score), 1),
                "excellence_floor": floor,
                "gap": round(gap, 1),
                "impact_weight": w,
                "expected_retention_gain": round(w * (gap / 100.0), 2),
                "recommendation": prescriptions.get(dim, "Raise this craft signal only."),
                "why_this_ranks_first": "V2 craft dimension lagging documentary Shorts bar.",
                "mode": "improve",
                "source": "v2_creative_quality",
            }
        )
    if not cands:
        return None
    cands.sort(key=lambda c: (-c["expected_retention_gain"], -c["impact_weight"]))
    top = cands[0]
    top["principle"] = "Never suggest 20 improvements. Ship one highest-impact creative change."
    top["do_not_touch"] = [c["element"] for c in cands[1:5]]
    return top
