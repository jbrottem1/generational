"""Narration-driven cinematography direction — never random movement."""

from __future__ import annotations

import re
from typing import Any

from core.log import get_logger, log_event
from services.cinematography.models import (
    ANGLES,
    CAMERA_MOVEMENTS,
    EASINGS,
    FRAMINGS,
    TRANSITIONS,
    CinematographyPlan,
    FocusPoint,
    MotionKeyframe,
    SceneCinematography,
    _clamp,
    animation_handoff_payload,
)

logger = get_logger(__name__)

# (pattern, movement, angle, framing, zoom_dir, pan_dir, reason_template)
_NARRATION_DIRECTIVES: tuple[tuple[re.Pattern[str], str, str, str, str, str, str], ...] = (
    (
        re.compile(r"\b(tilt|tilts|tilting|axial tilt|leans toward|orbit|orbits|rotat|spin)\b", re.I),
        "orbit",
        "eye_level",
        "medium",
        "none",
        "none",
        "Narration describes tilt/orbit — camera orbits the subject.",
    ),
    (
        re.compile(r"\b(notice|look at|see this|this fossil|examine|inspect|detail)\b", re.I),
        "slow_push_in",
        "eye_level",
        "close_up",
        "in",
        "none",
        "Narration asks viewer to notice a detail — slow push-in toward focus.",
    ),
    (
        re.compile(r"\b(tiny|micro|micron|transistor|cell|molecule|nanoscale|macro)\b", re.I),
        "macro_push_in",
        "macro_close",
        "extreme_close_up",
        "in",
        "none",
        "Narration emphasizes tiny scale — macro push-in.",
    ),
    (
        re.compile(r"\b(factory|city|landscape|planet|earth from|establishing|overview|facility)\b", re.I),
        "establishing_wide",
        "high_angle",
        "extreme_wide",
        "out",
        "left",
        "Narration establishes place — cinematic wide establishing move.",
    ),
    (
        re.compile(r"\b(reveal|uncover|hidden|behind|opens up|comes into view)\b", re.I),
        "reveal",
        "eye_level",
        "medium",
        "out",
        "right",
        "Narration reveals information — pull-back reveal.",
    ),
    (
        re.compile(r"\b(follow|along|through the|moves across|travels)\b", re.I),
        "tracking",
        "eye_level",
        "medium",
        "none",
        "right",
        "Narration follows motion — tracking shot.",
    ),
    (
        re.compile(r"\b(depth|layers|foreground|background|parallax)\b", re.I),
        "parallax",
        "oblique",
        "medium",
        "none",
        "left",
        "Narration implies depth — parallax camera move.",
    ),
    (
        re.compile(r"\b(focus|shifts to|meanwhile|in the distance)\b", re.I),
        "rack_focus",
        "eye_level",
        "medium_close",
        "none",
        "none",
        "Narration shifts attention — rack focus.",
    ),
    (
        re.compile(r"\b(rise|above|sky|atmosphere|from below)\b", re.I),
        "vertical_pan",
        "low_angle",
        "wide",
        "none",
        "up",
        "Narration lifts attention upward — vertical pan.",
    ),
    (
        re.compile(r"\b(across|horizon|left to right|side by side|compare)\b", re.I),
        "horizontal_pan",
        "eye_level",
        "wide",
        "none",
        "right",
        "Narration spans space — horizontal pan.",
    ),
    (
        re.compile(r"\b(3d|three[- ]dimensional|structure|volume|molecule model)\b", re.I),
        "camera_3d_move",
        "oblique",
        "medium",
        "in",
        "right",
        "Narration implies volumetric structure — 3D camera move.",
    ),
    (
        re.compile(r"\b(pull back|zoom out|wider|context|step back)\b", re.I),
        "slow_pull_out",
        "eye_level",
        "wide",
        "out",
        "none",
        "Narration widens context — slow pull-out.",
    ),
)

# Map cinematography movement → Animation / MotionPlanner effect + true_motion camera
_ANIMATION_MAP = {
    "slow_push_in": ("cinematic_push_in", "push_in"),
    "slow_pull_out": ("slow_zoom_out", "pull_out"),
    "horizontal_pan": ("pan_right", "pan_right"),
    "vertical_pan": ("pan_right", "pan_up"),
    "parallax": ("pan_right", "parallax"),
    "camera_3d_move": ("handheld_drift", "orbit"),
    "orbit": ("handheld_drift", "orbit"),
    "rack_focus": ("static", "static"),
    "tracking": ("pan_right", "track"),
    "reveal": ("cinematic_push_in", "reveal"),
    "macro_push_in": ("documentary_slow_zoom", "push_in"),
    "establishing_wide": ("slow_zoom_out", "pull_out"),
    "static_hold": ("static", "static"),
    "whip_transition": ("whip_pan", "whip"),
}


