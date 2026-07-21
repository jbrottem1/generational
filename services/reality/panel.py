"""Reality panel renderer — real images beside the professor."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from PIL import Image, ImageDraw

from services.reality.annotate import apply_annotations
from services.reality.catalog import RealityImage, get_image

_IMAGE_CACHE: dict[str, Image.Image] = {}


def _board_rect(width: int, height: int) -> tuple[int, int, int, int]:
    return (
        int(width * 0.38),
        int(height * 0.08),
        int(width * 0.96),
        int(height * 0.48),
    )


def _load_rgb(path) -> Image.Image:
    key = str(path)
    if key not in _IMAGE_CACHE:
        _IMAGE_CACHE[key] = Image.open(path).convert("RGB")
    return _IMAGE_CACHE[key].copy()


def _reveal_fraction(p: float, start: float, end: float) -> float:
    """Visibility with fade-out — panels must not persist forever after end."""
    from services.animation.layout_engine import visibility_envelope

    return visibility_envelope(p, start, end, fade_in=0.02, fade_out=0.035)


def _ease(f: float) -> float:
    f = max(0.0, min(1.0, f))
    return f * f * (3.0 - 2.0 * f)


def _fit_image(img: Image.Image, rect: tuple[int, int, int, int]) -> Image.Image:
    x0, y0, x1, y1 = rect
    tw, th = x1 - x0, y1 - y0
    iw, ih = img.size
    scale = min(tw / max(iw, 1), th / max(ih, 1))
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    out = Image.new("RGB", (tw, th), (248, 249, 252))
    ox, oy = (tw - nw) // 2, (th - nh) // 2
    out.paste(resized, (ox, oy))
    return out


def _panel_frame(d: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], *, title: str = "") -> None:
    x0, y0, x1, y1 = rect
    d.rounded_rectangle(
        (x0 + 4, y0 + 6, x1 + 4, y1 + 6),
        radius=10,
        fill=(225, 228, 234),
    )
    d.rounded_rectangle(rect, radius=10, fill=(255, 255, 255), outline=(35, 40, 50), width=3)
    if title:
        from services.reality.annotate import draw_label

        draw_label(d, x0 + 10, y0 + 8, title, size=20, badge=False)


@dataclass
class RealityPanel:
    """Timed real-image presentation spec."""

    layout: str  # board_inset | split_compare | evidence_tray
    start: float = 0.0
    end: float = 1.0
    image_ids: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)  # DANGEROUS / HARMLESS / MODEL / MIMIC
    title: str = ""
    annotations: list[dict[str, Any]] = field(default_factory=list)


def evidence_tray_rect(canvas_w: int, canvas_h: int) -> tuple[int, int, int, int]:
    """Lower board tray for photo evidence below whiteboard text."""
    bx0, _by0, bx1, by1 = _board_rect(canvas_w, canvas_h)
    return (bx0 + 12, by1 + 24, bx1 - 12, int(canvas_h * 0.78))


def split_panels(parent: tuple[int, int, int, int]) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    x0, y0, x1, y1 = parent
    mid = x0 + (x1 - x0) // 2
    gap = 8
    left = (x0, y0, mid - gap, y1)
    right = (mid + gap, y0, x1, y1)
    return left, right


def draw_reality_panel(
    canvas: Image.Image,
    panel: RealityPanel,
    p: float,
    *,
    layout_rect_fn=None,
) -> None:
    """Draw a timed reality panel onto the canvas."""
    frac = _ease(_reveal_fraction(p, panel.start, panel.end))
    if frac <= 0:
        return

    w, h = canvas.size
    d = ImageDraw.Draw(canvas)
    tray_fn = layout_rect_fn or evidence_tray_rect

    if panel.layout == "board_inset":
        rect = tray_fn(w, h)
        _panel_frame(d, rect, title=panel.title)
        if panel.image_ids:
            img = _load_rgb(get_image(panel.image_ids[0]).path)  # type: ignore[union-attr]
            fitted = _fit_image(img, (rect[0] + 8, rect[1] + 36, rect[2] - 8, rect[3] - 8))
            canvas.paste(fitted, (rect[0] + 8, rect[1] + 36))
            if panel.labels:
                from services.reality.annotate import draw_label

                draw_label(d, rect[0] + 16, rect[3] - 34, panel.labels[0], size=20)
        apply_annotations(d, panel.annotations, reveal=frac)

    elif panel.layout == "split_compare":
        rect = tray_fn(w, h)
        _panel_frame(d, rect, title=panel.title or "Compare")
        left, right = split_panels((rect[0] + 8, rect[1] + 36, rect[2] - 8, rect[3] - 8))
        for idx, slot in enumerate((left, right)):
            if idx >= len(panel.image_ids):
                break
            entry = get_image(panel.image_ids[idx])
            if entry is None:
                continue
            fitted = _fit_image(_load_rgb(entry.path), slot)
            canvas.paste(fitted, (slot[0], slot[1]))
            label = panel.labels[idx] if idx < len(panel.labels) else entry.organism
            tag = panel.tags[idx] if idx < len(panel.tags) else ""
            from services.reality.annotate import draw_label

            draw_label(d, slot[0] + 6, slot[1] + 6, label, size=18)
            if tag:
                color = (180, 40, 40) if "DANGER" in tag.upper() else (40, 100, 60)
                draw_label(d, slot[0] + 6, slot[3] - 30, tag, size=16, color=color)
        apply_annotations(d, panel.annotations, reveal=frac)

    elif panel.layout == "evidence_tray":
        draw_reality_panel(
            canvas,
            RealityPanel(
                layout="board_inset",
                start=panel.start,
                end=panel.end,
                image_ids=panel.image_ids,
                labels=panel.labels,
                title=panel.title,
                annotations=panel.annotations,
            ),
            p,
        )


def draw_panels(
    canvas: Image.Image,
    panels: list[RealityPanel],
    p: float,
    *,
    layout_rect_fn=None,
) -> None:
    for panel in panels:
        draw_reality_panel(canvas, panel, p, layout_rect_fn=layout_rect_fn)
