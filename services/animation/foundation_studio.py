"""PROJECT FOUNDATION — minimalist white teaching studio.

Pure white background. Whiteboard primary. No labs, MacroCenter, or scenery.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from services.animation.teaching_choreography import PLANS
from services.animation.whiteboard import (
    BoardAction,
    align_equation_to_write_beat,
    render_board_actions,
    write_window_from_plan,
)


STUDIO_WHITE = (255, 255, 255)


def draw_white_studio(canvas: Image.Image) -> int:
    """Fill pure white; subtle floor line only. Return floor_y for feet."""
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    d.rectangle((0, 0, w, h), fill=STUDIO_WHITE)
    floor_y = int(h * 0.82)
    # Hairline ground — orientation only, not scenery
    d.line((0, floor_y, w, floor_y), fill=(210, 212, 216), width=2)
    return floor_y


# --- Lesson 1: What Does F = ma Actually Mean? ---
# Timing locked to teaching_choreography foundation_f_equals_ma write beat (0.22–0.42)
_F_EQUALS_MA_BASE: list[BoardAction] = [
    BoardAction("write", "Today's question", start=0.02, end=0.08, row=0, size=28, color=(90, 95, 110)),
    BoardAction("write", "What does F = ma mean?", start=0.08, end=0.18, row=1, size=40),
    BoardAction("equation", "F = m × a", start=0.22, end=0.36, row=2, size=56, color=(20, 40, 90)),
    BoardAction("underline", "F = m × a", start=0.36, end=0.42, row=2, size=56, color=(200, 50, 40)),
    # explain_terms 0.42–0.58
    BoardAction("write", "Force  =  Mass  ×  Acceleration", start=0.42, end=0.56, row=3, size=30),
    # cart_example 0.58–0.72
    BoardAction("write", "Same push → light cart speeds up more", start=0.58, end=0.70, row=4, size=28, color=(40, 90, 60)),
    # circle_key 0.72–0.82
    BoardAction("circle", "F = m × a", start=0.72, end=0.82, row=2, size=56),
    # summary 0.82–0.94
    BoardAction("write", "Force causes acceleration.", start=0.84, end=0.93, row=5, size=32, color=(20, 40, 80)),
]


def _synced_f_equals_ma_actions() -> list[BoardAction]:
    plan = PLANS.get("foundation_f_equals_ma") or []
    win = write_window_from_plan(plan, label="write_equation")
    return align_equation_to_write_beat(_F_EQUALS_MA_BASE, win["start"], win["end"])


F_EQUALS_MA_ACTIONS: list[BoardAction] = _synced_f_equals_ma_actions()


def draw_f_equals_ma_lesson(canvas: Image.Image, t: float, duration: float) -> None:
    draw_white_studio(canvas)
    p = t / max(duration, 0.1)
    render_board_actions(canvas, F_EQUALS_MA_ACTIONS, p)


# --- Lesson 2: Why Does a Heavy Object Need More Force? ---
# write_a_equals 0.22–0.40; return_to_fma 0.70–0.84
FORCE_AND_MASS_ACTIONS: list[BoardAction] = [
    BoardAction("write", "Today's question", start=0.02, end=0.08, row=0, size=28, color=(90, 95, 110)),
    BoardAction("write", "Why more mass → more force?", start=0.08, end=0.18, row=1, size=36),
    BoardAction("equation", "a = F / m", start=0.22, end=0.38, row=2, size=56, color=(20, 40, 90)),
    BoardAction("write", "Bigger m → smaller a  (same F)", start=0.38, end=0.48, row=3, size=30),
    BoardAction("write", "Inertia: mass resists change", start=0.48, end=0.58, row=4, size=30, color=(80, 40, 40)),
    BoardAction("underline", "Inertia: mass resists change", start=0.58, end=0.66, row=4, size=30, color=(200, 50, 40)),
    BoardAction("write", "To get the same a: raise F", start=0.66, end=0.78, row=5, size=30, color=(40, 90, 60)),
    BoardAction("equation", "F = m × a", start=0.78, end=0.90, row=6, size=44, color=(20, 40, 90)),
]


def draw_force_and_mass_lesson(canvas: Image.Image, t: float, duration: float) -> None:
    from services.animation.whiteboard import _font, board_rect

    draw_white_studio(canvas)
    p = t / max(duration, 0.1)
    render_board_actions(canvas, FORCE_AND_MASS_ACTIONS, p)
    # Simple cart comparison in lower board area during mid lesson
    if 0.48 < p < 0.82:
        d = ImageDraw.Draw(canvas)
        x0, _y0, _x1, y1 = board_rect(*canvas.size)
        base = y1 - 55
        font = _font(20)
        # empty cart
        ex = x0 + 60
        d.rounded_rectangle((ex, base - 28, ex + 50, base), radius=4, outline=(30, 35, 45), width=2)
        d.ellipse((ex + 6, base - 4, ex + 18, base + 10), outline=(30, 35, 45), width=2)
        d.ellipse((ex + 32, base - 4, ex + 44, base + 10), outline=(30, 35, 45), width=2)
        d.text((ex, base + 14), "light", fill=(40, 90, 60), font=font)
        # loaded cart
        lx = x0 + 160
        d.rounded_rectangle((lx, base - 36, lx + 70, base), radius=4, outline=(30, 35, 45), width=2)
        d.rectangle((lx + 10, base - 52, lx + 35, base - 36), outline=(30, 35, 45), width=2)
        d.rectangle((lx + 38, base - 58, lx + 62, base - 36), outline=(30, 35, 45), width=2)
        d.ellipse((lx + 10, base - 4, lx + 24, base + 10), outline=(30, 35, 45), width=2)
        d.ellipse((lx + 46, base - 4, lx + 60, base + 10), outline=(30, 35, 45), width=2)
        d.text((lx + 8, base + 14), "heavy", fill=(120, 40, 40), font=font)


# --- Lesson 3: How Newton's Second Law Explains Everyday Life ---
# write_fma 0.20–0.32
NEWTON_EVERYDAY_ACTIONS: list[BoardAction] = [
    BoardAction("write", "Today's question", start=0.02, end=0.08, row=0, size=28, color=(90, 95, 110)),
    BoardAction("write", "Where is F = ma in real life?", start=0.08, end=0.18, row=1, size=34),
    BoardAction("equation", "F = m × a", start=0.20, end=0.32, row=2, size=52, color=(20, 40, 90)),
    BoardAction("write", "Car: more force → faster speedup", start=0.34, end=0.46, row=3, size=28),
    BoardAction("write", "Sports: push harder → more a", start=0.48, end=0.58, row=4, size=28),
    BoardAction("write", "Furniture: heavy → needs more F", start=0.60, end=0.70, row=5, size=28),
    BoardAction("write", "Bike: pedal force → accelerate", start=0.72, end=0.82, row=6, size=28),
    BoardAction("circle", "F = m × a", start=0.84, end=0.92, row=2, size=52),
    BoardAction("write", "Everyday motion is F = ma.", start=0.92, end=0.98, row=7, size=30, color=(20, 40, 80)),
]


def draw_newton_everyday_lesson(canvas: Image.Image, t: float, duration: float) -> None:
    draw_white_studio(canvas)
    p = t / max(duration, 0.1)
    render_board_actions(canvas, NEWTON_EVERYDAY_ACTIONS, p)


# --- Psychology: Confirmation Bias ---
CONFIRMATION_BIAS_ACTIONS: list[BoardAction] = [
    BoardAction("write", "Today's question", start=0.02, end=0.08, row=0, size=28, color=(90, 95, 110)),
    BoardAction("write", "Why do we favor agreeing evidence?", start=0.08, end=0.18, row=1, size=32),
    BoardAction("equation", "Confirmation Bias", start=0.22, end=0.38, row=2, size=48, color=(20, 40, 90)),
    BoardAction("underline", "Confirmation Bias", start=0.38, end=0.44, row=2, size=48, color=(200, 50, 40)),
    BoardAction("write", "We notice what fits our belief", start=0.44, end=0.56, row=3, size=30),
    BoardAction("write", "We skip what challenges it", start=0.56, end=0.68, row=4, size=30, color=(120, 40, 40)),
    BoardAction("write", "News · sports · arguments", start=0.68, end=0.80, row=5, size=28, color=(40, 90, 60)),
    BoardAction("circle", "Confirmation Bias", start=0.80, end=0.88, row=2, size=48),
    BoardAction("write", "Ask: What would prove me wrong?", start=0.88, end=0.96, row=6, size=28, color=(20, 40, 80)),
]


def draw_confirmation_bias_lesson(canvas: Image.Image, t: float, duration: float) -> None:
    draw_white_studio(canvas)
    p = t / max(duration, 0.1)
    render_board_actions(canvas, CONFIRMATION_BIAS_ACTIONS, p)


FOUNDATION_DEMOS = {
    "foundation_f_equals_ma": draw_f_equals_ma_lesson,
    "foundation_force_mass": draw_force_and_mass_lesson,
    "foundation_newton_everyday": draw_newton_everyday_lesson,
    "foundation_confirmation_bias": draw_confirmation_bias_lesson,
}


def get_foundation_demo(demo_id: str):
    return FOUNDATION_DEMOS.get(demo_id)
