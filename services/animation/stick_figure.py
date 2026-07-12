"""Reusable minimalist stick-figure character plate (Generational Universe)."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


@dataclass(frozen=True)
class StickFigureSpec:
    """Locked proportions for the first reusable animated character."""

    character_id: str = "CHAR-STICK-001"
    name: str = "Stick"
    outline: tuple[int, int, int, int] = (0, 0, 0, 255)
    face_fill: tuple[int, int, int, int] = (255, 255, 255, 255)
    stroke: int = 7
    head_ratio: float = 0.34
    # Gen Foundation lock: attire="none". Opt-in MacroCenter coat via "lab_coat" + version bump.
    attire: str = "none"

    def to_registry(self) -> dict[str, Any]:
        return asdict(self)


def _resolve_draw_coat(*, coat: bool, attire: str | None, spec: StickFigureSpec) -> bool:
    """Lab coat is gated — professor=True alone never draws a coat.

    Opt in with coat=True or attire=\"lab_coat\" (draw arg or StickFigureSpec).
    """
    resolved = (attire if attire is not None else spec.attire or "none").strip().lower()
    if coat or resolved in ("lab_coat", "coat"):
        return True
    return False


def draw_stick_figure(
    *,
    size: int = 1024,
    mouth_open: float = 0.0,
    blink: float = 0.0,
    head_tilt: float = 0.0,
    head_bob_y: float = 0.0,
    arm_phase: float = 0.0,
    weight_shift: float = 0.0,
    gesture: str = "idle",
    walk_stride: float = 0.0,
    confident: bool = False,
    professor: bool = False,
    coat: bool = False,
    attire: str | None = None,
    windy: bool = False,
    foundation_v2: bool = False,
    pose: dict[str, float] | None = None,
    eye_drift: float = 0.0,
    brow_raise: float = 0.0,
    spec: StickFigureSpec | None = None,
) -> Image.Image:
    """Draw one performance frame. mouth_open in [0,1]; blink in [0,1].

    Gestures: idle, wave, point, think, present, push, react, write.
    Optional ``pose`` (from fluid_motion) enables blended arm keypoints — no snaps.

    Attire: Gen Foundation defaults to clean stick (coat=False, attire=\"none\").
    MacroCenter may opt in later with coat=True or attire=\"lab_coat\".
    """
    spec = spec or StickFigureSpec()
    draw_coat = _resolve_draw_coat(coat=coat, attire=attire, spec=spec)
    mouth_open = max(0.0, min(1.0, float(mouth_open)))
    blink = max(0.0, min(1.0, float(blink)))
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    scale = size / 1024.0
    bob_scale = 0.005 if (confident or professor) else 0.012
    wind_lean = int(size * 0.012 * math.sin(arm_phase * 2 + 1)) if windy else 0
    pose_lean = float((pose or {}).get("lean", 0.0)) * size * 0.02
    cx = size // 2 + int(weight_shift * size * 0.015) + wind_lean + int(pose_lean)
    cy = int(size * 0.32) + int(head_bob_y * size * bob_scale) + int(head_tilt * 3)
    if windy:
        cy += int(6 * abs(math.sin(arm_phase * 3)))
    head_r = int(size * spec.head_ratio * (0.48 if foundation_v2 else 0.46))
    stroke = spec.stroke + (1 if professor else 0)

    # Head
    d.ellipse(
        (cx - head_r, cy - head_r, cx + head_r, cy + head_r),
        fill=spec.face_fill,
        outline=spec.outline,
        width=stroke,
    )

    # Eyes
    eye_h = max(2, int(34 * (1.0 - 0.92 * blink)))
    eye_w = 46
    eye_y = cy - int(head_r * 0.10)
    if professor:
        pupil_dx = 5 + int(eye_drift * 3)
    elif confident:
        pupil_dx = 2 + int(eye_drift * 2)
    else:
        pupil_dx = int(arm_phase * 3)
    for ex in (cx - int(head_r * 0.52), cx + int(head_r * 0.06)):
        d.ellipse(
            (ex, eye_y - eye_h // 2, ex + eye_w, eye_y + eye_h // 2),
            fill=spec.face_fill,
            outline=spec.outline,
            width=max(3, stroke - 2),
        )
        if blink < 0.75:
            pupil = 17
            d.ellipse(
                (ex + 13 + pupil_dx, eye_y - pupil // 2, ex + 13 + pupil + pupil_dx, eye_y + pupil // 2),
                fill=spec.outline,
            )

    # Brows — raise with expression
    brow_y = cy - int(head_r * 0.52) + int(head_tilt * 2) - int(brow_raise * 8)
    d.line((cx - 72, brow_y + 2, cx - 20, brow_y - 2 - int(brow_raise * 4)), fill=spec.outline, width=stroke)
    d.line((cx + 16, brow_y - 2 - int(brow_raise * 4), cx + 70, brow_y + 2), fill=spec.outline, width=stroke)

    # Mouth
    mouth_cx, mouth_cy = cx, cy + int(head_r * 0.40)
    if mouth_open < 0.12:
        smile_lift = 4 if (confident or professor) else 0
        d.arc(
            (mouth_cx - 34, mouth_cy - 10 - smile_lift, mouth_cx + 34, mouth_cy + 22 - smile_lift),
            25,
            155,
            fill=spec.outline,
            width=max(4, stroke - 2),
        )
    else:
        ow = 26 + int(20 * mouth_open)
        oh = 5 + int(32 * mouth_open)
        if professor:
            ow = int(ow * 1.08)
        d.ellipse(
            (mouth_cx - ow, mouth_cy - oh // 3, mouth_cx + ow, mouth_cy + oh),
            fill=spec.outline,
            outline=spec.outline,
            width=2,
        )
        if mouth_open > 0.35:
            d.ellipse(
                (mouth_cx - ow + 8, mouth_cy, mouth_cx + ow - 8, mouth_cy + max(4, oh - 10)),
                fill=(40, 40, 40, 255),
            )

    # Torso — lab coat is opt-in only (coat=True / attire=lab_coat); Gen stays clean stick
    body_top = cy + head_r
    body_bot = int(size * 0.68)
    if draw_coat:
        coat_fill = (245, 248, 252, 230)
        flutter = int(18 * math.sin(arm_phase * 4)) if windy else 0
        d.polygon(
            [
                (cx - 70, body_top + 20),
                (cx + 70, body_top + 20),
                (cx + 85 + flutter, body_bot + 10),
                (cx - 85 - flutter, body_bot + 10),
            ],
            fill=coat_fill,
            outline=spec.outline,
        )
        d.line((cx - 25, body_top + 28, cx - 35, body_bot), fill=(64, 196, 180, 255), width=4)
        d.line((cx + 25, body_top + 28, cx + 35, body_bot), fill=(64, 196, 180, 255), width=4)
        # Simple tie (Foundation V2)
        if foundation_v2:
            d.polygon(
                [(cx - 8, body_top + 32), (cx + 8, body_top + 32), (cx, body_top + 58)],
                fill=(30, 50, 120, 255),
                outline=spec.outline,
            )
            d.polygon(
                [(cx - 10, body_top + 58), (cx + 10, body_top + 58), (cx, body_top + 78)],
                fill=(30, 50, 120, 255),
            )
    d.line((cx, body_top, cx, body_bot), fill=spec.outline, width=stroke + 1)

    shoulder = body_top + 34
    sx, sy = cx, shoulder

    if pose is not None:
        # Fluid blended arms from keypoints
        def _pt(key_x: str, key_y: str):
            return (
                sx + int(float(pose[key_x]) * scale),
                sy + int(float(pose[key_y]) * scale),
            )

        lx, ly = _pt("lx", "ly")
        lhx, lhy = _pt("lhx", "lhy")
        rx, ry = _pt("rx", "ry")
        rhx, rhy = _pt("rhx", "rhy")
        d.line((sx, sy, lx, ly), fill=spec.outline, width=stroke)
        d.line((lx, ly, lhx, lhy), fill=spec.outline, width=max(3, stroke - 1))
        d.ellipse((lhx - 12, lhy - 12, lhx + 12, lhy + 12), outline=spec.outline, width=stroke - 1)
        d.line((sx, sy, rx, ry), fill=spec.outline, width=stroke)
        d.line((rx, ry, rhx, rhy), fill=spec.outline, width=max(3, stroke - 1))
        d.ellipse((rhx - 12, rhy - 12, rhx + 12, rhy + 12), outline=spec.outline, width=stroke - 1)
    else:
        # Legacy discrete gestures
        sway = int((3 if (confident or professor) else 14) * arm_phase)
        g = (gesture or "idle").lower()
        if g == "wave":
            d.line((cx, shoulder, cx - 90, shoulder + 75), fill=spec.outline, width=stroke)
            d.line((cx, shoulder, cx + 105, shoulder - 35 - sway), fill=spec.outline, width=stroke)
            d.ellipse((cx + 95, shoulder - 50 - sway, cx + 125, shoulder - 20 - sway), outline=spec.outline, width=stroke - 1)
        elif g == "point":
            d.line((cx, shoulder, cx - 70, shoulder + 90), fill=spec.outline, width=stroke)
            d.line((cx, shoulder, cx + 130, shoulder + 10), fill=spec.outline, width=stroke)
            d.line((cx + 130, shoulder + 10, cx + 175, shoulder - 5), fill=spec.outline, width=stroke - 1)
            d.ellipse((cx + 168, shoulder - 18, cx + 190, shoulder + 4), outline=spec.outline, width=4)
        elif g == "think":
            d.line((cx, shoulder, cx + 55, shoulder + 20), fill=spec.outline, width=stroke)
            d.line((cx + 55, shoulder + 20, cx + 40, cy + 10), fill=spec.outline, width=stroke)
            d.ellipse((cx + 28, cy - 5, cx + 55, cy + 22), outline=spec.outline, width=stroke - 1)
            d.line((cx, shoulder, cx - 85, shoulder + 95), fill=spec.outline, width=stroke)
        elif g == "present":
            d.line((cx, shoulder, cx - 110, shoulder + 40), fill=spec.outline, width=stroke)
            d.line((cx, shoulder, cx + 110, shoulder + 40), fill=spec.outline, width=stroke)
            d.ellipse((cx - 125, shoulder + 28, cx - 95, shoulder + 58), outline=spec.outline, width=stroke - 1)
            d.ellipse((cx + 95, shoulder + 28, cx + 125, shoulder + 58), outline=spec.outline, width=stroke - 1)
        elif g == "push":
            d.line((cx, shoulder, cx + 120, shoulder + 25), fill=spec.outline, width=stroke)
            d.line((cx, shoulder, cx + 115, shoulder + 55), fill=spec.outline, width=stroke)
            d.ellipse((cx + 115, shoulder + 15, cx + 145, shoulder + 45), outline=spec.outline, width=stroke - 1)
            d.ellipse((cx + 110, shoulder + 45, cx + 140, shoulder + 75), outline=spec.outline, width=stroke - 1)
        elif g == "react":
            d.line((cx, shoulder, cx - 100, shoulder - 20), fill=spec.outline, width=stroke)
            d.line((cx, shoulder, cx + 100, shoulder - 20), fill=spec.outline, width=stroke)
            d.ellipse((cx - 115, shoulder - 35, cx - 85, shoulder - 5), outline=spec.outline, width=stroke - 1)
            d.ellipse((cx + 85, shoulder - 35, cx + 115, shoulder - 5), outline=spec.outline, width=stroke - 1)
        elif g == "write":
            # Left arm idle; right arm raised to board with chalk micro-motion
            chalk = int(8 * math.sin(arm_phase * 6))
            d.line((cx, shoulder, cx - 80, shoulder + 95), fill=spec.outline, width=stroke)
            d.line((cx, shoulder, cx + 95, shoulder - 55 + chalk // 2), fill=spec.outline, width=stroke)
            d.line((cx + 95, shoulder - 55 + chalk // 2, cx + 130, shoulder - 70 + chalk), fill=spec.outline, width=max(3, stroke - 1))
            d.ellipse((cx + 122, shoulder - 82 + chalk, cx + 146, shoulder - 58 + chalk), outline=spec.outline, width=stroke - 1)
        else:
            d.line((cx, shoulder, cx - 80 + sway // 2, shoulder + 95), fill=spec.outline, width=stroke)
            d.line((cx, shoulder, cx + 85 - sway // 2, shoulder + 88 + sway // 2), fill=spec.outline, width=stroke)
            d.ellipse((cx - 95, shoulder + 85, cx - 65, shoulder + 115), outline=spec.outline, width=stroke - 1)
            d.ellipse((cx + 70, shoulder + 78, cx + 100, shoulder + 108), outline=spec.outline, width=stroke - 1)

    # Foundation V2 — clipboard + teaching pointer (professional, purposeful)
    if foundation_v2 and pose is not None:
        def _pt(key_x: str, key_y: str):
            return (
                sx + int(float(pose[key_x]) * scale),
                sy + int(float(pose[key_y]) * scale),
            )

        lhx, lhy = _pt("lhx", "lhy")
        rhx, rhy = _pt("rhx", "rhy")
        g = (gesture or "idle").lower()
        if g != "write":
            # Clipboard in left hand
            cb_w, cb_h = 36, 48
            d.rounded_rectangle(
                (lhx - cb_w // 2, lhy - cb_h, lhx + cb_w // 2, lhy + 4),
                radius=4,
                fill=(248, 250, 252, 255),
                outline=spec.outline,
                width=3,
            )
            d.line(
                (lhx - cb_w // 2 + 6, lhy - cb_h + 14, lhx + cb_w // 2 - 6, lhy - cb_h + 14),
                fill=(180, 185, 195),
                width=2,
            )
            d.line(
                (lhx - cb_w // 2 + 6, lhy - cb_h + 24, lhx + cb_w // 2 - 6, lhy - cb_h + 24),
                fill=(180, 185, 195),
                width=2,
            )
        if g in ("point", "write", "present"):
            # Teaching pointer — extends from right hand
            tip_x = rhx + int(55 * scale)
            tip_y = rhy - int(8 * scale)
            d.line((rhx, rhy, tip_x, tip_y), fill=(50, 50, 55), width=max(3, stroke - 2))
            d.polygon(
                [
                    (tip_x + int(12 * scale), tip_y),
                    (tip_x - int(6 * scale), tip_y - int(8 * scale)),
                    (tip_x - int(6 * scale), tip_y + int(8 * scale)),
                ],
                fill=(210, 45, 35, 255),
            )

    # Legs — grounded; soft stride
    foot_y = int(size * 0.92)
    stride = int(walk_stride * 55)
    shift = int(weight_shift * (10 if (confident or professor) else 22))
    d.line((cx, body_bot, cx - 55 + shift - stride, foot_y), fill=spec.outline, width=stroke)
    d.line((cx, body_bot, cx + 55 + shift + stride, foot_y), fill=spec.outline, width=stroke)
    d.ellipse((cx - 78 + shift - stride, foot_y - 8, cx - 38 + shift - stride, foot_y + 10), fill=spec.outline)
    d.ellipse((cx + 38 + shift + stride, foot_y - 8, cx + 78 + shift + stride, foot_y + 10), fill=spec.outline)

    return img


def save_turnaround_sheet(
    path: Path,
    *,
    size: int = 512,
    professor: bool = False,
    coat: bool = False,
    spec: StickFigureSpec | None = None,
) -> Path:
    """Save a simple front plate as the v1 reusable asset (Gen: professor, no coat)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    draw_stick_figure(
        size=size,
        mouth_open=0.0,
        professor=professor,
        coat=coat,
        spec=spec,
    ).save(path)
    return path
