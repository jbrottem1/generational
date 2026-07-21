"""Foundation V2 benchmark — The Origin of Turtles.

Uses the educational visual compositor:
- layout engine for non-overlapping keywords
- exclusive evidence tray
- semantic pointers tied to narration targets
"""

from __future__ import annotations

from PIL import Image

from services.animation.foundation_v2 import PointerAction, compose_v2_teaching_frame
from services.animation.whiteboard import BoardAction
from services.reality.panel import draw_panels
from services.reality.planner import TURTLE_202_PANELS


# Keyword-only board — never full narration
TURTLE_202_KEYWORDS: list[BoardAction] = [
    BoardAction("write", "Origin of Turtles", start=0.06, end=0.18, row=0, size=56, color=(20, 40, 90)),
    BoardAction("write", "200+ million years", start=0.20, end=0.30, row=1, size=48, color=(20, 40, 90)),
    BoardAction("write", "Early reptiles", start=0.30, end=0.38, row=2, size=44, color=(40, 90, 60)),
    BoardAction("write", "Gradual shell", start=0.40, end=0.54, row=0, size=52, color=(20, 40, 90)),
    BoardAction("underline", "Gradual shell", start=0.46, end=0.54, row=0, size=52, color=(210, 45, 35)),
    BoardAction("write", "Fossil intermediates", start=0.56, end=0.72, row=1, size=44, color=(80, 50, 30)),
    BoardAction("write", "Step by step", start=0.80, end=0.94, row=0, size=58, color=(20, 40, 80)),
    BoardAction("circle", "Step by step", start=0.86, end=0.94, row=0, size=58),
]

# Every pointer answers: what exactly am I looking at?
TURTLE_202_POINTERS: list[PointerAction] = [
    PointerAction(
        "point",
        start=0.12,
        end=0.20,
        target="panel:living",
        narration_cue="modern sea turtle",
    ),
    PointerAction(
        "tap",
        start=0.22,
        end=0.28,
        target="keyword:200+ million years",
        narration_cue="deep time span",
    ),
    PointerAction(
        "underline",
        start=0.30,
        end=0.36,
        target="keyword:Early reptiles",
        narration_cue="early reptiles",
    ),
    PointerAction(
        "trace",
        start=0.40,
        end=0.48,
        target="shell:1",
        narration_cue="shell begins to develop",
    ),
    PointerAction(
        "circle",
        start=0.50,
        end=0.54,
        target="shell:2",
        narration_cue="full shell stage",
    ),
    PointerAction(
        "point",
        start=0.58,
        end=0.68,
        target="panel:fossil",
        narration_cue="fossil intermediates",
    ),
    PointerAction(
        "circle",
        start=0.84,
        end=0.92,
        target="keyword:Step by step",
        narration_cue="step by step takeaway",
    ),
]

TURTLE_TIMELINE_WINDOW = (0.26, 0.36)
TURTLE_SHELL_WINDOW = (0.36, 0.50)


def _panel_drawer(canvas: Image.Image, panels, p: float) -> None:
    from services.animation.foundation_v2 import evidence_tray_v2

    draw_panels(canvas, panels, p, layout_rect_fn=evidence_tray_v2)


def draw_turtle_202(canvas: Image.Image, t: float, duration: float) -> None:
    p = t / max(duration, 0.1)
    compose_v2_teaching_frame(
        canvas,
        p,
        keywords=TURTLE_202_KEYWORDS,
        pointers=TURTLE_202_POINTERS,
        panels=TURTLE_202_PANELS,
        panel_drawer=_panel_drawer,
        timeline_window=TURTLE_TIMELINE_WINDOW,
        shell_window=TURTLE_SHELL_WINDOW,
    )


TURTLE_DEMOS = {
    "foundation_v2_turtle_202": draw_turtle_202,
}


def get_turtle_demo(demo_id: str):
    return TURTLE_DEMOS.get(demo_id)
