"""Biology Foundation demos — Batesian mimicry benchmark series.

White studio + whiteboard + PROJECT REALITY evidence panels.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from services.animation.foundation_studio import draw_white_studio
from services.animation.whiteboard import BoardAction, board_rect, render_board_actions
from services.reality.panel import draw_panels
from services.reality.planner import (
    BATESIAN_101_PANELS,
    BLUFFING_103_PANELS,
    CORAL_102_PANELS,
)


def _font(size: int = 28):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ):
        try:
            return ImageFont.truetype(path, size)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


# --- Video 1: Batesian Mimicry definition ---
BATESIAN_101_ACTIONS: list[BoardAction] = [
    BoardAction("write", "What if pretending saves your life?", start=0.00, end=0.08, row=0, size=30, color=(20, 40, 90)),
    BoardAction("equation", "Batesian Mimicry", start=0.18, end=0.32, row=1, size=46, color=(20, 40, 90)),
    BoardAction("underline", "Batesian Mimicry", start=0.32, end=0.38, row=1, size=46, color=(200, 50, 40)),
    BoardAction("write", "Harmless mimic  ← looks like →  Harmful model", start=0.40, end=0.55, row=2, size=26),
    BoardAction("write", "Predators learn: bright = avoid", start=0.55, end=0.68, row=3, size=28, color=(40, 90, 60)),
    BoardAction("write", "Real hoverfly · Real kingsnake mimic", start=0.68, end=0.80, row=4, size=26),
    BoardAction("circle", "Batesian Mimicry", start=0.80, end=0.88, row=1, size=46),
    BoardAction("write", "Safety by resemblance.", start=0.88, end=0.96, row=5, size=30, color=(20, 40, 80)),
]


def draw_batesian_101(canvas: Image.Image, t: float, duration: float) -> None:
    draw_white_studio(canvas)
    p = t / max(duration, 0.1)
    render_board_actions(canvas, BATESIAN_101_ACTIONS, p)
    draw_panels(canvas, BATESIAN_101_PANELS, p)
    # Stripe highlight during compare beat
    if 0.42 < p < 0.72:
        d = ImageDraw.Draw(canvas)
        w, h = canvas.size
        x0, _y0, x1, y1 = board_rect(w, h)
        tray_y0 = y1 + 24
        mid = x0 + (x1 - x0) // 2
        # Highlight mimic stripes region (right panel)
        d.rounded_rectangle(
            (mid + 20, tray_y0 + 80, x1 - 40, tray_y0 + 140),
            radius=6,
            outline=(220, 50, 40),
            width=3,
        )
        d.text((mid + 24, tray_y0 + 52), "Notice the stripes…", fill=(220, 50, 40), font=_font(18))


# --- Video 2: Coral vs kingsnake ---
CORAL_102_ACTIONS: list[BoardAction] = [
    BoardAction("write", "Which snake is dangerous?", start=0.00, end=0.08, row=0, size=32, color=(20, 40, 90)),
    BoardAction("write", "Coral snake  vs  Scarlet kingsnake", start=0.18, end=0.32, row=1, size=28),
    BoardAction("write", "Warning colors teach predators", start=0.40, end=0.52, row=2, size=28, color=(40, 90, 60)),
    BoardAction("write", "Color rhymes have REGIONAL limits", start=0.55, end=0.68, row=3, size=26, color=(180, 40, 40)),
    BoardAction("underline", "Color rhymes have REGIONAL limits", start=0.68, end=0.74, row=3, size=26, color=(200, 50, 40)),
    BoardAction("write", "Never handle an unknown snake.", start=0.78, end=0.90, row=4, size=30, color=(140, 30, 30)),
    BoardAction("write", "When unsure: leave it alone.", start=0.90, end=0.98, row=5, size=28, color=(20, 40, 80)),
]


def draw_coral_102(canvas: Image.Image, t: float, duration: float) -> None:
    draw_white_studio(canvas)
    p = t / max(duration, 0.1)
    render_board_actions(canvas, CORAL_102_ACTIONS, p)
    draw_panels(canvas, CORAL_102_PANELS, p)
    if p > 0.50:
        d = ImageDraw.Draw(canvas)
        x0, y0, _x1, _y1 = board_rect(*canvas.size)
        d.text((x0 + 36, y0 + 340), "Rhyme ≠ reliable ID tool", fill=(160, 40, 40), font=_font(22))


# --- Video 3: Masters of bluffing + arms race ---
BLUFFING_103_ACTIONS: list[BoardAction] = [
    BoardAction("write", "Survival by deception?", start=0.00, end=0.08, row=0, size=32, color=(20, 40, 90)),
    BoardAction("write", "Hoverflies · bee mimics · false warnings", start=0.16, end=0.28, row=1, size=26),
    BoardAction("write", "Monarch–viceroy: story evolved", start=0.32, end=0.48, row=2, size=26, color=(80, 50, 20)),
    BoardAction("write", "Modern view: more complex than Batesian alone", start=0.48, end=0.62, row=3, size=24, color=(120, 40, 40)),
    BoardAction("equation", "Arms race", start=0.64, end=0.76, row=4, size=40, color=(20, 40, 90)),
    BoardAction("write", "Predators learn · prey refine the bluff", start=0.76, end=0.88, row=5, size=26),
    BoardAction("write", "Sometimes the best deceiver survives.", start=0.88, end=0.98, row=6, size=28, color=(20, 40, 80)),
]


def draw_bluffing_103(canvas: Image.Image, t: float, duration: float) -> None:
    draw_white_studio(canvas)
    p = t / max(duration, 0.1)
    render_board_actions(canvas, BLUFFING_103_ACTIONS, p)
    draw_panels(canvas, BLUFFING_103_PANELS, p)
    if 0.64 < p < 0.90:
        d = ImageDraw.Draw(canvas)
        x0, y0, _x1, _y1 = board_rect(*canvas.size)
        d.text((x0 + 40, y0 + 300), "Predator learning  ⇄  Prey deception", fill=(20, 40, 90), font=_font(24))


BATESIAN_DEMOS = {
    "foundation_batesian_101": draw_batesian_101,
    "foundation_coral_102": draw_coral_102,
    "foundation_bluffing_103": draw_bluffing_103,
}


def get_batesian_demo(demo_id: str):
    return BATESIAN_DEMOS.get(demo_id)