def choose_movement(narration: str, *, evidence_motion: str = "") -> tuple[str, str, str, str, str, str]:
    """Return (movement, angle, framing, zoom_dir, pan_dir, reason). Deterministic."""
    text = narration or ""
    for pattern, movement, angle, framing, zoom, pan, reason in _NARRATION_DIRECTIVES:
        if pattern.search(text):
            return movement, angle, framing, zoom, pan, reason

    # Soft fallback from evidence motion vocabulary (still deterministic)
    ev = (evidence_motion or "").lower()
    if "orbit" in ev or "rotate" in ev:
        return "orbit", "eye_level", "medium", "none", "none", "Evidence motion suggested orbit."
    if "pull" in ev or "out" in ev or "reveal" in ev:
        return "slow_pull_out", "eye_level", "wide", "out", "none", "Evidence motion suggested pull-out."
    if "pan_left" in ev:
        return "horizontal_pan", "eye_level", "wide", "none", "left", "Evidence motion suggested pan left."
    if "pan" in ev:
        return "horizontal_pan", "eye_level", "wide", "none", "right", "Evidence motion suggested pan."
    if "static" in ev or "hold" in ev:
        # Prefer subtle motion over true static — educational shorts die on still frames.
        return "slow_push_in", "eye_level", "medium", "in", "none", "Replaced static hold with slow push-in for retention."
    if "push" in ev or "ken_burns_in" in ev or "zoom" in ev:
        return "slow_push_in", "eye_level", "medium_close", "in", "none", "Default teaching emphasis — slow push-in."

    return "slow_push_in", "eye_level", "medium", "in", "none", "Default educational emphasis — slow push-in guides attention."


def choose_transition(
    narration: str,
    *,
    scene_index: int,
    total_scenes: int,
    prev_movement: str = "",
) -> str:
    text = (narration or "").lower()
    if scene_index == 0:
        return "fade"
    if scene_index >= total_scenes - 1:
        return "fade"
    if re.search(r"\b(suddenly|meanwhile|cut to|but then)\b", text):
        return "whip_transition"
    if re.search(r"\b(same|identical|compare|versus|parallel)\b", text):
        return "match_cut"
    if prev_movement == "orbit" or "continues" in text:
        return "l_cut"
    if re.search(r"\b(next|then|after)\b", text):
        return "j_cut"
    if re.search(r"\b(quietly|slowly|gently)\b", text):
        return "cross_dissolve"
    return "cross_dissolve"


def build_focus_point(
    narration: str,
    *,
    evidence_scene: dict[str, Any] | None = None,
) -> FocusPoint:
    evidence_scene = evidence_scene or {}
    # Prefer annotation / evidence zoom focus
    motion = evidence_scene.get("motion_plan") or {}
    zooms = motion.get("suggested_zooms") or []
    if zooms and isinstance(zooms[0], dict):
        z0 = zooms[0]
        return FocusPoint(
            x=float(z0.get("focus_x") or 0.5),
            y=float(z0.get("focus_y") or 0.5),
            label=str(z0.get("reason") or "annotation focus"),
            reason="Evidence annotation zoom target",
        )
    anns = evidence_scene.get("annotation_plan") or []
    if anns and isinstance(anns[0], dict):
        region = anns[0].get("highlight_region") or {}
        cue = str(anns[0].get("narration_cue") or "")
        if region:
            return FocusPoint(
                x=(float(region.get("x0", 0.4)) + float(region.get("x1", 0.6))) / 2,
                y=(float(region.get("y0", 0.3)) + float(region.get("y1", 0.5))) / 2,
                label=cue,
                reason="Narration callout region",
            )
    # Heuristic: subject nouns tend center-right for educational frames
    if re.search(r"\b(left|west)\b", narration or "", re.I):
        return FocusPoint(x=0.35, y=0.48, label="left subject", reason="Narration references left side")
    if re.search(r"\b(right|east)\b", narration or "", re.I):
        return FocusPoint(x=0.65, y=0.48, label="right subject", reason="Narration references right side")
    return FocusPoint(x=0.5, y=0.45, label="subject", reason="Default educational subject focus")


