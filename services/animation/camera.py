"""Camera planning — framings, movements, keyframes, and bezier curves.

Consumes Creative Studio / Visual Intelligence shot language and expands it
into a provider-independent camera plan the Render Engine can execute.
"""

from __future__ import annotations

from services.animation.config import AnimationConfig
from services.animation.models import CameraKeyframe, CameraMovement, CameraShotType

# Free-form creative language → closed shot type vocabulary.
_SHOT_TYPE_MAP = (
    ("extreme close", CameraShotType.EXTREME_CLOSE_UP),
    ("ecu", CameraShotType.EXTREME_CLOSE_UP),
    ("close-up", CameraShotType.CLOSE_UP),
    ("close up", CameraShotType.CLOSE_UP),
    ("closeup", CameraShotType.CLOSE_UP),
    ("over-the-shoulder", CameraShotType.OVER_THE_SHOULDER),
    ("over the shoulder", CameraShotType.OVER_THE_SHOULDER),
    ("ots", CameraShotType.OVER_THE_SHOULDER),
    ("first-person", CameraShotType.FIRST_PERSON),
    ("first person", CameraShotType.FIRST_PERSON),
    ("pov", CameraShotType.FIRST_PERSON),
    ("top-down", CameraShotType.TOP_DOWN),
    ("top down", CameraShotType.TOP_DOWN),
    ("bird", CameraShotType.TOP_DOWN),
    ("establishing", CameraShotType.ESTABLISHING),
    ("drone", CameraShotType.DRONE),
    ("aerial", CameraShotType.DRONE),
    ("orbit", CameraShotType.ORBIT),
    ("tracking", CameraShotType.TRACKING),
    ("follow", CameraShotType.TRACKING),
    ("dolly", CameraShotType.DOLLY),
    ("crane", CameraShotType.CRANE),
    ("handheld", CameraShotType.HANDHELD),
    ("wide", CameraShotType.WIDE),
    ("medium", CameraShotType.MEDIUM),
    ("custom", CameraShotType.CUSTOM),
)

_MOVEMENT_MAP = (
    ("smooth follow", CameraMovement.SMOOTH_FOLLOW),
    ("follow", CameraMovement.SMOOTH_FOLLOW),
    ("pedestal", CameraMovement.PEDESTAL),
    ("truck", CameraMovement.TRUCK),
    ("orbit", CameraMovement.ORBIT),
    ("dolly", CameraMovement.DOLLY),
    ("crane", CameraMovement.CRANE),
    ("push", CameraMovement.PUSH),
    ("pull", CameraMovement.PULL),
    ("zoom", CameraMovement.ZOOM),
    ("tilt", CameraMovement.TILT),
    ("pan", CameraMovement.PAN),
    ("static", CameraMovement.STATIC),
    ("locked", CameraMovement.STATIC),
    ("handheld", CameraMovement.CUSTOM),
)


def resolve_shot_type(text: str, index: int = 0) -> str:
    lowered = (text or "").lower()
    for fragment, shot_type in _SHOT_TYPE_MAP:
        if fragment in lowered:
            return shot_type
    # Sensible defaults by position: establish → medium → close → payoff.
    cycle = (
        CameraShotType.ESTABLISHING,
        CameraShotType.MEDIUM,
        CameraShotType.CLOSE_UP,
        CameraShotType.WIDE,
    )
    return cycle[index % len(cycle)]


def resolve_movement(text: str, camera_style: str = "cinematic") -> str:
    lowered = (text or "").lower()
    for fragment, movement in _MOVEMENT_MAP:
        if fragment in lowered:
            return movement
    style_defaults = {
        "documentary": CameraMovement.STATIC,
        "handheld": CameraMovement.CUSTOM,
        "static": CameraMovement.STATIC,
        "anime": CameraMovement.PUSH,
        "explainer": CameraMovement.ZOOM,
        "dynamic": CameraMovement.ORBIT,
    }
    return style_defaults.get(camera_style, CameraMovement.PUSH)


def _intensity_scale(motion_intensity: str) -> float:
    return {"subtle": 0.35, "moderate": 0.65, "high": 0.85, "extreme": 1.0}.get(motion_intensity, 0.65)


