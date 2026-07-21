"""Bridge Character Performance Engine simulations → true_motion path exprs.

No new renderer — only richer inputs for the existing layered compositor.
"""

from __future__ import annotations

from typing import Any


def simulation_to_true_motion_path(simulation: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize simulation keyframes for composite_true_motion_scene."""
    sim = simulation or {}
    keyframes = list(sim.get("keyframes") or [])
    return {
        "actor_driven": bool(sim.get("actor_driven")),
        "duration_sec": float(sim.get("duration_sec") or 0),
        "performance": sim.get("true_motion_performance") or "walk_explain",
        "keyframes": [
            {
                "t": float(k.get("t") or 0),
                "x": float(k.get("x") or 0.5),
                "y": float(k.get("y") or 0.52),
                "scale": float(k.get("scale") or 0.72),
                "walk_bob": bool(k.get("walk_bob", True)),
                "grounded": bool(k.get("grounded", True)),
            }
            for k in keyframes
            if isinstance(k, dict)
        ],
    }


def path_to_ffmpeg_exprs(
    path: dict[str, Any],
    *,
    duration_sec: float,
    shot_size: str = "dynamic_medium",
) -> tuple[str, str, str]:
    """Convert normalized path keyframes to ffmpeg overlay x/y + scale.

    x,y are framed as fractions of available (W-w) / (H-h) space so the
    character stays on-stage while traveling a planned blocking path.
    """
    keyframes = list((path or {}).get("keyframes") or [])
    if len(keyframes) < 2:
        # Fallback linear cross — still actor travel, not camera-only
        travel = 0.35
        x_expr = f"(W-w)*({0.5 - travel / 2:.3f}+{travel:.3f}*t/{max(duration_sec, 0.1)})"
        y_expr = "(H-h)*0.48+18*sin(2*PI*t*2.0)+6*sin(2*PI*t/3.2)"
        scale = _base_scale(shot_size)
        return x_expr, y_expr, f"{scale:.2f}"

    # Piecewise linear x/y; scale from shot size with mild path modulation
    x_expr = _piecewise(keyframes, "x", duration_sec, space="(W-w)")
    y_expr = (
        _piecewise(keyframes, "y", duration_sec, space="(H-h)")
        + "+16*sin(2*PI*t*2.0)+6*sin(2*PI*t/3.2)"  # walk bob + breathe
    )
    # Use average scale; ffmpeg scale filter wants a constant here
    scales = [float(k.get("scale") or _base_scale(shot_size)) for k in keyframes]
    scale = sum(scales) / max(len(scales), 1)
    scale = max(0.42, min(0.95, scale * (_base_scale(shot_size) / 0.74)))
    return x_expr, y_expr, f"{scale:.2f}"


def _base_scale(shot_size: str) -> float:
    return {
        "intimate_close_up": 0.92,
        "hero_low_angle": 0.84,
        "dynamic_medium": 0.74,
        "high_angle_vulnerable": 0.62,
        "establishing_wide": 0.48,
        "wide_establishing": 0.48,
    }.get(str(shot_size or "dynamic_medium"), 0.74)


def _piecewise(
    keyframes: list[dict[str, Any]],
    axis: str,
    duration_sec: float,
    *,
    space: str,
) -> str:
    """Build nested if() ffmpeg expression for piecewise linear interpolation."""
    kfs = sorted(keyframes, key=lambda k: float(k.get("t") or 0))
    # Clamp last keyframe to duration
    if float(kfs[-1].get("t") or 0) < duration_sec:
        kfs = [*kfs, {**kfs[-1], "t": duration_sec}]

    def seg(i: int) -> str:
        a, b = kfs[i], kfs[i + 1]
        ta, tb = float(a["t"]), float(b["t"])
        va, vb = float(a.get(axis) or 0.5), float(b.get(axis) or 0.5)
        if tb <= ta:
            return f"{space}*{vb:.4f}"
        # va + (vb-va)*(t-ta)/(tb-ta)
        return (
            f"({space}*({va:.4f}+({vb:.4f}-({va:.4f}))*(t-{ta:.3f})/{max(tb - ta, 0.001):.3f}))"
        )

    expr = seg(len(kfs) - 2)
    for i in range(len(kfs) - 3, -1, -1):
        tb = float(kfs[i + 1]["t"])
        expr = f"if(lt(t,{tb:.3f}),{seg(i)},{expr})"
    return expr


def package_true_motion_fields(package: dict[str, Any]) -> dict[str, Any]:
    """Fields to merge into scene['true_motion']."""
    sim = package.get("simulation") or {}
    cam = package.get("camera_follow") or {}
    path = simulation_to_true_motion_path(sim)
    return {
        "performance": path.get("performance") or "walk_explain",
        "camera": cam.get("true_motion_camera") or "tracking",
        "performance_path": path,
        "actor_driven": True,
        "not_ken_burns_only": True,
        "camera_follow_mode": cam.get("mode"),
        "character_performance_engine": True,
        "environment_life_channels": list((package.get("environment_life") or {}).get("channels") or []),
    }