def build_motion_graph(
    movement: str,
    *,
    focus: FocusPoint,
    duration_sec: float,
    speed: float,
    parallax: float,
) -> list[MotionKeyframe]:
    """Sampled keyframes 0→1 for Animation Engine interpolation."""
    depth = 0.06 + speed * 0.12
    fx, fy = focus.x, focus.y
    if movement in ("slow_push_in", "macro_push_in", "reveal"):
        return [
            MotionKeyframe(t=0.0, zoom=1.0, focus_x=fx, focus_y=fy, parallax=0),
            MotionKeyframe(t=0.5, zoom=1.0 + depth * 0.55, focus_x=fx, focus_y=fy, parallax=parallax * 0.5),
            MotionKeyframe(t=1.0, zoom=1.0 + depth, focus_x=fx, focus_y=fy, parallax=parallax),
        ]
    if movement in ("slow_pull_out", "establishing_wide"):
        return [
            MotionKeyframe(t=0.0, zoom=1.0 + depth, focus_x=fx, focus_y=fy),
            MotionKeyframe(t=1.0, zoom=1.0, focus_x=0.5, focus_y=0.5, parallax=parallax),
        ]
    if movement == "orbit":
        return [
            MotionKeyframe(t=0.0, zoom=1.05, rotate_deg=-8, focus_x=fx, focus_y=fy, parallax=parallax),
            MotionKeyframe(t=0.5, zoom=1.08, rotate_deg=0, focus_x=fx, focus_y=fy, parallax=parallax),
            MotionKeyframe(t=1.0, zoom=1.05, rotate_deg=8, focus_x=fx, focus_y=fy, parallax=parallax),
        ]
    if movement == "horizontal_pan":
        return [
            MotionKeyframe(t=0.0, zoom=1.05, pan_x=-0.08, focus_x=max(0.2, fx - 0.1), focus_y=fy),
            MotionKeyframe(t=1.0, zoom=1.05, pan_x=0.08, focus_x=min(0.8, fx + 0.1), focus_y=fy, parallax=parallax),
        ]
    if movement == "vertical_pan":
        return [
            MotionKeyframe(t=0.0, zoom=1.05, pan_y=0.06, focus_x=fx, focus_y=min(0.7, fy + 0.1)),
            MotionKeyframe(t=1.0, zoom=1.05, pan_y=-0.06, focus_x=fx, focus_y=max(0.3, fy - 0.1), parallax=parallax),
        ]
    if movement == "parallax":
        return [
            MotionKeyframe(t=0.0, zoom=1.04, pan_x=-0.04, parallax=0.0, focus_x=fx, focus_y=fy),
            MotionKeyframe(t=1.0, zoom=1.06, pan_x=0.05, parallax=max(0.35, parallax), focus_x=fx, focus_y=fy),
        ]
    if movement == "tracking":
        return [
            MotionKeyframe(t=0.0, zoom=1.03, pan_x=-0.1, focus_x=fx, focus_y=fy),
            MotionKeyframe(t=1.0, zoom=1.03, pan_x=0.1, focus_x=fx, focus_y=fy, parallax=parallax * 0.6),
        ]
    if movement == "camera_3d_move":
        return [
            MotionKeyframe(t=0.0, zoom=1.02, rotate_deg=-4, pan_x=-0.03, parallax=0.2, focus_x=fx, focus_y=fy),
            MotionKeyframe(t=0.5, zoom=1.08, rotate_deg=0, pan_x=0.0, parallax=0.45, focus_x=fx, focus_y=fy),
            MotionKeyframe(t=1.0, zoom=1.05, rotate_deg=5, pan_x=0.04, parallax=0.55, focus_x=fx, focus_y=fy),
        ]
    if movement == "rack_focus":
        return [
            MotionKeyframe(t=0.0, zoom=1.02, focus_x=0.35, focus_y=0.5),
            MotionKeyframe(t=0.45, zoom=1.02, focus_x=0.35, focus_y=0.5),
            MotionKeyframe(t=1.0, zoom=1.04, focus_x=fx, focus_y=fy),
        ]
    # static
    return [
        MotionKeyframe(t=0.0, zoom=1.0, focus_x=fx, focus_y=fy),
        MotionKeyframe(t=1.0, zoom=1.0, focus_x=fx, focus_y=fy),
    ]


def _easing_for(speed: float, movement: str) -> str:
    if movement in ("whip_transition",):
        return "ease_out"
    if movement in ("macro_push_in", "slow_push_in"):
        return "ease_in_out_cubic"
    if speed < 0.35:
        return "smoothstep"
    if speed > 0.65:
        return "ease_out"
    return "ease_in_out"


