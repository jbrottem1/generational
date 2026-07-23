"""Animation Engine adapter — consume Cinematography handoff.

Does not replace Animation Studio renderers; translates cinematography_plan
into the shapes true_motion / MotionPlanner / ffmpeg expect.
"""

from __future__ import annotations

from typing import Any

from services.cinematography.models import CinematographyPlan, animation_handoff_payload


def cinematography_to_motion_planner_scenes(plan: CinematographyPlan | dict[str, Any]) -> list[dict[str, Any]]:
    """Scenes compatible with engines.render.motion.MotionPlanner.plan_scene."""
    if isinstance(plan, dict):
        plan = CinematographyPlan.from_dict(plan)
    out = []
    for s in plan.scenes:
        out.append(
            {
                "scene_number": s.scene_number,
                "scene_id": s.scene_id,
                "length_sec": s.duration_sec,
                "camera_motion": s.movement.replace("_", " "),
                "motion_intensity": int(s.camera_speed * 100),
                "zoom": s.zoom_direction,
                "camera": s.animation_camera,
                "animation_effect": s.animation_effect,
                "easing": s.easing,
                "focus_coordinates": {"x": s.focus_point.x, "y": s.focus_point.y},
                "motion_graph": [k.to_dict() for k in s.motion_graph],
            }
        )
    return out


def cinematography_to_true_motion_cameras(plan: CinematographyPlan | dict[str, Any]) -> list[str]:
    """Per-scene camera tokens for composite_true_motion_scene(..., camera=)."""
    if isinstance(plan, dict):
        plan = CinematographyPlan.from_dict(plan)
    return [s.animation_camera for s in plan.scenes]


def get_animation_handoff(candidate: dict[str, Any]) -> dict[str, Any]:
    """Read animation handoff from a candidate, rebuilding if needed."""
    if candidate.get("animation_handoff"):
        return dict(candidate["animation_handoff"])
    plan = candidate.get("cinematography_plan")
    if plan:
        return animation_handoff_payload(CinematographyPlan.from_dict(plan))
    return {"provider": "Cinematography Engine", "scenes": []}
