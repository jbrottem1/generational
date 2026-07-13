"""Annotation overlays for real scientific images."""

from __future__ import annotations

from typing import Any

from PIL import ImageDraw


def _font(size: int = 22):
    from PIL import ImageFont

    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


def draw_highlight_box(
    d: ImageDraw.ImageDraw,
    rect: tuple[int, int, int, int],
    *,
    color: tuple[int, int, int] = (220, 50, 40),
    width: int = 4,
    label: str = "",
) -> None:
    x0, y0, x1, y1 = rect
    d.rounded_rectangle(rect, radius=8, outline=color, width=width)
    if label:
        d.text((x0, y0 - 24), label, fill=color, font=_font(20))


def draw_circle(
    d: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    radius: int,
    *,
    color: tuple[int, int, int] = (220, 50, 40),
    width: int = 4,
) -> None:
    d.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=color, width=width)


def draw_arrow(
    d: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    color: tuple[int, int, int] = (20, 40, 90),
    width: int = 4,
) -> None:
    d.line((start, end), fill=color, width=width)
    ex, ey = end
    sx, sy = start
    import math

    angle = math.atan2(ey - sy, ex - sx)
    head = 14
    for da in (2.6, -2.6):
        ax = ex - head * math.cos(angle + da)
        ay = ey - head * math.sin(angle + da)
        d.line((end, (int(ax), int(ay))), fill=color, width=width)


def draw_label(
    d: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    *,
    color: tuple[int, int, int] = (20, 28, 40),
    size: int = 22,
    badge: bool = True,
) -> None:
    font = _font(size)
    if badge:
        bbox = d.textbbox((x, y), text, font=font)
        pad = 6
        d.rounded_rectangle(
            (bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad),
            radius=6,
            fill=(255, 255, 255),
            outline=(35, 40, 50),
            width=2,
        )
    d.text((x, y), text, fill=color, font=font)


def apply_annotations(
    d: ImageDraw.ImageDraw,
    annotations: list[dict[str, Any]],
    *,
    reveal: float = 1.0,
) -> None:
    """Draw timed annotations when reveal fraction > 0."""
    if reveal <= 0:
        return
    for ann in annotations:
        start = float(ann.get("start") or 0.0)
        if reveal < start:
            continue
        kind = str(ann.get("kind") or "")
        if kind == "highlight":
            draw_highlight_box(
                d,
                tuple(ann["rect"]),
                color=tuple(ann.get("color") or (220, 50, 40)),
                label=str(ann.get("label") or ""),
            )
        elif kind == "circle":
            draw_circle(
                d,
                int(ann["cx"]),
                int(ann["cy"]),
                int(ann.get("radius") or 40),
                color=tuple(ann.get("color") or (220, 50, 40)),
            )
        elif kind == "arrow":
            draw_arrow(
                d,
                tuple(ann["start"]),
                tuple(ann["end"]),
                color=tuple(ann.get("color") or (20, 40, 90)),
            )
        elif kind == "label":
            draw_label(
                d,
                int(ann["x"]),
                int(ann["y"]),
                str(ann.get("text") or ""),
                color=tuple(ann.get("color") or (20, 28, 40)),
                size=int(ann.get("size") or 22),
            )
