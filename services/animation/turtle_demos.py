"""Foundation V2 benchmark — The Origin of Turtles."""

from __future__ import annotations

from PIL import Image

from services.animation.foundation_v2 import (
    PointerAction,
    draw_foundation_v2_studio,
    draw_shell_evolution_sketch,
    draw_timeline_bar,
    render_keyword_board,
    render_pointer_actions,
)
from services.animation.whiteboard import BoardAction
from services.reality.panel import draw_panels
from services.reality.planner import TURTLE_202_PANELS


# Keyword-only board — never full narration
TURTLE_202_KEYWORDS: list[BoardAction] = [
    BoardAction("write", "Origin of Turtles", start=0.06, end=0.14, row=0, size=56, color=(20, 40, 90)),
    BoardAction("write", "200+ million years", start=0.20, end=0.30, row=1, size=48, color=(20, 40, 90)),
    BoardAction("write", "Early reptiles", start=0.30, end=0.38, row=2, size=44, color=(40, 90, 60)),
    BoardAction("write", "Gradual shell", start=0.42, end=0.52, row=0, size=52, color=(20, 40, 90)),
    BoardAction("underline", "Gradual shell", start=0.52, end=0.58, row=0, size=52, color=(210, 45, 35)),
    BoardAction("write", "Fossil intermediates", start=0.58, end=0.68, row=1, size=44, color=(80, 50, 30)),
    BoardAction("write", "Step by step", start=0.82, end=0.92, row=0, size=58, color=(20, 40, 80)),
    BoardAction("circle", "Step by step", start=0.88, end=0.96, row=0, size=58),
]

TURTLE_202_POINTERS: list[PointerAction] = [
    PointerAction("point", start=0.14, end=0.22, x0=0.52, y0=0.52, x1=0.62, y1=0.58),
    PointerAction("tap", start=0.22, end=0.30, x0=0.50, y0=0.48, x1=0.58, y1=0.52),
    PointerAction("underline", start=0.30, end=0.38, x0=0.48, y0=0.50, x1=0.72, y1=0.54),
    PointerAction("trace", start=0.42, end=0.52, x0=0.46, y0=0.58, x1=0.78, y1=0.68),
    PointerAction("circle", start=0.58, end=0.68, x0=0.50, y0=0.55, x1=0.70, y1=0.72),
    PointerAction("point", start=0.72, end=0.82, x0=0.48, y0=0.50, x1=0.60, y1=0.62),
    PointerAction("tap", start=0.82, end=0.92, x0=0.52, y0=0.28, x1=0.68, y1=0.36),
]


def draw_turtle_202(canvas: Image.Image, t: float, duration: float) -> None:
    draw_foundation_v2_studio(canvas)
    p = t / max(duration, 0.1)
    render_keyword_board(canvas, TURTLE_202_KEYWORDS, p)
    draw_panels(canvas, TURTLE_202_PANELS, p, layout_rect_fn=_v2_content_rect)
    draw_timeline_bar(canvas, p)
    draw_shell_evolution_sketch(canvas, p)
    render_pointer_actions(canvas, TURTLE_202_POINTERS, p)


def _v2_content_rect(w: int, h: int) -> tuple[int, int, int, int]:
    from services.animation.foundation_v2 import evidence_tray_v2

    return evidence_tray_v2(w, h)


TURTLE_DEMOS = {
    "foundation_v2_turtle_202": draw_turtle_202,
}


def get_turtle_demo(demo_id: str):
    return TURTLE_DEMOS.get(demo_id)
