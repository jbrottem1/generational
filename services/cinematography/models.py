"""Cinematography contracts — professional directed motion per scene.

Structured JSON only. Feeds Animation Engine / Render MotionPlanner.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def _clamp(value: float, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, int(round(value))))


# Closed cinematography vocabulary (mission movements + transitions)
CAMERA_MOVEMENTS = (
    "slow_push_in",
    "slow_pull_out",
    "horizontal_pan",
    "vertical_pan",
    "parallax",
    "camera_3d_move",
    "orbit",
    "rack_focus",
    "tracking",
    "reveal",
    "macro_push_in",
    "establishing_wide",
    "static_hold",
)

TRANSITIONS = (
    "whip_transition",
    "match_cut",
    "cross_dissolve",
    "fade",
    "l_cut",
    "j_cut",
    "hard_cut",
)

EASINGS = (
    "linear",
    "ease_in",
    "ease_out",
    "ease_in_out",
    "ease_in_out_cubic",
    "smoothstep",
)

ANGLES = (
    "eye_level",
    "low_angle",
    "high_angle",
    "top_down",
    "oblique",
    "macro_close",
    "wide_establishing",
)

FRAMINGS = (
    "extreme_wide",
    "wide",
    "medium",
    "medium_close",
    "close_up",
    "extreme_close_up",
    "insert",
)


@dataclass
class FocusPoint:
    x: float = 0.5  # normalized 0–1
    y: float = 0.5
    label: str = ""
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FocusPoint":
        data = data or {}
        return cls(
            x=float(data.get("x") or 0.5),
            y=float(data.get("y") or 0.5),
            label=str(data.get("label") or ""),
            reason=str(data.get("reason") or ""),
        )


@dataclass
class MotionKeyframe:
    """One point on the motion graph."""

    t: float  # 0–1 within scene
    zoom: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0
    rotate_deg: float = 0.0
    focus_x: float = 0.5
    focus_y: float = 0.5
    parallax: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MotionKeyframe":
        data = data or {}
        return cls(
            t=float(data.get("t") or 0),
            zoom=float(data.get("zoom") or 1.0),
            pan_x=float(data.get("pan_x") or 0),
            pan_y=float(data.get("pan_y") or 0),
            rotate_deg=float(data.get("rotate_deg") or 0),
            focus_x=float(data.get("focus_x") or 0.5),
            focus_y=float(data.get("focus_y") or 0.5),
            parallax=float(data.get("parallax") or 0),
        )


@dataclass
class SceneCinematography:
    """Directed cinematography for one scene."""

    scene_id: str = ""
    scene_number: int = 0
    narration: str = ""
    camera_angle: str = "eye_level"
    framing: str = "medium"
    zoom_direction: str = "none"  # in | out | none
    pan_direction: str = "none"  # left | right | up | down | none
    parallax_depth: float = 0.0  # 0–1
    camera_speed: float = 0.35  # 0–1
    easing: str = "ease_in_out"
    focus_point: FocusPoint = field(default_factory=FocusPoint)
    transition: str = "cross_dissolve"
    duration_sec: float = 4.0
    movement: str = "slow_push_in"
    movement_reason: str = ""
    motion_graph: list[MotionKeyframe] = field(default_factory=list)
    timeline: dict[str, float] = field(default_factory=dict)  # start_sec, end_sec
    scene_pacing: str = "measured"  # brisk | measured | contemplative
    attention_score: int = 50
    # Animation Engine handoff (render vocabulary)
    animation_effect: str = "cinematic_push_in"
    animation_camera: str = "push_in"

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "scene_number": self.scene_number,
            "narration": self.narration,
            "camera_angle": self.camera_angle,
            "framing": self.framing,
            "zoom_direction": self.zoom_direction,
            "pan_direction": self.pan_direction,
            "parallax_depth": round(float(self.parallax_depth), 3),
            "camera_speed": round(float(self.camera_speed), 3),
            "easing": self.easing,
            "focus_point": self.focus_point.to_dict(),
            "focus_coordinates": {"x": self.focus_point.x, "y": self.focus_point.y},
            "transition": self.transition,
            "duration_sec": float(self.duration_sec),
            "movement": self.movement,
            "movement_reason": self.movement_reason,
            "motion_graph": [k.to_dict() for k in self.motion_graph],
            "timeline": dict(self.timeline),
            "scene_pacing": self.scene_pacing,
            "attention_score": int(self.attention_score),
            "animation_effect": self.animation_effect,
            "animation_camera": self.animation_camera,
            "camera_plan": {
                "angle": self.camera_angle,
                "framing": self.framing,
                "movement": self.movement,
                "zoom_direction": self.zoom_direction,
                "pan_direction": self.pan_direction,
                "speed": self.camera_speed,
                "easing": self.easing,
                "focus": self.focus_point.to_dict(),
                "parallax_depth": self.parallax_depth,
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SceneCinematography":
        data = data or {}
        graph = [MotionKeyframe.from_dict(k) for k in (data.get("motion_graph") or [])]
        return cls(
            scene_id=str(data.get("scene_id") or ""),
            scene_number=int(data.get("scene_number") or 0),
            narration=str(data.get("narration") or ""),
            camera_angle=str(data.get("camera_angle") or "eye_level"),
            framing=str(data.get("framing") or "medium"),
            zoom_direction=str(data.get("zoom_direction") or "none"),
            pan_direction=str(data.get("pan_direction") or "none"),
            parallax_depth=float(data.get("parallax_depth") or 0),
            camera_speed=float(data.get("camera_speed") or 0.35),
            easing=str(data.get("easing") or "ease_in_out"),
            focus_point=FocusPoint.from_dict(data.get("focus_point") or data.get("focus_coordinates") or {}),
            transition=str(data.get("transition") or "cross_dissolve"),
            duration_sec=float(data.get("duration_sec") or 4),
            movement=str(data.get("movement") or "slow_push_in"),
            movement_reason=str(data.get("movement_reason") or ""),
            motion_graph=graph,
            timeline=dict(data.get("timeline") or {}),
            scene_pacing=str(data.get("scene_pacing") or "measured"),
            attention_score=_clamp(data.get("attention_score", 50)),
            animation_effect=str(data.get("animation_effect") or "cinematic_push_in"),
            animation_camera=str(data.get("animation_camera") or "push_in"),
        )


@dataclass
class CinematographyPlan:
    """Full candidate cinematography package for Animation Engine."""

    topic: str = ""
    scenes: list[SceneCinematography] = field(default_factory=list)
    overall_attention_score: int = 50
    pacing_summary: str = ""
    reasoning: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "scenes": [s.to_dict() for s in self.scenes],
            "camera_plan": [s.to_dict()["camera_plan"] for s in self.scenes],
            "timeline": [
                {"scene_id": s.scene_id, **s.timeline, "duration_sec": s.duration_sec}
                for s in self.scenes
            ],
            "motion_graph": [
                {"scene_id": s.scene_id, "keyframes": [k.to_dict() for k in s.motion_graph]}
                for s in self.scenes
            ],
            "overall_attention_score": int(self.overall_attention_score),
            "scene_pacing": self.pacing_summary,
            "reasoning": self.reasoning,
            "animation_handoff": animation_handoff_payload(self),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CinematographyPlan":
        data = data or {}
        return cls(
            topic=str(data.get("topic") or ""),
            scenes=[SceneCinematography.from_dict(s) for s in (data.get("scenes") or [])],
            overall_attention_score=_clamp(data.get("overall_attention_score", 50)),
            pacing_summary=str(data.get("scene_pacing") or data.get("pacing_summary") or ""),
            reasoning=str(data.get("reasoning") or ""),
        )


def animation_handoff_payload(plan: CinematographyPlan) -> dict[str, Any]:
    """Canonical payload for Animation Engine / true_motion / ffmpeg."""
    return {
        "provider": "Cinematography Engine",
        "scenes": [
            {
                "scene_id": s.scene_id,
                "scene_number": s.scene_number,
                "duration_sec": s.duration_sec,
                "camera": s.animation_camera,
                "effect": s.animation_effect,
                "easing": s.easing,
                "focus": s.focus_point.to_dict(),
                "motion_graph": [k.to_dict() for k in s.motion_graph],
                "transition": s.transition,
                "parallax_depth": s.parallax_depth,
                "speed": s.camera_speed,
                "attention_score": s.attention_score,
            }
            for s in plan.scenes
        ],
    }
