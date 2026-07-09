"""The Creative Director — every creative decision before a scene is boarded.

Interprets the script, selects the visual style, determines pacing,
cinematic language, and production complexity, chooses the storytelling
style, recommends production techniques, and emits one production
blueprint (CREATIVE_BLUEPRINT_FIELDS) the Storyboard Engine executes.

Deterministic by design (same convention as the rest of the OS): identical
input produces an identical blueprint, so tests, diagnostics, and the
learning loop can reason about creative decisions.
"""

from __future__ import annotations

from services.creative_studio.production_types import select_production_type
from services.creative_studio.styles import select_style
from services.creative_studio.worlds import select_world

# Pacing presets the Director chooses from — tempo drives scene length and
# cut frequency downstream (storyboard, motion plan, render timeline).
PACING_PRESETS = {
    "slow": {"tempo": "slow", "scene_target_sec": 8.0, "cuts_per_minute": 8},
    "measured": {"tempo": "measured", "scene_target_sec": 6.0, "cuts_per_minute": 10},
    "dynamic": {"tempo": "dynamic", "scene_target_sec": 4.0, "cuts_per_minute": 15},
    "rapid": {"tempo": "rapid", "scene_target_sec": 2.5, "cuts_per_minute": 24},
}

COMPLEXITY_LEVELS = ("simple", "standard", "advanced", "flagship")


def _split_script(item: dict) -> "list[str]":
    """Narration beats from the richest script source available."""
    breakdown = item.get("scene_breakdown") or []
    if breakdown:
        beats = [
            str(scene.get("narration") or scene.get("text") or scene.get("script") or "").strip()
            for scene in breakdown
            if isinstance(scene, dict)
        ]
        beats = [beat for beat in beats if beat]
        if beats:
            return beats

    script = str(
        item.get("script")
        or item.get("script_package", {}).get("script")
        or ""
    ).strip()
    if not script:
        return []
    sentences = [part.strip() for part in script.replace("\n", " ").split(".")]
    return [sentence for sentence in sentences if sentence]


def interpret_script(item: dict) -> dict:
    """What the script is, dramatically — premise, arc, key moments, curve."""
    beats = _split_script(item)
    hook = str(item.get("hook", "")).strip()
    premise = hook or (beats[0] if beats else str(item.get("topic", "")))

    key_moments = []
    if beats:
        key_moments.append({"position": "hook", "beat": beats[0]})
        if len(beats) > 2:
            key_moments.append({"position": "midpoint", "beat": beats[len(beats) // 2]})
        if len(beats) > 1:
            key_moments.append({"position": "payoff", "beat": beats[-1]})

    if len(beats) >= 5:
        arc = "hook → escalation → revelation → payoff"
        curve = ["curiosity", "tension", "surprise", "awe", "satisfaction"]
    elif len(beats) >= 3:
        arc = "hook → development → payoff"
        curve = ["curiosity", "tension", "satisfaction"]
    else:
        arc = "single statement"
        curve = ["curiosity"]

    return {
        "premise": premise,
        "arc": arc,
        "beats": len(beats),
        "key_moments": key_moments,
        "emotional_curve": curve,
    }


def determine_pacing(item: dict, production_type: dict) -> dict:
    """The production's tempo — explicit request wins, else the medium's default."""
    requested = str(item.get("pacing", "")).strip()
    tempo = requested if requested in PACING_PRESETS else production_type.get("default_pacing", "dynamic")
    if tempo not in PACING_PRESETS:
        tempo = "dynamic"
    return dict(PACING_PRESETS[tempo])


def determine_cinematic_language(production_type: dict, style: dict) -> dict:
    """The camera grammar of the whole production, from medium + style."""
    return {
        "camera_grammar": production_type.get("camera_language", "cinematic coverage"),
        "style_camera": style.get("camera_language", ""),
        "shot_progression": "establish → develop → emphasize → resolve",
        "transition_grammar": (
            "hard cuts on beats, one signature transition per act"
            if production_type.get("default_pacing") in ("dynamic", "rapid")
            else "dissolves and matched cuts, unhurried"
        ),
    }


def determine_complexity(item: dict, production_type: dict) -> str:
    """Production complexity — the medium's baseline, promoted for
    high-scoring opportunities (they earn flagship treatment)."""
    baseline = production_type.get("complexity", "standard")
    if baseline not in COMPLEXITY_LEVELS:
        baseline = "standard"
    score = max(
        int(item.get("opportunity_score", 0) or 0),
        int(item.get("virality_score", 0) or 0),
        int(item.get("quality_score", 0) or 0),
    )
    index = COMPLEXITY_LEVELS.index(baseline)
    if score >= 85 and index < len(COMPLEXITY_LEVELS) - 1:
        return COMPLEXITY_LEVELS[index + 1]
    return baseline


def recommend_techniques(production_type: dict, style: dict, interpretation: dict) -> "list[str]":
    """Ordered production techniques — the medium's core techniques plus
    what the script's shape asks for."""
    techniques = list(production_type.get("techniques", []))
    if interpretation.get("beats", 0) >= 5 and "chapter_markers" not in techniques:
        techniques.append("chapter_markers")
    if style.get("motion_language") and "style_motion_pass" not in techniques:
        techniques.append("style_motion_pass")
    return techniques


def _target_duration(item: dict, pacing: dict) -> float:
    explicit = float(item.get("target_duration_sec", 0) or 0)
    if explicit > 0:
        return explicit
    beats = interpret_script(item)["beats"] or 1
    return round(beats * pacing["scene_target_sec"], 1)


def build_blueprint(item: dict) -> dict:
    """One complete production blueprint for one content item."""
    production_type = select_production_type(item)
    style = select_style(item, production_type)
    interpretation = interpret_script(item)
    pacing = determine_pacing(item, production_type)

    return {
        "production_type": production_type["type_id"],
        "visual_style": style["style_id"],
        "pacing": pacing,
        "cinematic_language": determine_cinematic_language(production_type, style),
        "production_complexity": determine_complexity(item, production_type),
        "storytelling_style": production_type.get("storytelling_style", "narrative_arc"),
        "recommended_techniques": recommend_techniques(production_type, style, interpretation),
        "aspect_ratio": str(item.get("aspect_ratio", "9:16")),
        "target_duration_sec": _target_duration(item, pacing),
        "tone": style.get("mood", ""),
        "audience": str(item.get("audience", item.get("niche", "general"))),
        "script_interpretation": interpretation,
        "brand_id": str(item.get("brand_id", "")),
        "world_id": select_world(item)["world_id"],
    }
