"""Visual Production Package — the complete visual plan for one idea.

Assembles everything the downstream renderers (voice → audio → video) will
consume: storyboard, full scene list, per-model AI image and video prompts,
five scored thumbnail concepts, a timed caption plan, pacing / camera /
transition / motion reports, the five-frame hook sequence, and one weighted
Overall Visual Score (0-100) with a plain-English summary.
"""

from __future__ import annotations

from engines.heuristics import clamp
from services.visual.hooks import build_hook_sequence
from services.visual.prompts import build_image_prompts, build_video_prompts
from services.visual.scenes import palette_for, plan_scenes
from services.visual.thumbnails import build_thumbnail_concepts

# How much each component contributes to the package's Overall Visual Score.
# Scene craft and the hook window dominate because they decide retention;
# thumbnails decide the impression. Sum == 1.0.
PACKAGE_SCORE_WEIGHTS = {
    "scene_visuals": 0.35,
    "hook_strength": 0.25,
    "thumbnail_power": 0.20,
    "pacing_fitness": 0.12,
    "camera_variety": 0.08,
}

# Ideal average scene length window (seconds) for short-form retention.
IDEAL_SCENE_SEC_LOW = 3.0
IDEAL_SCENE_SEC_HIGH = 8.0

MOTION_LEVELS = ((70, "high"), (45, "medium"), (0, "low"))


def _motion_level(value: float) -> str:
    for threshold, label in MOTION_LEVELS:
        if value >= threshold:
            return label
    return MOTION_LEVELS[-1][1]


def build_storyboard(scenes: list) -> list:
    """Compact, human-readable board — one panel per scene."""
    return [
        {
            "panel": scene["scene_number"],
            "purpose": scene["purpose"],
            "length_sec": scene["length_sec"],
            "description": scene["visual_description"],
            "camera": f"{scene['camera_angle']} · {scene['camera_motion']}",
            "text_overlay": scene["text_overlay"],
        }
        for scene in scenes
    ]


def build_caption_plan(scenes: list) -> list:
    """Timed caption segments — one per scene, ready for subtitle rendering."""
    return [
        {
            "scene_number": scene["scene_number"],
            "start_sec": scene["caption_timing"]["start_sec"],
            "end_sec": scene["caption_timing"]["end_sec"],
            "text": scene["narration"],
            "overlay": scene["text_overlay"],
            "style": "bold word-by-word pop, high-contrast stroke, safe-zone bottom third",
        }
        for scene in scenes
    ]


def build_pacing_report(scenes: list) -> dict:
    """Visual pacing diagnostics — cut rhythm against the retention ideal."""
    lengths = [scene["length_sec"] for scene in scenes] or [0]
    total = sum(lengths)
    average = round(total / len(lengths), 1)
    cuts_per_10s = round((len(scenes) / total) * 10, 1) if total else 0.0

    if average < IDEAL_SCENE_SEC_LOW:
        verdict = "frenetic — consider merging the shortest beats"
    elif average > IDEAL_SCENE_SEC_HIGH:
        verdict = "slow — split long beats or add mid-scene visual switches"
    else:
        verdict = "on target for short-form retention"

    deviation = 0.0
    if average < IDEAL_SCENE_SEC_LOW:
        deviation = IDEAL_SCENE_SEC_LOW - average
    elif average > IDEAL_SCENE_SEC_HIGH:
        deviation = average - IDEAL_SCENE_SEC_HIGH
    fitness = clamp(95 - deviation * 12, low=10, high=95)

    return {
        "scene_count": len(scenes),
        "total_runtime_sec": round(total, 1),
        "average_scene_sec": average,
        "cuts_per_10s": cuts_per_10s,
        "scene_lengths_sec": lengths,
        "verdict": verdict,
        "pacing_fitness": fitness,
    }


