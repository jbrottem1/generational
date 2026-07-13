"""Whiteboard writing animation — stroke-reveal text synced to narration.

Primary teaching surface for PROJECT FOUNDATION (no scenery, no effects).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from PIL import Image, ImageDraw, ImageFont


def _font(size: int = 42):
    for path in (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ):
        try:
            return ImageFont.truetype(path, size)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


@dataclass
class BoardAction:
    """One timed writing / emphasis action on the board."""

    kind: str  # write | equation | circle | underline | erase | diagram
    text: str = ""
    start: float = 0.0  # normalized 0–1
    end: float = 1.0
    row: int = 0
    color: tuple[int, int, int] = (20, 28, 40)
    size: int = 44
    extras: dict[str, Any] = field(default_factory=dict)


def board_rect(width: int, height: int) -> tuple[int, int, int, int]:
    """Canonical whiteboard frame — right two-thirds, upper half."""
    return (
        int(width * 0.38),
        int(height * 0.08),
        int(width * 0.96),
        int(height * 0.48),
    )


def draw_whiteboard_frame(canvas: Image.Image) -> tuple[int, int, int, int]:
    """Pure white board with thin dark frame. Returns (x0,y0,x1,y1)."""
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    rect = board_rect(w, h)
    x0, y0, x1, y1 = rect
    # Soft shadow
    d.rounded_rectangle(
        (x0 + 6, y0 + 8, x1 + 6, y1 + 8),
        radius=10,
        fill=(220, 222, 226),
    )
    d.rounded_rectangle(
        rect,
        radius=10,
        fill=(255, 255, 255),
        outline=(35, 40, 50),
        width=4,
    )
    # Tray
    d.rectangle((x0 + 20, y1 - 6, x1 - 20, y1 + 14), fill=(55, 60, 70))
    return rect


def _reveal_fraction(p: float, start: float, end: float) -> float:
    if p < start:
        return 0.0
    if p >= end:
        return 1.0
    return (p - start) / max(1e-6, end - start)


def _ease_write(frac: float) -> float:
    """Slight ease-in so early strokes feel deliberate (marker contact)."""
    f = max(0.0, min(1.0, frac))
    return f * f * (3.0 - 2.0 * f)


def write_window_from_plan(plan: list[dict[str, Any]], *, label: str = "write") -> dict[str, float]:
    """Return first choreography write window {start, end} for board sync."""
    for beat in plan:
        gesture = str(beat.get("gesture") or "")
        if gesture == "write" or label in str(beat.get("label") or ""):
            return {"start": float(beat["start"]), "end": float(beat["end"])}
    return {"start": 0.22, "end": 0.42}


def align_equation_to_write_beat(
    actions: list[BoardAction],
    write_start: float,
    write_end: float,
) -> list[BoardAction]:
    """Snap equation (+ optional underline) into the write choreography beat.

    Keeps non-equation rows untouched. Equation stroke fills ~70% of the write
    window; underline occupies the trailing ~30% when present.
    """
    span = max(0.06, write_end - write_start)
    eq_end = write_start + span * 0.72
    out: list[BoardAction] = []
    for action in actions:
        if action.kind == "equation":
            out.append(
                BoardAction(
                    action.kind,
                    action.text,
                    start=write_start,
                    end=eq_end,
                    row=action.row,
                    color=action.color,
                    size=action.size,
                    extras=dict(action.extras),
                )
            )
        elif action.kind == "underline" and action.text:
            # Underline right after equation, still inside write beat
            out.append(
                BoardAction(
                    action.kind,
                    action.text,
                    start=eq_end,
                    end=write_end,
                    row=action.row,
                    color=action.color,
                    size=action.size,
                    extras=dict(action.extras),
                )
            )
        else:
            out.append(action)
    return out


def _draw_partial_text(
    d: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    *,
    frac: float,
    fill: tuple[int, int, int],
    size: int,
    stroke_tokens: bool = False,
) -> tuple[int, int]:
    """Reveal characters left-to-right; return full text bbox size.

    When ``stroke_tokens`` is True (equations), reveal symbol groups
    (F, =, m, ×, a) on beat edges for clearer write choreography sync.
    """
    font = _font(size)
    frac = _ease_write(frac)
    if stroke_tokens:
        tokens = [t for t in text.replace("×", " × ").replace("=", " = ").split(" ") if t]
        if not tokens:
            tokens = list(text)
        n = max(1, len(tokens))
        shown_n = max(0, min(n, int(round(frac * n))))
        # Partial token: grow last visible token mid-stroke
        rem = (frac * n) - shown_n
        parts: list[str] = []
        for i, tok in enumerate(tokens):
            if i < shown_n:
                parts.append(tok)
            elif i == shown_n and rem > 0.15:
                cut = max(1, int(round(rem * len(tok))))
                parts.append(tok[:cut])
                break
            else:
                break
        visible = " ".join(parts)
        # Normalize double spaces from token join of "=" etc.
        while "  " in visible:
            visible = visible.replace("  ", " ")
    else:
        n = max(1, len(text))
        shown = max(0, min(n, int(round(frac * n))))
        visible = text[:shown]
    if visible:
        d.text(xy, visible, fill=fill, font=font)
    # Cursor tick while writing
    if 0.02 < frac < 0.98 and visible:
        bbox = d.textbbox(xy, visible, font=font)
        cx = bbox[2] + 4
        cy0, cy1 = bbox[1] + 4, bbox[3] - 2
        d.line((cx, cy0, cx, cy1), fill=fill, width=3)
    full = d.textbbox(xy, text, font=font)
    return full[2] - full[0], full[3] - full[1]


def _draw_cart_diagram(
    d: ImageDraw.ImageDraw,
    rect: tuple[int, int, int, int],
    *,
    loaded: bool,
    force_arrow: bool,
    p_local: float,
) -> None:
    x0, y0, x1, y1 = rect
    cx = int((x0 + x1) * 0.55)
    by = int(y1 - 70)
    # Cart body
    bw = 90 if loaded else 70
    bh = 50 if loaded else 40
    d.rounded_rectangle((cx - bw, by - bh, cx + bw, by), radius=6, outline=(30, 35, 45), width=3, fill=(248, 250, 252))
    # Wheels
    for wx in (cx - bw // 2, cx + bw // 2):
        d.ellipse((wx - 14, by - 4, wx + 14, by + 24), outline=(30, 35, 45), width=3)
    if loaded:
        # Boxes
        d.rectangle((cx - 40, by - bh - 28, cx - 5, by - bh), outline=(30, 35, 45), width=2)
        d.rectangle((cx + 5, by - bh - 36, cx + 45, by - bh), outline=(30, 35, 45), width=2)
        d.text((cx - 28, by - bh - 58), "heavy", fill=(80, 40, 40), font=_font(22))
    else:
        d.text((cx - 30, by - bh - 32), "empty", fill=(40, 80, 50), font=_font(22))
    if force_arrow:
        tip = int(cx - bw - 10 - 40 * (1.0 - min(1.0, p_local)))
        d.line((tip - 50, by - bh // 2, tip, by - bh // 2), fill=(200, 50, 40), width=6)
        d.polygon(
            [(tip, by - bh // 2 - 12), (tip + 18, by - bh // 2), (tip, by - bh // 2 + 12)],
            fill=(200, 50, 40),
        )
        d.text((tip - 48, by - bh - 28), "F", fill=(180, 40, 30), font=_font(28))


def render_board_actions(
    canvas: Image.Image,
    actions: list[BoardAction],
    p: float,
) -> None:
    """Draw whiteboard + progressive actions for normalized time p."""
    rect = draw_whiteboard_frame(canvas)
    d = ImageDraw.Draw(canvas)
    x0, y0, x1, y1 = rect
    row_h = 58
    left = x0 + 28
    top = y0 + 28

    for action in actions:
        frac = _reveal_fraction(p, action.start, action.end)
        if frac <= 0:
            continue
        # Erase: fade prior content by covering with white (partial)
        if action.kind == "erase":
            if frac > 0.05:
                d.rounded_rectangle(
                    (x0 + 10, y0 + 10, x1 - 10, y1 - 20),
                    radius=6,
                    fill=(255, 255, 255),
                )
            continue

        y = top + action.row * row_h
        if action.kind in ("write", "equation"):
            _draw_partial_text(
                d,
                action.text,
                (left, y),
                frac=frac,
                fill=action.color,
                size=action.size,
                stroke_tokens=(action.kind == "equation"),
            )
        elif action.kind == "underline" and frac > 0.15:
            font = _font(action.size)
            bbox = d.textbbox((left, y), action.text, font=font)
            uw = int((bbox[2] - bbox[0]) * min(1.0, (frac - 0.15) / 0.85))
            d.line((left, bbox[3] + 4, left + uw, bbox[3] + 4), fill=action.color, width=4)
        elif action.kind == "circle" and frac > 0.1:
            font = _font(action.size)
            bbox = d.textbbox((left, y), action.text, font=font)
            pad = 10
            # Progressive ellipse arc via polygon approximation
            cx = (bbox[0] + bbox[2]) // 2
            cy = (bbox[1] + bbox[3]) // 2
            rx = (bbox[2] - bbox[0]) // 2 + pad
            ry = (bbox[3] - bbox[1]) // 2 + pad
            import math

            steps = max(8, int(48 * frac))
            pts = []
            for i in range(steps + 1):
                ang = -math.pi / 2 + 2 * math.pi * (i / 48)
                pts.append((cx + int(rx * math.cos(ang)), cy + int(ry * math.sin(ang))))
            if len(pts) >= 2:
                d.line(pts, fill=(200, 50, 40), width=4)
        elif action.kind == "diagram":
            style = str(action.extras.get("style") or "empty_cart")
            _draw_cart_diagram(
                d,
                rect,
                loaded=style == "loaded_cart",
                force_arrow=bool(action.extras.get("force")),
                p_local=frac,
            )
