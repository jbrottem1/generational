"""Visual effects and transition planning."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.post_production.config import PostProductionConfig

_TRANSITION_MAP = {
    "minimal": ["cut", "crossfade"],
    "dynamic": ["cut", "crossfade", "zoom", "wipe"],
    "cinematic": ["crossfade", "dissolve", "zoom"],
}


def build_transitions(
    render_package: dict,
    scene_cuts: list,
    config: "PostProductionConfig | None" = None,
) -> list:
    """Plan transitions between edited scenes."""
    from services.post_production.config import get_post_production_config

    config = config or get_post_production_config()
    allowed = _TRANSITION_MAP.get(config.transition_style, _TRANSITION_MAP["dynamic"])
    transition_plan = render_package.get("transition_plan") or {}
    source_transitions = transition_plan.get("transitions") or []

    transitions = []
    for index, cut in enumerate(scene_cuts):
        source = source_transitions[index] if index < len(source_transitions) else {}
        t_type = source.get("type", allowed[index % len(allowed)])
        if t_type not in allowed:
            t_type = allowed[0]

        transitions.append({
            "transition_id": f"trans_{cut['scene_id']}",
            "from_clip": f"scene_{cut['scene_id']}",
            "to_clip": f"scene_{scene_cuts[index + 1]['scene_id']}" if index + 1 < len(scene_cuts) else "",
            "time": cut["edited_end"],
            "type": t_type,
            "duration_sec": float(source.get("duration_sec", 0.3)),
        })

    return transitions


def build_effects(
    render_package: dict,
    scene_cuts: list,
    config: "PostProductionConfig | None" = None,
) -> list:
    """Plan visual effects — motion blur, glow, speed ramps, zoom emphasis."""
    from services.post_production.config import get_post_production_config

    config = config or get_post_production_config()
    motion_plan = render_package.get("motion_plan") or {}
    if isinstance(motion_plan, list):
        motion_effects = motion_plan
    else:
        motion_effects = motion_plan.get("effects") or []
    effects = []

    for cut in scene_cuts:
        scene_id = cut["scene_id"]
        if cut["cut_type"] == "speed_ramp":
            effects.append({
                "effect_id": f"fx_speed_{scene_id}",
                "clip_ref": f"scene_{scene_id}",
                "effect_type": "speed_ramp",
                "start_time": cut["edited_start"],
                "end_time": cut["edited_end"],
                "parameters": {"ramp_in": 1.5, "ramp_out": 0.8},
            })
        elif cut["cut_type"] == "jump_cut":
            effects.append({
                "effect_id": f"fx_zoom_{scene_id}",
                "clip_ref": f"scene_{scene_id}",
                "effect_type": "zoom",
                "start_time": cut["edited_start"],
                "end_time": cut["edited_start"] + 0.5,
                "parameters": {"scale": 1.08, "ease": "ease_out"},
            })

    for motion in motion_effects:
        effects.append({
            "effect_id": motion.get("effect_id", ""),
            "clip_ref": motion.get("clip_ref", ""),
            "effect_type": motion.get("type", "motion_blur"),
            "start_time": float(motion.get("start_time", 0.0)),
            "end_time": float(motion.get("end_time", 0.0)),
            "parameters": motion.get("parameters", {}),
        })

    return effects