def build_camera_plan(scenes: list) -> dict:
    """Per-scene camera plan plus a variety score (repetition kills attention)."""
    shots = [
        {
            "scene_number": scene["scene_number"],
            "angle": scene["camera_angle"],
            "motion": scene["camera_motion"],
            "zoom": scene["zoom"],
            "composition": scene["shot_composition"],
        }
        for scene in scenes
    ]
    combos = [f"{shot['angle']}|{shot['motion']}" for shot in shots]
    variety = clamp((len(set(combos)) / len(combos)) * 100, low=10, high=98) if combos else 0
    return {"shots": shots, "variety_score": variety}


def build_motion_report(scenes: list) -> dict:
    """Motion energy across the video — average, peak, and per-scene curve."""
    intensities = [scene["motion_intensity"] for scene in scenes] or [0]
    average = round(sum(intensities) / len(intensities), 1)
    peak_scene = max(scenes, key=lambda scene: scene["motion_intensity"]) if scenes else {}
    return {
        "average_intensity": average,
        "level": _motion_level(average),
        "peak_scene_number": peak_scene.get("scene_number", 0),
        "peak_intensity": max(intensities),
        "curve": [
            {"scene_number": scene["scene_number"], "intensity": scene["motion_intensity"]}
            for scene in scenes
        ],
    }


def build_transitions(scenes: list) -> list:
    return [
        {
            "from_scene": scene["scene_number"],
            "to_scene": scene["scene_number"] + 1,
            "transition": scene["transition_out"],
        }
        for scene in scenes[:-1]
    ]


def overall_visual_score(components: dict) -> int:
    """Single weighted 0-100 score from the package components."""
    return clamp(
        sum(components[key] * weight for key, weight in PACKAGE_SCORE_WEIGHTS.items()),
        low=0,
        high=100,
    )


def build_visual_package(
    idea: dict,
    *,
    niche: str = "",
    subject: str = "",
    aspect_ratio: str = "9:16",
) -> dict:
    """Full Visual Production Package for one scripted idea (JSON-safe dict)."""
    palette = palette_for(niche)
    scene_plans = plan_scenes(idea, niche=niche, subject=subject)
    scenes = [scene.to_dict() for scene in scene_plans]

    thumbnails = [concept.to_dict() for concept in build_thumbnail_concepts(idea, palette=palette)]
    hook_sequence = build_hook_sequence(idea, subject=subject)
    pacing = build_pacing_report(scenes)
    camera_plan = build_camera_plan(scenes)
    motion_report = build_motion_report(scenes)

    scene_scores = [scene["visual_score"] for scene in scenes] or [0]
    hook_scene = next((scene for scene in scenes if scene["purpose"] == "hook"), None)
    components = {
        "scene_visuals": round(sum(scene_scores) / len(scene_scores), 1),
        "hook_strength": hook_scene["visual_score"] if hook_scene else 40,
        "thumbnail_power": thumbnails[0]["overall"] if thumbnails else 40,
        "pacing_fitness": pacing["pacing_fitness"],
        "camera_variety": camera_plan["variety_score"],
    }
    score = overall_visual_score(components)

    label = idea.get("title") or idea.get("hook") or "This idea"
    summary = (
        f"\"{label}\" — Visual Score {score}/100 across {len(scenes)} scenes. "
        f"Pacing: {pacing['verdict']}. Motion: {motion_report['level']}. "
        f"Best thumbnail: {thumbnails[0]['label']} ({thumbnails[0]['expected_ctr_pct']}% expected CTR)."
        if thumbnails
        else f"\"{label}\" — Visual Score {score}/100 across {len(scenes)} scenes."
    )

    return {
        "visual_score": score,
        "score_components": components,
        "summary": summary,
        "aspect_ratio": aspect_ratio,
        "color_palette": palette,
        "storyboard": build_storyboard(scenes),
        "scenes": scenes,
        "image_prompts": build_image_prompts(scenes, niche=niche, aspect_ratio=aspect_ratio),
        "video_prompts": build_video_prompts(scenes, niche=niche, aspect_ratio=aspect_ratio),
        "thumbnails": thumbnails,
        "hook_sequence": hook_sequence,
        "caption_plan": build_caption_plan(scenes),
        "pacing_report": pacing,
        "camera_plan": camera_plan,
        "transitions": build_transitions(scenes),
        "motion_report": motion_report,
    }