def _keyframes_for(
    movement: str,
    duration_sec: float,
    intensity: float,
    smoothing: float,
) -> "list[dict]":
    """Generate start/mid/end keyframes with bezier interpolation metadata."""
    depth = round(0.4 + intensity * 1.2, 3)
    start = CameraKeyframe(time_sec=0.0, position={"x": 0.0, "y": 1.6, "z": 3.0 + depth * 0.2})
    end_pos = {"x": 0.0, "y": 1.6, "z": 3.0}
    end_rot = {"pitch": 0.0, "yaw": 0.0, "roll": 0.0}

    if movement == CameraMovement.PAN:
        end_rot = {"pitch": 0.0, "yaw": round(12 * intensity, 2), "roll": 0.0}
    elif movement == CameraMovement.TILT:
        end_rot = {"pitch": round(-8 * intensity, 2), "yaw": 0.0, "roll": 0.0}
    elif movement == CameraMovement.ZOOM:
        end_pos = {"x": 0.0, "y": 1.6, "z": round(3.0 - depth, 3)}
    elif movement in (CameraMovement.PUSH, CameraMovement.DOLLY):
        end_pos = {"x": 0.0, "y": 1.6, "z": round(3.0 - depth, 3)}
    elif movement == CameraMovement.PULL:
        end_pos = {"x": 0.0, "y": 1.6, "z": round(3.0 + depth, 3)}
    elif movement == CameraMovement.ORBIT:
        end_pos = {"x": round(depth, 3), "y": 1.6, "z": round(3.0 - depth * 0.3, 3)}
        end_rot = {"pitch": 0.0, "yaw": round(25 * intensity, 2), "roll": 0.0}
    elif movement == CameraMovement.TRUCK:
        end_pos = {"x": round(depth, 3), "y": 1.6, "z": 3.0}
    elif movement == CameraMovement.PEDESTAL:
        end_pos = {"x": 0.0, "y": round(1.6 + depth * 0.4, 3), "z": 3.0}
    elif movement == CameraMovement.CRANE:
        end_pos = {"x": 0.0, "y": round(1.6 + depth, 3), "z": round(3.0 - depth * 0.5, 3)}
    elif movement == CameraMovement.SMOOTH_FOLLOW:
        end_pos = {"x": round(0.3 * intensity, 3), "y": 1.6, "z": round(3.0 - 0.4 * intensity, 3)}

    bezier = [
        round(0.25 + (1 - smoothing) * 0.2, 3),
        0.0,
        round(0.75 - (1 - smoothing) * 0.2, 3),
        1.0,
    ]
    mid = CameraKeyframe(
        time_sec=round(duration_sec / 2, 3),
        position={
            "x": round((start.position["x"] + end_pos["x"]) / 2, 3),
            "y": round((start.position["y"] + end_pos["y"]) / 2, 3),
            "z": round((start.position["z"] + end_pos["z"]) / 2, 3),
        },
        rotation={
            "pitch": round(end_rot["pitch"] / 2, 2),
            "yaw": round(end_rot["yaw"] / 2, 2),
            "roll": 0.0,
        },
        easing="bezier",
        bezier=bezier,
    )
    end = CameraKeyframe(
        time_sec=round(duration_sec, 3),
        position=end_pos,
        rotation=end_rot,
        easing="bezier",
        bezier=bezier,
    )
    return [start.to_dict(), mid.to_dict(), end.to_dict()]


def plan_camera(
    scenes: "list[dict]",
    shot_list: "list[dict]",
    config: AnimationConfig,
    creative_camera: "dict | None" = None,
) -> dict:
    """Build the full camera plan for one production."""
    intensity = _intensity_scale(config.motion_intensity)
    shots: "list[dict]" = []
    cursor = 0.0

    # Prefer Creative Studio shot list; fall back to one shot per scene.
    source_shots = shot_list or [
        {
            "shot_id": f"shot_{scene.get('scene_id', idx)}",
            "scene_id": scene.get("scene_id", f"scene_{idx}"),
            "camera_angle": scene.get("camera_angle", ""),
            "camera_movement": scene.get("camera_movement", ""),
            "duration_sec": float(scene.get("estimated_duration_sec", 3.0) or 3.0),
            "notes": scene.get("motion_instructions", ""),
        }
        for idx, scene in enumerate(scenes, start=1)
    ]

    for index, shot in enumerate(source_shots):
        duration = max(0.5, float(shot.get("duration_sec", 3.0) or 3.0))
        angle_text = str(shot.get("camera_angle", "") or shot.get("angle", ""))
        move_text = str(shot.get("camera_movement", "") or shot.get("movement", ""))
        shot_type = resolve_shot_type(angle_text, index)
        movement = resolve_movement(move_text, config.camera_style)
        keyframes = _keyframes_for(movement, duration, intensity, config.motion_smoothing)
        shots.append({
            "shot_id": str(shot.get("shot_id", f"shot_{index + 1}")),
            "scene_id": str(shot.get("scene_id", "")),
            "shot_type": shot_type,
            "movement": movement,
            "start_sec": round(cursor, 3),
            "end_sec": round(cursor + duration, 3),
            "duration_sec": round(duration, 3),
            "keyframes": keyframes,
            "motion_curve": {
                "interpolation": "bezier",
                "smoothing": config.motion_smoothing,
                "intensity": intensity,
            },
            "path": [kf["position"] for kf in keyframes],
            "notes": str(shot.get("notes", "")),
        })
        cursor += duration

    language = (creative_camera or {}).get("cinematic_language", {})
    return {
        "camera_style": config.camera_style,
        "cinematic_language": language,
        "aspect_ratio": config.target_aspect_ratio,
        "shot_count": len(shots),
        "shots": shots,
        "supported_shot_types": list(CameraShotType.ALL),
        "supported_movements": list(CameraMovement.ALL),
    }