def _speed_for(movement: str, duration_sec: float, attention: int) -> float:
    base = {
        "macro_push_in": 0.28,
        "slow_push_in": 0.32,
        "slow_pull_out": 0.30,
        "establishing_wide": 0.34,
        "orbit": 0.38,
        "parallax": 0.40,
        "tracking": 0.45,
        "horizontal_pan": 0.42,
        "vertical_pan": 0.40,
        "reveal": 0.36,
        "camera_3d_move": 0.44,
        "rack_focus": 0.25,
        "static_hold": 0.18,
    }.get(movement, 0.35)
    # Longer scenes → slightly slower; high attention → slightly more energy
    adj = base - min(0.08, max(0, duration_sec - 4) * 0.01) + (attention - 50) * 0.001
    return round(max(0.08, min(0.85, adj)), 3)


def _pacing(duration_sec: float, speed: float) -> str:
    if duration_sec <= 3.5 or speed >= 0.55:
        return "brisk"
    if duration_sec >= 7 or speed <= 0.28:
        return "contemplative"
    return "measured"


def _attention_score(
    movement: str,
    *,
    evidence_attention: int,
    has_focus_label: bool,
) -> int:
    boost = {
        "macro_push_in": 18,
        "orbit": 16,
        "reveal": 15,
        "slow_push_in": 14,
        "parallax": 13,
        "tracking": 12,
        "establishing_wide": 10,
        "whip_transition": 12,
        "camera_3d_move": 14,
        "static_hold": -18,
    }.get(movement, 10)
    # Prefer cinematic motion: floor attention when moving (educational shorts).
    return _clamp(0.45 * evidence_attention + 0.20 * 70 + 0.35 * (55 + boost) + (6 if has_focus_label else 0))


def direct_scene(
    scene: dict[str, Any],
    *,
    scene_index: int = 0,
    total_scenes: int = 1,
    prev_movement: str = "",
) -> SceneCinematography:
    """Direct one evidence/VI scene into full cinematography."""
    narration = str(scene.get("narration") or scene.get("text") or "")
    evidence_motion = ""
    mp = scene.get("motion_plan") or {}
    if isinstance(mp, dict):
        evidence_motion = str(mp.get("camera_motion") or "")
    evidence_motion = evidence_motion or str(scene.get("camera_motion") or "")

    movement, angle, framing, zoom_dir, pan_dir, reason = choose_movement(
        narration, evidence_motion=evidence_motion
    )
    if movement not in CAMERA_MOVEMENTS:
        movement = "slow_push_in"
    if angle not in ANGLES:
        angle = "eye_level"
    if framing not in FRAMINGS:
        framing = "medium"

    start = float((scene.get("narration_timing") or {}).get("start_sec") or scene.get("timing_start") or 0)
    end = float((scene.get("narration_timing") or {}).get("end_sec") or scene.get("timing_end") or 0)
    duration = float(scene.get("length_sec") or scene.get("duration_sec") or (end - start if end > start else 4.0))
    if duration <= 0:
        duration = 4.0

    evidence_attention = int(scene.get("expected_attention_score") or scene.get("attention_score") or 72)
    speed = _speed_for(movement, duration, evidence_attention)
    parallax = 0.55 if movement in ("parallax", "camera_3d_move", "orbit") else (0.25 if movement == "tracking" else 0.1)
    easing = _easing_for(speed, movement)
    if easing not in EASINGS:
        easing = "ease_in_out"

    focus = build_focus_point(narration, evidence_scene=scene)
    graph = build_motion_graph(movement, focus=focus, duration_sec=duration, speed=speed, parallax=parallax)
    transition = choose_transition(
        narration, scene_index=scene_index, total_scenes=total_scenes, prev_movement=prev_movement
    )
    if transition not in TRANSITIONS:
        transition = "cross_dissolve"

    effect, anim_cam = _ANIMATION_MAP.get(movement, ("cinematic_push_in", "push_in"))
    attention = _attention_score(movement, evidence_attention=evidence_attention, has_focus_label=bool(focus.label))

    scene_id = str(scene.get("scene_id") or scene.get("scene_number") or f"s{scene_index+1}")
    number = int(scene.get("scene_number") or scene_index + 1)

    return SceneCinematography(
        scene_id=scene_id,
        scene_number=number,
        narration=narration,
        camera_angle=angle,
        framing=framing,
        zoom_direction=zoom_dir,
        pan_direction=pan_dir,
        parallax_depth=parallax,
        camera_speed=speed,
        easing=easing,
        focus_point=focus,
        transition=transition,
        duration_sec=round(duration, 2),
        movement=movement,
        movement_reason=reason,
        motion_graph=graph,
        timeline={"start_sec": round(start, 3), "end_sec": round(start + duration, 3)},
        scene_pacing=_pacing(duration, speed),
        attention_score=attention,
        animation_effect=effect,
        animation_camera=anim_cam,
    )


