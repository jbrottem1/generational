"""Foundation Visual System V2 — baby-blue studio, keyword board, teaching pointer.

Calming backdrop. Professor left. Teaching visuals right. Minimal on-screen text.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from PIL import Image, ImageDraw

from services.animation.whiteboard import BoardAction, _ease_write, _font, _reveal_fraction


# Soft baby-blue studio — high contrast for dark text, calm for learning
STUDIO_BLUE_TOP = (228, 240, 252)
STUDIO_BLUE_BOTTOM = (205, 228, 248)
STUDIO_FLOOR = (190, 210, 228)
STUDIO_FLOOR_LINE = (165, 185, 205)

# Canonical V2 layout (1080×1920 vertical Short)
PROFESSOR_X_MAX = 0.32
CONTENT_X_MIN = 0.34
CONTENT_X_MAX = 0.96
MARGIN_Y_TOP = 0.06
MARGIN_Y_BOTTOM = 0.82


def is_foundation_v2_demo(demo_id: str | None) -> bool:
    return str(demo_id or "").startswith("foundation_v2_")


def draw_foundation_v2_studio(canvas: Image.Image) -> int:
    """Soft baby-blue gradient studio. Returns floor_y for character feet."""
    w, h = canvas.size
    d = ImageDraw.Draw(canvas)
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(STUDIO_BLUE_TOP[0] * (1 - t) + STUDIO_BLUE_BOTTOM[0] * t)
        g = int(STUDIO_BLUE_TOP[1] * (1 - t) + STUDIO_BLUE_BOTTOM[1] * t)
        b = int(STUDIO_BLUE_TOP[2] * (1 - t) + STUDIO_BLUE_BOTTOM[2] * t)
        d.line((0, y, w, y), fill=(r, g, b))

    floor_y = int(h * MARGIN_Y_BOTTOM)
    d.rectangle((0, floor_y, w, h), fill=STUDIO_FLOOR)
    d.line((0, floor_y, w, floor_y), fill=STUDIO_FLOOR_LINE, width=2)
    return floor_y


def professor_zone_rect(width: int, height: int) -> tuple[int, int, int, int]:
    return (int(width * 0.02), int(height * MARGIN_Y_TOP), int(width * PROFESSOR_X_MAX), floor_y(height))


def content_zone_rect(width: int, height: int) -> tuple[int, int, int, int]:
    return (
        int(width * CONTENT_X_MIN),
        int(height * MARGIN_Y_TOP),
        int(width * CONTENT_X_MAX),
        int(height * 0.78),
    )


def floor_y(height: int) -> int:
    return int(height * MARGIN_Y_BOTTOM)


def board_rect_v2(width: int, height: int) -> tuple[int, int, int, int]:
    """Whiteboard in the right teaching zone — upper content area."""
    cx0, cy0, cx1, _cy1 = content_zone_rect(width, height)
    return (cx0 + 8, cy0 + 8, cx1 - 8, int(height * 0.44))


def evidence_tray_v2(width: int, height: int) -> tuple[int, int, int, int]:
    """Photo / diagram tray below the whiteboard."""
    bx0, _by0, bx1, by1 = board_rect_v2(width, height)
    return (bx0 + 4, by1 + 16, bx1 - 4, int(height * 0.76))


def draw_whiteboard_frame_v2(canvas: Image.Image) -> tuple[int, int, int, int]:
    d = ImageDraw.Draw(canvas)
    rect = board_rect_v2(*canvas.size)
    x0, y0, x1, y1 = rect
    d.rounded_rectangle(
        (x0 + 5, y0 + 7, x1 + 5, y1 + 7),
        radius=12,
        fill=(215, 222, 232),
    )
    d.rounded_rectangle(rect, radius=12, fill=(255, 255, 255), outline=(40, 50, 65), width=3)
    d.rectangle((x0 + 18, y1 - 4, x1 - 18, y1 + 12), fill=(55, 62, 72))
    return rect


def keyword_word_count(text: str) -> int:
    return len([w for w in (text or "").split() if w.strip()])


def clamp_keyword(text: str, *, max_words: int = 8) -> str:
    words = [w for w in (text or "").split() if w.strip()]
    return " ".join(words[:max_words])


def keyword_font_size(text: str, *, base: int = 44, large: int = 62) -> int:
    n = keyword_word_count(text)
    if n <= 2:
        return large
    if n <= 4:
        return int((base + large) / 2)
    return base


@dataclass
class PointerAction:
    """Teaching pointer overlay — tap, underline, circle, trace, point."""

    kind: str  # point | tap | underline | circle | trace
    start: float = 0.0
    end: float = 1.0
    x0: float = 0.55  # normalized canvas coords
    y0: float = 0.30
    x1: float = 0.75
    y1: float = 0.45
    color: tuple[int, int, int] = (210, 45, 35)
    extras: dict[str, Any] = field(default_factory=dict)


def _norm_to_px(canvas: Image.Image, x: float, y: float) -> tuple[int, int]:
    w, h = canvas.size
    return int(x * w), int(y * h)


def render_pointer_actions(canvas: Image.Image, actions: list[PointerAction], p: float) -> None:
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    for action in actions:
        frac = _reveal_fraction(p, action.start, action.end)
        if frac <= 0:
            continue
        x0, y0 = _norm_to_px(canvas, action.x0, action.y0)
        x1, y1 = _norm_to_px(canvas, action.x1, action.y1)
        col = action.color
        kind = action.kind.lower()

        if kind == "point":
            tip_x = int(x0 + (x1 - x0) * min(1.0, frac * 1.2))
            tip_y = int(y0 + (y1 - y0) * min(1.0, frac * 1.2))
            d.line((x0 - 40, y0 + 30, tip_x, tip_y), fill=(50, 50, 55), width=4)
            d.polygon(
                [(tip_x + 14, tip_y), (tip_x - 6, tip_y - 8), (tip_x - 6, tip_y + 8)],
                fill=col,
            )
        elif kind == "tap":
            pulse = 0.5 + 0.5 * math.sin(frac * math.pi * 6)
            r = int(8 + 10 * pulse)
            d.ellipse((x1 - r, y1 - r, x1 + r, y1 + r), outline=col, width=3)
            d.line((x0 - 30, y0 + 20, x1, y1), fill=(50, 50, 55), width=3)
        elif kind == "underline":
            uw = int((x1 - x0) * min(1.0, frac))
            d.line((x0, y1, x0 + uw, y1), fill=col, width=5)
            d.line((x0 - 30, y0 + 20, x0, y1 - 10), fill=(50, 50, 55), width=3)
        elif kind == "circle":
            cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
            rx = abs(x1 - x0) // 2
            ry = abs(y1 - y0) // 2
            steps = max(8, int(40 * frac))
            pts = []
            for i in range(steps + 1):
                ang = -math.pi / 2 + 2 * math.pi * (i / 40)
                pts.append((cx + int(rx * math.cos(ang)), cy + int(ry * math.sin(ang))))
            if len(pts) >= 2:
                d.line(pts, fill=col, width=4)
            d.line((x0 - 30, y0 + 20, cx - rx, cy), fill=(50, 50, 55), width=3)
        elif kind == "trace":
            steps = max(2, int(20 * frac))
            pts = []
            for i in range(steps + 1):
                t = i / 20
                pts.append((int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t + 20 * math.sin(t * math.pi))))
            if len(pts) >= 2:
                d.line(pts, fill=col, width=4)
            d.line((x0 - 30, y0 + 20, pts[0][0], pts[0][1]), fill=(50, 50, 55), width=3)


def render_keyword_board(
    canvas: Image.Image,
    actions: list[BoardAction],
    p: float,
) -> None:
    """Render keyword-only whiteboard (3–8 words max per line)."""
    rect = draw_whiteboard_frame_v2(canvas)
    d = ImageDraw.Draw(canvas)
    x0, y0, x1, y1 = rect
    row_h = 72
    left = x0 + 24
    top = y0 + 24

    for action in actions:
        text = clamp_keyword(action.text)
        if keyword_word_count(text) > 8:
            continue
        frac = _reveal_fraction(p, action.start, action.end)
        if frac <= 0:
            continue
        size = action.size or keyword_font_size(text)
        y = top + action.row * row_h
        if action.kind in ("write", "equation"):
            visible_n = max(0, min(len(text), int(round(_ease_write(frac) * len(text)))))
            visible = text[:visible_n]
            if visible:
                d.text((left, y), visible, fill=action.color, font=_font(size))
        elif action.kind == "underline" and frac > 0.15:
            font = _font(size)
            bbox = d.textbbox((left, y), text, font=font)
            uw = int((bbox[2] - bbox[0]) * min(1.0, (frac - 0.15) / 0.85))
            d.line((left, bbox[3] + 6, left + uw, bbox[3] + 6), fill=action.color, width=5)
        elif action.kind == "circle" and frac > 0.1:
            font = _font(size)
            bbox = d.textbbox((left, y), text, font=font)
            pad = 12
            cx = (bbox[0] + bbox[2]) // 2
            cy = (bbox[1] + bbox[3]) // 2
            rx = (bbox[2] - bbox[0]) // 2 + pad
            ry = (bbox[3] - bbox[1]) // 2 + pad
            steps = max(8, int(48 * frac))
            pts = []
            for i in range(steps + 1):
                ang = -math.pi / 2 + 2 * math.pi * (i / 48)
                pts.append((cx + int(rx * math.cos(ang)), cy + int(ry * math.sin(ang))))
            if len(pts) >= 2:
                d.line(pts, fill=(210, 45, 35), width=4)


def draw_shell_evolution_sketch(canvas: Image.Image, p: float) -> None:
    """Simple whiteboard diagram — gradual shell formation."""
    if p < 0.38 or p > 0.72:
        return
    d = ImageDraw.Draw(canvas)
    rect = evidence_tray_v2(*canvas.size)
    x0, y0, x1, y1 = rect
    # Three stages left → right
    stages = [
        ("No shell", (180, 100, 80)),
        ("Ribs widen", (120, 130, 90)),
        ("Full shell", (60, 110, 70)),
    ]
    step_w = (x1 - x0) // 4
    local = (p - 0.38) / 0.34
    for i, (label, col) in enumerate(stages):
        reveal = max(0.0, min(1.0, local * 3 - i))
        if reveal <= 0:
            continue
        cx = x0 + step_w * (i + 1)
        cy = y0 + (y1 - y0) // 2 + 20
        bw = int(50 + 30 * reveal)
        bh = int(20 + 35 * i * reveal)
        d.ellipse((cx - bw, cy - bh, cx + bw, cy + bh // 2), outline=col, width=3)
        if i >= 1:
            d.arc((cx - bw + 10, cy - bh, cx + bw - 10, cy), 180, 360, fill=col, width=4)
        d.text((cx - 55, y0 + 12), label, fill=(30, 40, 55), font=_font(20))
    # Arrow timeline
    ax0, ax1 = x0 + 40, x1 - 40
    ay = y1 - 30
    d.line((ax0, ay, ax0 + int((ax1 - ax0) * min(1.0, local)), ay), fill=(20, 40, 90), width=3)
    d.text((x0 + 20, y1 - 55), "Millions of years →", fill=(20, 40, 90), font=_font(22))


def draw_timeline_bar(canvas: Image.Image, p: float) -> None:
    """Evolutionary timeline — 250 Ma to present."""
    if p < 0.18 or p > 0.55:
        return
    d = ImageDraw.Draw(canvas)
    rect = evidence_tray_v2(*canvas.size)
    x0, y0, x1, y1 = rect
    bar_y = y0 + 18
    local = (p - 0.18) / 0.37
    bw = int((x1 - x0 - 40) * min(1.0, local))
    d.rounded_rectangle((x0 + 20, bar_y, x0 + 20 + bw, bar_y + 14), radius=6, fill=(20, 40, 90))
    d.text((x0 + 20, bar_y - 22), "250 Ma", fill=(20, 40, 90), font=_font(18))
    d.text((x1 - 80, bar_y - 22), "Today", fill=(20, 40, 90), font=_font(18))
    if local > 0.5:
        d.text((x0 + 60, bar_y + 22), "Early reptiles → turtles", fill=(40, 90, 60), font=_font(20))


# V2 professor defaults
V2_CHARACTER_SCALE = 0.58  # ~26% larger than foundation V1 (0.46)
V2_STICK_SPEC = {
    "character_id": "CHAR-PROFESSOR-V2-001",
    "name": "Professor Gen",
    "attire": "lab_coat",
    "head_ratio": 0.38,
}
