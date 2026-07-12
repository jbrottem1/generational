"""Interactive classroom demos — Generational Method visual beats.

Beats align with ``teaching_choreography`` plans for each demo_id.
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFont


def _font(size: int = 32):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", size)
    except Exception:  # noqa: BLE001
        try:
            return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
        except Exception:  # noqa: BLE001
            return ImageFont.load_default()


def _label(d: ImageDraw.ImageDraw, text: str, xy, fill=(25, 35, 55)):
    d.text(xy, text, fill=fill, font=_font(30))


def draw_classroom_floor(canvas: Image.Image) -> int:
    """Draw grounded floor; return floor_y for character feet."""
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    floor_y = int(h * 0.78)
    d.rectangle((0, floor_y, w, h), fill=(210, 218, 226))
    d.line((0, floor_y, w, floor_y), fill=(160, 170, 180), width=3)
    d.rectangle((0, 0, w, floor_y), fill=(236, 241, 247))
    d.rounded_rectangle(
        (int(w * 0.42), int(h * 0.10), int(w * 0.95), int(h * 0.42)),
        radius=8,
        fill=(250, 252, 255),
        outline=(120, 140, 160),
        width=3,
    )
    return floor_y


def _draw_balls(d, bx, bowl_x, base_y, bb_r, bowl_r):
    d.ellipse((bx - bb_r, base_y - 2 * bb_r, bx + bb_r, base_y), fill=(230, 120, 50), outline=(40, 20, 10), width=4)
    d.arc((bx - bb_r, base_y - 2 * bb_r, bx + bb_r, base_y), 200, 340, fill=(40, 20, 10), width=3)
    d.ellipse(
        (bowl_x - bowl_r, base_y - 2 * bowl_r, bowl_x + bowl_r, base_y),
        fill=(35, 35, 45),
        outline=(0, 0, 0),
        width=4,
    )


def draw_bowling_momentum_lesson(canvas: Image.Image, t: float, duration: float) -> None:
    """Show mass/force/momentum — synced to BOWLING_BEATS."""
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    floor_y = draw_classroom_floor(canvas)
    p = t / max(duration, 0.1)

    bb_r, bowl_r = 48, 70
    base_y = floor_y - 8

    # 0–10%: hook — both balls present (already visible when "this ball" lands)
    if p < 0.10:
        bx, bowl_x = int(w * 0.58), int(w * 0.78)
        _label(d, "same size-ish…", (int(w * 0.50), int(h * 0.14)), fill=(40, 50, 70))
        _label(d, "basketball", (bx - 50, base_y - bb_r - 50), fill=(180, 90, 40))
        _label(d, "bowling ball", (bowl_x - 70, base_y - bowl_r - 50), fill=(40, 40, 50))
    # 10–22%: point / compare
    elif p < 0.22:
        bx, bowl_x = int(w * 0.58), int(w * 0.78)
        _label(d, "Watch. Same push.", (int(w * 0.48), int(h * 0.14)), fill=(30, 50, 90))
        _label(d, "basketball", (bx - 50, base_y - bb_r - 50), fill=(180, 90, 40))
        _label(d, "bowling ball", (bowl_x - 70, base_y - bowl_r - 50), fill=(40, 40, 50))
    # 22–40%: push light ball — event happens with the words
    elif p < 0.40:
        local = (p - 0.22) / 0.18
        bx = int(w * 0.55 + local * w * 0.30)
        bowl_x = int(w * 0.78)
        _label(d, "basketball races ahead", (int(w * 0.48), int(h * 0.14)), fill=(40, 100, 60))
        d.line((bx - 90, base_y - bb_r, bx - 20, base_y - bb_r), fill=(220, 60, 50), width=8)
        d.polygon(
            [(bx - 20, base_y - bb_r - 14), (bx + 5, base_y - bb_r), (bx - 20, base_y - bb_r + 14)],
            fill=(220, 60, 50),
        )
        _label(d, "FORCE", (bx - 100, base_y - bb_r - 55), fill=(180, 40, 40))
    # 40–45%: brief hold / step
    elif p < 0.45:
        bx, bowl_x = int(w * 0.88), int(w * 0.78)
        _label(d, "Now the heavy one…", (int(w * 0.48), int(h * 0.14)), fill=(80, 40, 40))
    # 45–62%: push heavy — barely moves
    elif p < 0.62:
        local = (p - 0.45) / 0.17
        bx = int(w * 0.88)
        bowl_x = int(w * 0.58 + local * w * 0.10)
        _label(d, "barely budges", (int(w * 0.48), int(h * 0.14)), fill=(100, 40, 40))
        d.line((bowl_x - 100, base_y - bowl_r, bowl_x - 25, base_y - bowl_r), fill=(220, 60, 50), width=8)
        d.polygon(
            [(bowl_x - 25, base_y - bowl_r - 14), (bowl_x, base_y - bowl_r), (bowl_x - 25, base_y - bowl_r + 14)],
            fill=(220, 60, 50),
        )
        _label(d, "more MASS → more INERTIA", (int(w * 0.45), int(h * 0.20)), fill=(30, 50, 90))
    # 62–78%: name concepts
    elif p < 0.78:
        bx, bowl_x = int(w * 0.60), int(w * 0.80)
        _label(d, "MASS", (int(w * 0.48), int(h * 0.14)), fill=(30, 60, 100))
        _label(d, "FORCE", (int(w * 0.62), int(h * 0.14)), fill=(160, 40, 40))
        _label(d, "MOMENTUM = mass × velocity", (int(w * 0.45), int(h * 0.22)), fill=(20, 40, 80))
    # 78–92%: real world
    elif p < 0.92:
        bx, bowl_x = int(w * 0.60), int(w * 0.80)
        _label(d, "full cart vs empty cart", (int(w * 0.48), int(h * 0.14)), fill=(40, 60, 90))
        _label(d, "same idea you can feel", (int(w * 0.48), int(h * 0.22)), fill=(50, 70, 100))
    # takeaway
    else:
        bx, bowl_x = int(w * 0.60), int(w * 0.80)
        _label(d, "Mass. Force. Momentum.", (int(w * 0.46), int(h * 0.16)), fill=(20, 40, 80))
        _label(d, "Feel the difference.", (int(w * 0.48), int(h * 0.24)), fill=(40, 60, 100))

    _draw_balls(d, bx, bowl_x, base_y, bb_r, bowl_r)


def draw_gravity_direction_lesson(canvas: Image.Image, t: float, duration: float) -> None:
    """Gravity toward center — synced to GRAVITY_BEATS."""
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    floor_y = draw_classroom_floor(canvas)
    p = t / max(duration, 0.1)

    gx, gy, gr = int(w * 0.70), int(h * 0.52), 150
    d.ellipse((gx - gr, gy - gr, gx + gr, gy + gr), fill=(70, 130, 200), outline=(20, 50, 90), width=5)
    d.ellipse((gx - 40, gy - 50, gx + 30, gy + 20), fill=(60, 140, 80))
    d.ellipse((gx + 20, gy + 10, gx + 80, gy + 70), fill=(55, 130, 75))
    d.ellipse((gx - 8, gy - 8, gx + 8, gy + 8), fill=(255, 220, 60))
    _label(d, "Earth's center", (gx - 60, gy + gr + 10), fill=(40, 60, 100))

    # Hook / think: apple ready at top
    if p < 0.11:
        ax, ay = gx, gy - gr - 40
        _label(d, "Sideways… into space?", (int(w * 0.42), int(h * 0.12)), fill=(80, 40, 40))
    # Apple falls while pointing
    elif p < 0.35:
        local = (p - 0.11) / 0.24
        ax = gx
        ay = int(gy - gr - 40 + local * (gr - 10))
        _label(d, "Watch the apple — inward", (int(w * 0.42), int(h * 0.12)), fill=(30, 50, 90))
    # React: arrows appear immediately
    else:
        ax, ay = gx, gy - gr + 20
        for ang in (270, 200, 340, 90):
            rad = math.radians(ang)
            sx = gx + int(math.cos(rad) * (gr - 5))
            sy = gy + int(math.sin(rad) * (gr - 5))
            ex = gx + int(math.cos(rad) * 35)
            ey = gy + int(math.sin(rad) * 35)
            d.line((sx, sy, ex, ey), fill=(220, 60, 50), width=5)
            d.ellipse((ex - 5, ey - 5, ex + 5, ey + 5), fill=(220, 60, 50))
        if p < 0.45:
            _label(d, "toward the CENTER — not sideways", (int(w * 0.42), int(h * 0.12)), fill=(140, 40, 40))
        elif p < 0.70:
            _label(d, "Everywhere: down = toward center", (int(w * 0.42), int(h * 0.12)), fill=(30, 50, 100))
        elif p < 0.88:
            _label(d, "GRAVITY", (int(w * 0.45), int(h * 0.14)), fill=(30, 50, 100))
            _label(d, "Direction = Earth's center of mass", (int(w * 0.42), int(h * 0.22)))
        else:
            _label(d, "Always toward the middle.", (int(w * 0.44), int(h * 0.16)), fill=(20, 40, 80))

    d.ellipse((ax - 22, ay - 22, ax + 22, ay + 22), fill=(200, 50, 50), outline=(80, 20, 20), width=3)
    d.line((ax, ay - 22, ax + 4, ay - 34), fill=(40, 100, 40), width=3)

    if p > 0.70:
        mx, my = int(w * 0.48), int(h * 0.55)
        d.line((mx, my, mx + 60, my), fill=(180, 40, 40), width=6)
        d.line((mx + 50, my - 15, mx + 70, my + 15), fill=(180, 40, 40), width=5)
        d.line((mx + 50, my + 15, mx + 70, my - 15), fill=(180, 40, 40), width=5)
        _label(d, "not this way", (mx - 10, my + 20), fill=(160, 40, 40))


EDUCATOR_DEMOS = {
    "bowling_momentum": draw_bowling_momentum_lesson,
    "gravity_direction": draw_gravity_direction_lesson,
}


def get_educator_demo(demo_id: str):
    demo = EDUCATOR_DEMOS.get(demo_id)
    if demo is not None:
        return demo
    from services.animation.foundation_studio import get_foundation_demo
    from services.animation.batesian_demos import get_batesian_demo
    from services.animation.biology_demos import get_biology_demo
    from services.animation.macrocenter import get_macrocenter_demo
    from services.animation.skydive_demos import get_skydive_demo

    # Foundation white-studio demos take priority over MacroCenter / labs
    return (
        get_foundation_demo(demo_id)
        or get_batesian_demo(demo_id)
        or get_skydive_demo(demo_id)
        or get_macrocenter_demo(demo_id)
        or get_biology_demo(demo_id)
    )
