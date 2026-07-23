"""Foundation Visual System V2 — baby-blue studio, keyword board, teaching pointer.

Calming backdrop. Professor left. Teaching visuals right. Minimal on-screen text.
Layout + annotation engines enforce: no overlapping text, exclusive tray layers,
semantic pointers tied to narration targets, fade in/out visibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from PIL import Image, ImageDraw

from services.animation.annotation_engine import annotations_from_pointer_actions, draw_semantic_annotations
from services.animation.layout_engine import (
    BoardLayoutResult,
    claim_evidence_tray,
    layout_keyword_board,
    paint_text_boxes,
    visibility_envelope,
)
from services.animation.whiteboard import BoardAction, _font


# Soft baby-blue studio — high contrast for dark text, calm for learning
STUDIO_BLUE_TOP = (228, 240, 252)
STUDIO_BLUE_BOTTOM = (205, 228, 248)
STUDIO_FLOOR = (190, 210, 228)
STUDIO_FLOOR_LINE = (165, 185, 205)

# Canonical V2 layout (1080×1920 vertical Short)
PROFESSOR_X_MAX = 0.30
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
    """Teaching pointer overlay — must resolve to a semantic target when possible."""

    kind: str  # point | tap | underline | circle | trace
    start: float = 0.0
    end: float = 1.0
    x0: float = 0.55
    y0: float = 0.30
    x1: float = 0.75
    y1: float = 0.45
    color: tuple[int, int, int] = (210, 45, 35)
    target: str = ""
    narration_cue: str = ""
    extras: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.target and "target" not in self.extras:
            self.extras["target"] = self.target
        if self.narration_cue and "narration_cue" not in self.extras:
            self.extras["narration_cue"] = self.narration_cue


def render_pointer_actions(
    canvas: Image.Image,
    actions: list[PointerAction],
    p: float,
    *,
    board_layout: BoardLayoutResult | None = None,
    board_rect: tuple[int, int, int, int] | None = None,
    panel_slots: dict[str, tuple[int, int, int, int]] | None = None,
    shell_stages: list[tuple[int, int, int, int]] | None = None,
    allow_fallback_coords: bool = False,
) -> list[dict[str, Any]]:
    """Draw semantic pointers; free coords only when allow_fallback_coords=True."""
    anns = annotations_from_pointer_actions(actions)
    for i, action in enumerate(actions):
        if action.target and not anns[i].target:
            anns[i].target = action.target
        if action.narration_cue and not anns[i].narration_cue:
            anns[i].narration_cue = action.narration_cue
    return draw_semantic_annotations(
        canvas,
        anns,
        p,
        board_layout=board_layout,
        board_rect=board_rect,
        panel_slots=panel_slots,
        shell_stages=shell_stages,
        allow_fallback_coords=allow_fallback_coords,
    )


def render_keyword_board(
    canvas: Image.Image,
    actions: list[BoardAction],
    p: float,
) -> BoardLayoutResult:
    """Render keyword-only whiteboard via the layout engine (no overlapping text)."""
    rect = draw_whiteboard_frame_v2(canvas)
    layout = layout_keyword_board(actions, rect, p)
    paint_text_boxes(canvas, layout.boxes)
    return layout


def shell_stage_rects(canvas: Image.Image) -> list[tuple[int, int, int, int]]:
    rect = evidence_tray_v2(*canvas.size)
    x0, y0, x1, y1 = rect
    step_w = (x1 - x0) // 4
    stages = []
    for i in range(3):
        cx = x0 + step_w * (i + 1)
        cy = y0 + (y1 - y0) // 2 + 20
        stages.append((cx - 55, y0 + 8, cx + 55, cy + 40))
    return stages


def draw_shell_evolution_sketch(
    canvas: Image.Image,
    p: float,
    *,
    window: tuple[float, float] = (0.36, 0.50),
) -> None:
    """Gradual shell formation diagram — exclusive tray window."""
    start, end = window
    alpha = visibility_envelope(p, start, end, fade_in=0.02, fade_out=0.04)
    if alpha <= 0.05:
        return
    d = ImageDraw.Draw(canvas)
    rect = evidence_tray_v2(*canvas.size)
    x0, y0, x1, y1 = rect
    stages = [
        ("No shell", (180, 100, 80)),
        ("Ribs widen", (120, 130, 90)),
        ("Full shell", (60, 110, 70)),
    ]
    step_w = (x1 - x0) // 4
    local = (p - start) / max(end - start, 1e-6)
    for i, (label, col) in enumerate(stages):
        reveal = max(0.0, min(1.0, local * 3 - i)) * alpha
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
    ax0, ax1 = x0 + 40, x1 - 40
    ay = y1 - 30
    d.line(
        (ax0, ay, ax0 + int((ax1 - ax0) * min(1.0, local) * alpha), ay),
        fill=(20, 40, 90),
        width=3,
    )
    d.text((x0 + 20, y1 - 55), "Millions of years →", fill=(20, 40, 90), font=_font(22))


def draw_timeline_bar(
    canvas: Image.Image,
    p: float,
    *,
    window: tuple[float, float] = (0.26, 0.36),
) -> None:
    """Evolutionary timeline — exclusive tray window (never over photos)."""
    start, end = window
    alpha = visibility_envelope(p, start, end, fade_in=0.02, fade_out=0.04)
    if alpha <= 0.05:
        return
    d = ImageDraw.Draw(canvas)
    rect = evidence_tray_v2(*canvas.size)
    x0, y0, x1, _y1 = rect
    bar_y = y0 + 48
    local = (p - start) / max(end - start, 1e-6)
    bw = int((x1 - x0 - 40) * min(1.0, local))
    d.rounded_rectangle((x0 + 20, bar_y, x0 + 20 + bw, bar_y + 14), radius=6, fill=(20, 40, 90))
    d.text((x0 + 20, bar_y - 28), "250 Ma", fill=(20, 40, 90), font=_font(22))
    d.text((x1 - 90, bar_y - 28), "Today", fill=(20, 40, 90), font=_font(22))
    if local > 0.35:
        d.text((x0 + 40, bar_y + 28), "Early reptiles → turtles", fill=(40, 90, 60), font=_font(24))


def compose_v2_teaching_frame(
    canvas: Image.Image,
    p: float,
    *,
    keywords: list[BoardAction],
    pointers: list[PointerAction],
    panels: list[Any] | None = None,
    panel_drawer: Any = None,
    timeline_window: tuple[float, float] = (0.26, 0.36),
    shell_window: tuple[float, float] = (0.36, 0.50),
) -> dict[str, Any]:
    """Full V2 teaching compositor: board + exclusive tray + semantic pointers."""
    draw_foundation_v2_studio(canvas)
    board_rect = board_rect_v2(*canvas.size)
    layout = render_keyword_board(canvas, keywords, p)

    panel_windows = [(float(pn.start), float(pn.end)) for pn in (panels or [])]
    claim = claim_evidence_tray(
        p,
        panel_windows=panel_windows,
        timeline_window=timeline_window,
        shell_window=shell_window,
    )

    panel_slots: dict[str, tuple[int, int, int, int]] = {}
    if claim.mode == "panel" and panels is not None and panel_drawer is not None:
        panel_drawer(canvas, panels, p)
        tray = evidence_tray_v2(*canvas.size)
        for i, pn in enumerate(panels):
            if visibility_envelope(p, float(pn.start), float(pn.end)) > 0.05:
                panel_slots[str(i)] = tray
                if getattr(pn, "title", None):
                    key = str(pn.title).lower().replace(" ", "_")
                    panel_slots[key] = tray
                for img_id in getattr(pn, "image_ids", []) or []:
                    panel_slots[str(img_id)] = tray
                joined = " ".join(getattr(pn, "image_ids", []) or [])
                if "turtle" in joined:
                    panel_slots["living"] = tray
                if "fossil" in joined:
                    panel_slots["fossil"] = tray
    elif claim.mode == "timeline":
        draw_timeline_bar(canvas, p, window=timeline_window)
    elif claim.mode == "shell":
        draw_shell_evolution_sketch(canvas, p, window=shell_window)

    shell_stages = shell_stage_rects(canvas) if claim.mode == "shell" else []
    ann_records = render_pointer_actions(
        canvas,
        pointers,
        p,
        board_layout=layout,
        board_rect=board_rect,
        panel_slots=panel_slots,
        shell_stages=shell_stages,
        allow_fallback_coords=False,
    )
    return {
        "tray_mode": claim.mode,
        "board_layout": layout,
        "annotations": ann_records,
        "panel_slots": list(panel_slots.keys()),
    }


# V2 professor defaults — sized to stay inside professor zone
V2_CHARACTER_SCALE = 0.42
V2_STICK_SPEC = {
    "character_id": "CHAR-PROFESSOR-V2-001",
    "name": "Professor Gen",
    "attire": "lab_coat",
    "head_ratio": 0.38,
}