def _scenes_from_candidate(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    """Prefer evidence scene_builder plans, then VI scenes, then evidence package scenes."""
    evidence = candidate.get("evidence_package") or {}
    if evidence.get("scenes"):
        out = []
        for s in evidence["scenes"]:
            if not isinstance(s, dict):
                continue
            row = dict(s)
            # Flatten scene_builder if needed
            sb = s.get("scene_builder") or {}
            if sb and not row.get("motion_plan"):
                row["motion_plan"] = sb.get("motion_plan")
            out.append(row)
        if out:
            return out

    visual = candidate.get("visual_package") or {}
    if visual.get("scenes"):
        return [s for s in visual["scenes"] if isinstance(s, dict)]

    plans = candidate.get("scene_builder_plans") or []
    if plans:
        return [{"narration": "", "scene_builder": p, **(p if isinstance(p, dict) else {})} for p in plans]

    # Fallback single beat
    return [
        {
            "scene_number": 1,
            "scene_id": "s1",
            "narration": str(candidate.get("hook") or candidate.get("script") or candidate.get("title") or ""),
            "length_sec": 5.0,
        }
    ]


def build_cinematography_plan(candidate: dict[str, Any], *, topic: str = "") -> CinematographyPlan:
    """Full cinematography package from Evidence + Visual Intelligence scenes."""
    title = str(candidate.get("title") or topic or "educational video")
    raw_scenes = _scenes_from_candidate(candidate)
    directed: list[SceneCinematography] = []
    prev = ""
    for i, scene in enumerate(raw_scenes):
        shot = direct_scene(scene, scene_index=i, total_scenes=len(raw_scenes), prev_movement=prev)
        directed.append(shot)
        prev = shot.movement

    overall = _clamp(sum(s.attention_score for s in directed) / max(1, len(directed)))
    pacing_counts = {}
    for s in directed:
        pacing_counts[s.scene_pacing] = pacing_counts.get(s.scene_pacing, 0) + 1
    pacing_summary = max(pacing_counts, key=pacing_counts.get) if pacing_counts else "measured"

    movements = ", ".join(f"{s.scene_number}:{s.movement}" for s in directed[:6])
    reasoning = (
        f"Directed {len(directed)} scenes for '{title}'. "
        f"Movements chosen to reinforce narration ({movements}). "
        f"Overall attention {overall}; pacing={pacing_summary}."
    )
    plan = CinematographyPlan(
        topic=title,
        scenes=directed,
        overall_attention_score=overall,
        pacing_summary=pacing_summary,
        reasoning=reasoning,
    )
    log_event(
        logger,
        "cinematography.planned",
        topic=title[:80],
        scenes=len(directed),
        attention=overall,
        pacing=pacing_summary,
    )
    return plan


def apply_cinematography_to_visual_scenes(
    visual_package: dict[str, Any],
    plan: CinematographyPlan | dict[str, Any],
) -> dict[str, Any]:
    """Enrich VI scenes with cinematography fields (additive)."""
    if isinstance(plan, dict):
        plan = CinematographyPlan.from_dict(plan)
    pkg = dict(visual_package)
    scenes = list(pkg.get("scenes") or [])
    directed = list(plan.scenes)
    bound = []
    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            bound.append(scene)
            continue
        shot = directed[i] if i < len(directed) else (directed[-1] if directed else None)
        row = dict(scene)
        if shot:
            row["cinematography"] = shot.to_dict()
            row["camera_motion"] = shot.movement.replace("_", " ")
            row["camera_angle"] = shot.camera_angle
            row["motion_intensity"] = int(shot.camera_speed * 100)
            row["zoom"] = shot.zoom_direction
            row["transition_out"] = shot.transition.replace("_", " ")
            row["animation_effect"] = shot.animation_effect
            row["animation_camera"] = shot.animation_camera
            row["motion_graph"] = [k.to_dict() for k in shot.motion_graph]
            row["focus_coordinates"] = {"x": shot.focus_point.x, "y": shot.focus_point.y}
            row["easing"] = shot.easing
            row["cinematography_attention_score"] = shot.attention_score
        bound.append(row)
    pkg["scenes"] = bound
    pkg["cinematography_plan"] = plan.to_dict()
    return pkg
