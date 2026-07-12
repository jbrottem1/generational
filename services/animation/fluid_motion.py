"""Project Fluid Motion — animation fundamentals for believable performance.

Ease, anticipation, follow-through, pose blending. Not more motion — better motion.
"""

from __future__ import annotations

import math
from typing import Any


def smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def smootherstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def ease_in_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 3 / 2.0


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_pose(a: dict[str, float], b: dict[str, float], t: float) -> dict[str, float]:
    t = smootherstep(t)
    keys = set(a) | set(b)
    return {k: lerp(float(a.get(k, 0.0)), float(b.get(k, 0.0)), t) for k in keys}


# Normalized arm keypoints relative to shoulder (sx, sy) and body scale.
# Values are offsets in "figure units" (will be scaled by size/1024).
GESTURE_POSES: dict[str, dict[str, float]] = {
    # idle — arms down, relaxed
    "idle": {
        "lx": -80, "ly": 95, "lhx": -95, "lhy": 100,
        "rx": 85, "ry": 88, "rhx": 100, "rhy": 93,
        "brow": 0.0, "lean": 0.0,
    },
    "wave": {
        "lx": -90, "ly": 75, "lhx": -100, "lhy": 85,
        "rx": 105, "ry": -35, "rhx": 120, "rhy": -45,
        "brow": 0.15, "lean": 0.05,
    },
    "point": {
        "lx": -70, "ly": 90, "lhx": -85, "lhy": 100,
        "rx": 130, "ry": 10, "rhx": 175, "rhy": -5,
        "brow": 0.2, "lean": 0.08,
    },
    "think": {
        "lx": -85, "ly": 95, "lhx": -95, "lhy": 105,
        "rx": 55, "ry": 20, "rhx": 40, "rhy": -40,
        "brow": 0.35, "lean": -0.05,
    },
    "present": {
        "lx": -110, "ly": 40, "lhx": -125, "lhy": 43,
        "rx": 110, "ry": 40, "rhx": 125, "rhy": 43,
        "brow": 0.1, "lean": 0.0,
    },
    "push": {
        "lx": 115, "ly": 55, "lhx": 125, "lhy": 60,
        "rx": 120, "ry": 25, "rhx": 130, "rhy": 30,
        "brow": 0.25, "lean": 0.12,
    },
    "react": {
        "lx": -100, "ly": -20, "lhx": -115, "lhy": -30,
        "rx": 100, "ry": -20, "rhx": 115, "rhy": -30,
        "brow": 0.45, "lean": -0.08,
    },
    # write — right hand raised to whiteboard, left relaxed
    "write": {
        "lx": -75, "ly": 95, "lhx": -88, "lhy": 105,
        "rx": 95, "ry": -55, "rhx": 130, "rhy": -70,
        "brow": 0.12, "lean": 0.10,
    },
}


def pose_for(gesture: str) -> dict[str, float]:
    g = (gesture or "idle").lower()
    return dict(GESTURE_POSES.get(g) or GESTURE_POSES["idle"])


class GestureBlender:
    """Crossfade between gestures with anticipation + ease (no snaps)."""

    def __init__(self, blend_sec: float = 0.32, anticipate_sec: float = 0.08):
        self.blend_sec = blend_sec
        self.anticipate_sec = anticipate_sec
        self.current = "idle"
        self.previous = "idle"
        self.changed_at = 0.0

    def update(self, t: float, gesture: str) -> dict[str, Any]:
        g = (gesture or "idle").lower()
        if g != self.current:
            self.previous = self.current
            self.current = g
            self.changed_at = t
        elapsed = t - self.changed_at
        # Anticipation: slight hold / opposite lean into transition
        if elapsed < self.anticipate_sec and self.previous != self.current:
            # Stay mostly on previous with tiny opposite lean
            pose = pose_for(self.previous)
            nxt = pose_for(self.current)
            anti = -0.15
            pose = dict(pose)
            pose["lean"] = float(pose.get("lean", 0)) + anti * (float(nxt.get("lean", 0)) - float(pose.get("lean", 0)))
            return {"pose": pose, "gesture": self.previous, "blend": 0.0, "from": self.previous, "to": self.current}

        u = (elapsed - self.anticipate_sec) / max(1e-6, self.blend_sec)
        if u >= 1.0:
            return {"pose": pose_for(self.current), "gesture": self.current, "blend": 1.0, "from": self.previous, "to": self.current}
        blended = lerp_pose(pose_for(self.previous), pose_for(self.current), ease_in_out_cubic(u))
        # Follow-through: overshoot lean slightly past target near end
        if 0.7 < u < 1.0:
            over = math.sin((u - 0.7) / 0.3 * math.pi) * 0.08
            blended["lean"] = float(blended.get("lean", 0)) * (1.0 + over)
        return {"pose": blended, "gesture": self.current, "blend": u, "from": self.previous, "to": self.current}


class MouthSmoother:
    """EMA mouth openness — reduces jitter, keeps speech tightly aligned.

    Higher ``alpha`` = snappier follow (foundation / educator). Lower = softer.
    Reversible: pass alpha explicitly; defaults unchanged for non-educator.
    """

    def __init__(self, alpha: float = 0.55, *, close_bias: float = 0.0):
        self.alpha = alpha
        self.close_bias = close_bias  # extra weight toward closed when signal drops
        self.value = 0.0

    def update(self, openness: float) -> float:
        o = max(0.0, min(1.0, float(openness)))
        alpha = self.alpha
        # Close slightly faster than open — reduces sticky-open between syllables
        if self.close_bias > 0 and o < self.value:
            alpha = min(0.95, self.alpha + self.close_bias)
        self.value = alpha * o + (1.0 - alpha) * self.value
        return self.value


def breath_scale(t: float, *, professor: bool = True) -> float:
    # Slow calm breath — visible life, not bounce
    amp = 0.004 if professor else 0.01
    return 1.0 + amp * math.sin(2 * math.pi * t / 3.8)


def fluid_life(t: float, *, professor: bool = True) -> dict[str, float]:
    """Subtle continuous life: breath, micro weight, micro head."""
    breath = math.sin(2 * math.pi * t / 3.8)
    weight = math.sin(2 * math.pi * t / 5.2) * (0.35 if professor else 0.7)
    head_bob = breath * (0.18 if professor else 0.5)
    head_tilt = math.sin(2 * math.pi * t / 6.5) * (0.12 if professor else 0.3)
    # Occasional micro eye drift
    eye = math.sin(2 * math.pi * t / 7.0) * 0.4
    return {
        "breath": breath,
        "weight_shift": weight,
        "head_bob_y": head_bob,
        "head_tilt": head_tilt,
        "eye_drift": eye,
    }


def blink_envelope(t: float) -> float:
    """Natural blinks ~every 2.6–3.4s with occasional double."""
    # Primary cycle
    cycle = 3.0
    phase = t % cycle
    blink = 0.0
    if 0.04 < phase < 0.16:
        x = (phase - 0.04) / 0.12
        blink = max(blink, 1.0 - abs(2 * x - 1.0))
    # Rare double blink every ~11s
    dcycle = 11.0
    dphase = t % dcycle
    if 5.2 < dphase < 5.32:
        x = (dphase - 5.2) / 0.12
        blink = max(blink, 1.0 - abs(2 * x - 1.0))
    return float(blink)


def eased_walk_stride(t: float, walk_amt: float) -> float:
    if walk_amt <= 0:
        return 0.0
    # Soft sine with ease — no hard plant snaps
    raw = math.sin(2 * math.pi * t * 1.35)
    return raw * walk_amt * 0.92
