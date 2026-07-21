"""Simulate a performance into executable path keyframes (pre-render)."""

from __future__ import annotations

from typing import Any

from services.character_performance_engine.models import PERFORMANCE_HINTS


def simulate_performance(
    *,
    locomotion: dict[str, Any],
    body: dict[str, Any],
    interactions: dict[str, Any],
    camera_follow: dict[str, Any],
    duration_sec: float,
    emotion: str = "confidence",
) -> dict[str, Any]:
    """Produce actor-driven keyframes the compositor can execute.

    Output is performance data — not pixels. true_motion consumes the path.
    """
    waypoints = list((locomotion or {}).get("waypoints") or [])
    dur = max(float(duration_sec or 3.0), 0.1)
    keyframes: list[dict[str, Any]] = []

    for wp in waypoints:
        t = float(wp.get("t") or 0.0)
        keyframes.append(
            {
                "t": round(min(max(t, 0.0), dur), 3),
                "x": float(wp.get("x") or 0.5),
                "y": float(wp.get("y") or 0.52),
                "scale": _scale_for_depth(float(wp.get("y") or 0.52)),
                "facing": wp.get("facing") or "path",
                "action": wp.get("action") or "walk",
                "grounded": True,
            }
        )

    # Inject interaction peaks as micro-holds with gesture scale pulse (not freezes)
    for ev in interactions.get("events") or []:
        t = float(ev.get("t") or 0)
        if 0 < t < dur:
            keyframes.append(
                {
                    "t": round(t, 3),
                    "x": _interp_x(keyframes, t),
                    "y": _interp_y(keyframes, t) - 0.01,  # slight lean into prop
                    "scale": _scale_for_depth(_interp_y(keyframes, t)) + 0.02,
                    "facing": "target",
                    "action": str(ev.get("verb") or "interact"),
                    "grounded": True,
                    "interaction": True,
                }
            )

    keyframes.sort(key=lambda k: float(k["t"]))
    keyframes = _dedupe_times(keyframes)

    # Continuous micro-motion samples so nothing is a still photo between waypoints
    dense = _densify(keyframes, dur, step=0.35)

    hint = _performance_hint(body, camera_follow)
    return {
        "duration_sec": dur,
        "keyframes": dense,
        "path_summary": {
            "start": dense[0] if dense else None,
            "end": dense[-1] if dense else None,
            "waypoint_count": len(dense),
            "travel_norm": locomotion.get("path_distance_norm"),
        },
        "true_motion_performance": hint,
        "emotion": emotion,
        "actor_driven": True,
        "camera_follow_mode": camera_follow.get("mode"),
        "foot_contact_required": True,
        "simulation": "blocking_locomotion_body_interaction",
    }


def _scale_for_depth(y: float) -> float:
    # Slight perspective: lower on frame → nearer → larger
    return round(0.62 + (float(y) - 0.45) * 0.35, 3)


def _interp_x(keyframes: list[dict[str, Any]], t: float) -> float:
    return _interp_axis(keyframes, t, "x", 0.5)


def _interp_y(keyframes: list[dict[str, Any]], t: float) -> float:
    return _interp_axis(keyframes, t, "y", 0.52)


def _interp_axis(keyframes: list[dict[str, Any]], t: float, axis: str, default: float) -> float:
    if not keyframes:
        return default
    if t <= float(keyframes[0]["t"]):
        return float(keyframes[0].get(axis) or default)
    if t >= float(keyframes[-1]["t"]):
        return float(keyframes[-1].get(axis) or default)
    for a, b in zip(keyframes, keyframes[1:]):
        ta, tb = float(a["t"]), float(b["t"])
        if ta <= t <= tb:
            if tb <= ta:
                return float(b.get(axis) or default)
            u = (t - ta) / (tb - ta)
            return float(a.get(axis) or default) * (1 - u) + float(b.get(axis) or default) * u
    return default


def _dedupe_times(keyframes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for kf in keyframes:
        if out and abs(float(out[-1]["t"]) - float(kf["t"])) < 0.05:
            out[-1] = kf
        else:
            out.append(kf)
    return out


def _densify(keyframes: list[dict[str, Any]], dur: float, *, step: float = 0.35) -> list[dict[str, Any]]:
    if len(keyframes) < 2:
        return keyframes
    out: list[dict[str, Any]] = []
    t = 0.0
    while t <= dur + 1e-6:
        out.append(
            {
                "t": round(min(t, dur), 3),
                "x": round(_interp_x(keyframes, t), 4),
                "y": round(_interp_y(keyframes, t), 4),
                "scale": round(_scale_for_depth(_interp_y(keyframes, t)), 3),
                "action": "continuous",
                "grounded": True,
                "walk_bob": True,
            }
        )
        t += step
    # Preserve interaction / named action markers
    for kf in keyframes:
        if kf.get("interaction") or kf.get("action") not in {None, "continuous", "walk"}:
            out.append(kf)
    out.sort(key=lambda k: float(k["t"]))
    return _dedupe_times(out)


def _performance_hint(body: dict[str, Any], camera_follow: dict[str, Any]) -> str:
    timeline = body.get("timeline") or []
    verbs = " ".join(str(x.get("primary_action") or "") for x in timeline)
    if "point" in verbs or "touch" in verbs:
        return "point_teach"
    if camera_follow.get("mode") in {"walk_and_talk", "tracking", "follow"}:
        return "walk_explain"
    return PERFORMANCE_HINTS[0]
