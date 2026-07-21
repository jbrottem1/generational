"""Educational visual layout engine — collision-aware text & region allocation.

Rules:
- Measure every text box before paint
- Never overlap text/labels
- Auto-wrap and downsize fonts when needed
- Respect margins and minimum spacing
- Deduplicate identical labels
- Redesign (drop/relayout) rather than force-fit
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from PIL import Image, ImageDraw, ImageFont

# Layout constants (normalized / px)
MIN_LABEL_GAP_PX = 10
MIN_MARGIN_PX = 12
MIN_FONT_SIZE = 16
MAX_BOARD_ROWS = 4
DEFAULT_ROW_HEIGHT = 70


def _font(size: int = 42) -> ImageFont.ImageFont:
    for path in (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


def visibility_envelope(
    p: float,
    start: float,
    end: float,
    *,
    fade_in: float = 0.02,
    fade_out: float = 0.04,
) -> float:
    """0–1 visibility with fade in/out. Returns 0 outside the educational window.

    Unlike raw reveal-fraction helpers, this does NOT stay at 1.0 forever after end.
    """
    if end <= start:
        end = start + 0.05
    if p < start:
        return 0.0
    if p < start + fade_in:
        return max(0.0, min(1.0, (p - start) / max(fade_in, 1e-6)))
    if p <= end:
        return 1.0
    if p < end + fade_out:
        return max(0.0, min(1.0, 1.0 - (p - end) / max(fade_out, 1e-6)))
    return 0.0


def stroke_reveal(p: float, start: float, end: float) -> float:
    """Progress of a write stroke within [start, end] only (0 outside)."""
    if p < start or p > end + 0.05:
        return 0.0 if p < start else 1.0
    if p >= end:
        return 1.0
    return max(0.0, min(1.0, (p - start) / max(end - start, 1e-6)))


@dataclass
class TextBox:
    """Measured axis-aligned text box in pixel space."""

    text: str
    x: int
    y: int
    w: int
    h: int
    font_size: int
    color: tuple[int, int, int] = (20, 40, 90)
    kind: str = "label"
    row: int = 0
    alpha: float = 1.0
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def rect(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.x + self.w, self.y + self.h)

    def overlaps(self, other: "TextBox", *, gap: int = MIN_LABEL_GAP_PX) -> bool:
        a = self.rect
        b = other.rect
        return not (
            a[2] + gap <= b[0]
            or b[2] + gap <= a[0]
            or a[3] + gap <= b[1]
            or b[3] + gap <= a[1]
        )


def measure_text(text: str, font_size: int) -> tuple[int, int]:
    """Return (width, height) of text at font_size."""
    font = _font(font_size)
    # Use a scratch draw for accurate bbox
    img = Image.new("RGB", (4, 4))
    d = ImageDraw.Draw(img)
    bbox = d.textbbox((0, 0), text or " ", font=font)
    return max(1, bbox[2] - bbox[0]), max(1, bbox[3] - bbox[1])


def wrap_text(text: str, max_width: int, font_size: int) -> list[str]:
    """Word-wrap text to fit max_width pixels."""
    words = [w for w in (text or "").split() if w]
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        tw, _ = measure_text(trial, font_size)
        if tw <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def fit_font_size(
    text: str,
    max_width: int,
    max_height: int,
    *,
    preferred: int,
    minimum: int = MIN_FONT_SIZE,
) -> tuple[int, list[str]]:
    """Shrink font and wrap until text fits the slot. Returns (size, lines)."""
    size = preferred
    while size >= minimum:
        lines = wrap_text(text, max_width, size)
        total_h = 0
        max_w = 0
        line_gap = max(4, size // 6)
        for i, line in enumerate(lines):
            lw, lh = measure_text(line, size)
            max_w = max(max_w, lw)
            total_h += lh + (line_gap if i else 0)
        if max_w <= max_width and total_h <= max_height and len(lines) <= 3:
            return size, lines
        size -= 2
    lines = wrap_text(text, max_width, minimum)
    return minimum, lines[:3]


def dedupe_labels(boxes: Iterable[TextBox]) -> list[TextBox]:
    """Remove duplicate identical text (keep first / highest alpha)."""
    seen: set[str] = set()
    out: list[TextBox] = []
    for box in sorted(boxes, key=lambda b: (-b.alpha, b.y, b.x)):
        key = " ".join((box.text or "").lower().split())
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(box)
    return out


def resolve_collisions(boxes: list[TextBox], bounds: tuple[int, int, int, int]) -> list[TextBox]:
    """Push colliding boxes downward within bounds; drop if they cannot fit."""
    x0, y0, x1, y1 = bounds
    placed: list[TextBox] = []
    for box in sorted(boxes, key=lambda b: (b.y, b.x)):
        candidate = TextBox(
            text=box.text,
            x=max(x0 + MIN_MARGIN_PX, min(box.x, x1 - box.w - MIN_MARGIN_PX)),
            y=box.y,
            w=box.w,
            h=box.h,
            font_size=box.font_size,
            color=box.color,
            kind=box.kind,
            row=box.row,
            alpha=box.alpha,
            meta=dict(box.meta),
        )
        attempts = 0
        while any(candidate.overlaps(p) for p in placed) and attempts < 12:
            candidate.y += candidate.h + MIN_LABEL_GAP_PX
            attempts += 1
        if candidate.y + candidate.h > y1 - MIN_MARGIN_PX:
            # Cannot fit — redesign by dropping rather than clipping
            continue
        placed.append(candidate)
    return placed


@dataclass
class BoardLayoutResult:
    boxes: list[TextBox]
    occupied_rows: dict[int, str]
    redesigns: list[str] = field(default_factory=list)


def layout_keyword_board(
    actions: list[Any],
    board_rect: tuple[int, int, int, int],
    p: float,
    *,
    max_rows: int = MAX_BOARD_ROWS,
    row_h: int = DEFAULT_ROW_HEIGHT,
) -> BoardLayoutResult:
    """Layout active keyword board actions with lifetime + collision rules.

    Visibility rules:
    - A write is visible only during its educational window (with fade).
    - Only one write per row at a time (later write on same row wins).
    - Emphasis (underline/circle) only while its text is the active row content.
    - Duplicate text is removed.
    """
    x0, y0, x1, y1 = board_rect
    inner = (
        x0 + 20,
        y0 + 20,
        x1 - 20,
        y1 - 16,
    )
    usable_w = inner[2] - inner[0]
    usable_h = inner[3] - inner[1]
    row_h = min(row_h, max(40, usable_h // max(max_rows, 1)))

    # Determine active write per row at time p (latest start that is still visible)
    writes = [a for a in actions if str(getattr(a, "kind", "")) in ("write", "equation")]
    emphasis = [a for a in actions if str(getattr(a, "kind", "")) in ("underline", "circle")]

    active_by_row: dict[int, Any] = {}
    for action in sorted(writes, key=lambda a: float(getattr(a, "start", 0))):
        row = int(getattr(action, "row", 0))
        if row < 0 or row >= max_rows:
            continue
        vis = visibility_envelope(p, float(action.start), float(action.end))
        if vis <= 0:
            continue
        # Later write on same row replaces earlier
        prev = active_by_row.get(row)
        if prev is None or float(action.start) >= float(prev.start):
            active_by_row[row] = action

    boxes: list[TextBox] = []
    redesigns: list[str] = []
    occupied: dict[int, str] = {}

    for row, action in sorted(active_by_row.items()):
        text = " ".join(str(getattr(action, "text", "") or "").split())
        if not text:
            continue
        # Clamp to short keywords
        words = text.split()
        if len(words) > 8:
            text = " ".join(words[:8])
            redesigns.append(f"truncated_keyword:{text}")
        preferred = int(getattr(action, "size", 0) or 48)
        slot_h = row_h - 8
        size, lines = fit_font_size(text, usable_w, slot_h, preferred=preferred)
        if len(lines) > 1:
            redesigns.append(f"wrapped_row_{row}")
        vis = visibility_envelope(p, float(action.start), float(action.end))
        # Stroke reveal during write window
        reveal = stroke_reveal(p, float(action.start), float(action.end))
        ease = reveal * reveal * (3.0 - 2.0 * reveal)
        display = text if ease >= 0.99 else text[: max(0, int(round(ease * len(text))))]
        if not display:
            continue
        # Re-measure visible substring
        line = display if len(lines) == 1 else lines[0][: len(display)]
        tw, th = measure_text(line, size)
        y = inner[1] + row * row_h
        color = tuple(getattr(action, "color", (20, 40, 90)) or (20, 40, 90))
        boxes.append(
            TextBox(
                text=line,
                x=inner[0],
                y=y,
                w=tw,
                h=th,
                font_size=size,
                color=color,  # type: ignore[arg-type]
                kind="write",
                row=row,
                alpha=vis,
                meta={"full_text": text, "action_start": float(action.start), "action_end": float(action.end)},
            )
        )
        occupied[row] = text

    # Emphasis only for currently occupied matching text
    for action in emphasis:
        text = " ".join(str(getattr(action, "text", "") or "").split())
        row = int(getattr(action, "row", 0))
        if occupied.get(row) != text:
            continue
        vis = visibility_envelope(p, float(action.start), float(action.end), fade_in=0.01, fade_out=0.03)
        if vis <= 0:
            continue
        # Find the write box on this row
        target = next((b for b in boxes if b.row == row), None)
        if target is None:
            continue
        boxes.append(
            TextBox(
                text=text,
                x=target.x,
                y=target.y,
                w=target.w,
                h=target.h,
                font_size=target.font_size,
                color=tuple(getattr(action, "color", (210, 45, 35)) or (210, 45, 35)),  # type: ignore[arg-type]
                kind=str(action.kind),
                row=row,
                alpha=vis,
                meta={"emphasis": True},
            )
        )

    boxes = dedupe_labels([b for b in boxes if b.kind == "write"]) + [
        b for b in boxes if b.kind != "write"
    ]
    # Write boxes already on separate rows — collision resolve for safety
    writes_only = [b for b in boxes if b.kind == "write"]
    emphasis_only = [b for b in boxes if b.kind != "write"]
    writes_only = resolve_collisions(writes_only, inner)
    return BoardLayoutResult(boxes=writes_only + emphasis_only, occupied_rows=occupied, redesigns=redesigns)


def paint_text_boxes(canvas: Image.Image, boxes: list[TextBox]) -> None:
    """Paint laid-out text boxes and emphasis marks onto the canvas."""
    d = ImageDraw.Draw(canvas)
    for box in boxes:
        if box.alpha <= 0.02:
            continue
        if box.kind in ("write", "equation", "label"):
            # Approximate alpha via color blend toward white board
            col = box.color
            if box.alpha < 0.99:
                col = tuple(int(c * box.alpha + 255 * (1 - box.alpha)) for c in col)  # type: ignore[assignment]
            d.text((box.x, box.y), box.text, fill=col, font=_font(box.font_size))
        elif box.kind == "underline":
            y = box.y + box.h + 6
            uw = int(box.w * box.alpha)
            d.line((box.x, y, box.x + uw, y), fill=box.color, width=5)
        elif box.kind == "circle":
            import math

            pad = 12
            cx = box.x + box.w // 2
            cy = box.y + box.h // 2
            rx = box.w // 2 + pad
            ry = box.h // 2 + pad
            steps = max(8, int(48 * box.alpha))
            pts = []
            for i in range(steps + 1):
                ang = -math.pi / 2 + 2 * math.pi * (i / 48)
                pts.append((cx + int(rx * math.cos(ang)), cy + int(ry * math.sin(ang))))
            if len(pts) >= 2:
                d.line(pts, fill=(210, 45, 35), width=4)


def keyword_bbox_lookup(
    layout: BoardLayoutResult,
    text: str,
    board_rect: tuple[int, int, int, int],
) -> tuple[int, int, int, int] | None:
    """Resolve a keyword target text to its pixel bbox, if currently visible."""
    needle = " ".join((text or "").lower().split())
    for box in layout.boxes:
        if box.kind not in ("write", "equation"):
            continue
        full = " ".join(str(box.meta.get("full_text") or box.text).lower().split())
        if full == needle or box.text.lower() == needle:
            return box.rect
    return None


@dataclass
class TrayClaim:
    mode: str  # panel | timeline | shell | none
    reason: str = ""


def claim_evidence_tray(
    p: float,
    *,
    panel_windows: list[tuple[float, float]] | None = None,
    timeline_window: tuple[float, float] | None = None,
    shell_window: tuple[float, float] | None = None,
) -> TrayClaim:
    """Exclusive tray compositor — one educational layer at a time.

    Priority: panel > shell > timeline. Never stack competing tray graphics.
    """
    panels = panel_windows or []
    for start, end in panels:
        if visibility_envelope(p, start, end, fade_in=0.015, fade_out=0.03) > 0.05:
            return TrayClaim("panel", "active_reality_panel")
    if shell_window:
        s, e = shell_window
        if visibility_envelope(p, s, e, fade_in=0.02, fade_out=0.04) > 0.05:
            return TrayClaim("shell", "shell_evolution_exclusive")
    if timeline_window:
        s, e = timeline_window
        if visibility_envelope(p, s, e, fade_in=0.02, fade_out=0.04) > 0.05:
            return TrayClaim("timeline", "timeline_exclusive")
    return TrayClaim("none")


def professor_fits_zone(
    char_w: int,
    char_h: int,
    zone: tuple[int, int, int, int],
    *,
    content_x_min: int,
) -> tuple[int, int, float]:
    """Return (x, max_height_scale_factor, recommended_scale_mul) so professor stays left of content."""
    zx0, zy0, zx1, zy1 = zone
    max_w = max(40, min(zx1 - zx0, content_x_min - zx0 - 8))
    max_h = max(40, zy1 - zy0)
    scale_w = max_w / max(char_w, 1)
    scale_h = max_h / max(char_h, 1)
    mul = min(1.0, scale_w, scale_h)
    x = zx0 + max(0, (max_w - int(char_w * mul)) // 8)
    return x, mul, mul
