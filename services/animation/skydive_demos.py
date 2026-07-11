"""Skydive classroom — freefall educational storytelling format."""

from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFont

SKY = {
    "sky_top": (70, 150, 220),
    "sky_mid": (120, 180, 230),
    "sky_low": (180, 210, 235),
    "cloud": (245, 250, 255),
    "cabin": (45, 50, 60),
    "door": (30, 34, 42),
    "ground": (90, 140, 70),
    "dust": (160, 140, 100),
    "ink": (20, 30, 45),
    "ink_light": (245, 248, 252),
    "teal": (40, 180, 170),
    "acid": (255, 200, 60),
    "mucus": (100, 220, 190),
    "wall": (210, 110, 120),
    "food": (170, 100, 60),
    "coral": (240, 90, 80),
}


def _font(size: int = 28):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", size)
    except Exception:  # noqa: BLE001
        try:
            return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
        except Exception:  # noqa: BLE001
            return ImageFont.load_default()


def _label(d, text, xy, fill=None, size=28):
    d.text(xy, text, fill=fill or SKY["ink_light"], font=_font(size))


def _draw_clouds(d, w, h, t, speed=1.0):
    for i in range(8):
        cx = int((i * 180 + t * 90 * speed) % (w + 200) - 100)
        cy = int(80 + (i * 97) % int(h * 0.55))
        r = 40 + (i % 4) * 18
        d.ellipse((cx - r, cy - r // 2, cx + r, cy + r // 2), fill=SKY["cloud"])
        d.ellipse((cx - r // 2, cy - r, cx + r // 2 + 20, cy), fill=SKY["cloud"])


def _stomach(d, cx, cy, scale=1.0, mucus_on=False):
    rw, rh = int(95 * scale), int(72 * scale)
    d.ellipse((cx - rw, cy - rh, cx + rw, cy + rh), fill=(95, 48, 58), outline=SKY["wall"], width=5)
    if mucus_on:
        d.ellipse((cx - rw + 16, cy - rh + 14, cx + rw - 16, cy + rh - 14), outline=SKY["mucus"], width=7)
        for i in range(6):
            ang = i / 6 * 2 * math.pi
            px = cx + int(math.cos(ang) * (rw - 26))
            py = cy + int(math.sin(ang) * (rh - 20))
            d.ellipse((px - 5, py - 5, px + 5, py + 5), fill=SKY["mucus"])


def draw_skydive_stomach_lesson(canvas: Image.Image, t: float, duration: float) -> None:
    """Freefall lesson: Why doesn't your stomach digest itself?"""
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    p = t / max(duration, 0.1)

    # Sky gradient (ground rushes up near end)
    ground_y = int(h * (0.92 - 0.55 * max(0.0, (p - 0.82) / 0.12))) if p > 0.82 else int(h * 0.92)
    for y in range(0, max(1, ground_y), 4):
        frac = y / max(1, ground_y)
        r = int(SKY["sky_top"][0] + (SKY["sky_low"][0] - SKY["sky_top"][0]) * frac)
        g = int(SKY["sky_top"][1] + (SKY["sky_low"][1] - SKY["sky_top"][1]) * frac)
        b = int(SKY["sky_top"][2] + (SKY["sky_low"][2] - SKY["sky_top"][2]) * frac)
        d.rectangle((0, y, w, y + 4), fill=(r, g, b))
    if p > 0.82:
        d.rectangle((0, ground_y, w, h), fill=SKY["ground"])
        # Trees rushing up
        for i in range(6):
            tx = int(w * 0.1 + i * w * 0.15)
            d.polygon([(tx, ground_y), (tx - 25, ground_y + 80), (tx + 25, ground_y + 80)], fill=(40, 100, 50))

    # Wind streaks
    if 0.08 < p < 0.88:
        for i in range(14):
            x = int((i * 97 + t * 280) % w)
            y0 = int((i * 130 + t * 400) % h)
            d.line((x, y0, x - 8, y0 + 55), fill=(255, 255, 255), width=2)

    _draw_clouds(d, w, h, t, speed=2.2 if p > 0.1 else 0.4)

    # Stage for floating science (right of professor)
    sx = int(w * 0.62)
    sy = int(h * 0.48)

    if p < 0.10:
        # Plane cabin + open door — no logo/title
        d.rectangle((0, 0, w, h), fill=SKY["cabin"])
        # Door opening to sky
        door = int(w * (0.35 + 0.45 * (p / 0.10)))
        d.rectangle((door, 0, w, h), fill=SKY["sky_mid"])
        _draw_clouds(d, w, h, t, speed=0.3)
        # Wind lines into cabin
        for i in range(8):
            y = 200 + i * 160
            d.line((door - 80, y, door + 40, y - 20), fill=(220, 230, 240), width=3)
        _label(d, "Quick! We don't have much time…", (int(w * 0.08), int(h * 0.12)), size=30)
        # Soft smile cue
        d.ellipse((int(w * 0.18), int(h * 0.55), int(w * 0.22), int(h * 0.58)), fill=(255, 220, 180))

    elif p < 0.18:
        # Jump — freefall establish
        _label(d, "One chance. Let's go.", (int(w * 0.42), int(h * 0.12)), size=28)
        # Distant plane above
        d.rounded_rectangle((int(w * 0.7), 40, int(w * 0.95), 90), radius=20, fill=(60, 65, 75))

    elif p < 0.32:
        # SHOW: acid dissolves food (floating model)
        _label(d, "Watch — stomach acid dissolves meat.", (int(w * 0.38), int(h * 0.10)), size=26)
        local = (p - 0.18) / 0.14
        d.ellipse((sx - 90, sy - 50, sx + 90, sy + 60), fill=(55, 45, 25), outline=SKY["acid"], width=4)
        fr = int(36 * (1.0 - local * 0.75))
        d.ellipse((sx - fr, sy - fr // 2, sx + fr, sy + fr // 2), fill=SKY["food"])
        # Acid molecules swirl
        for i in range(10):
            ang = t * 3 + i
            ax = sx + int(math.cos(ang) * (70 + i * 3))
            ay = sy + int(math.sin(ang) * (50 + i * 2))
            d.ellipse((ax - 6, ay - 6, ax + 6, ay + 6), fill=SKY["acid"])

    elif p < 0.48:
        # Question + intact wall
        _label(d, "So why doesn't it dissolve YOU?", (int(w * 0.38), int(h * 0.10)), fill=SKY["coral"], size=28)
        _stomach(d, sx, sy, 1.15, mucus_on=False)
        d.ellipse((sx - 50, sy - 20, sx + 50, sy + 35), fill=(65, 50, 25))
        for i in range(5):
            bx = sx - 35 + i * 18
            by = sy + int(6 * math.sin(t * 5 + i))
            d.ellipse((bx - 5, by - 5, bx + 5, by + 5), fill=SKY["acid"])

    elif p < 0.68:
        # Reveal mucus + cells floating
        _label(d, "A living shield — mucus.", (int(w * 0.42), int(h * 0.10)), fill=SKY["mucus"], size=30)
        _label(d, "Plus cells that rebuild constantly.", (int(w * 0.40), int(h * 0.15)), size=22)
        _stomach(d, sx, sy, 1.2, mucus_on=True)
        # Floating cells
        for i in range(7):
            ang = t * 1.2 + i
            cx = sx + int(math.cos(ang) * 140)
            cy = sy + int(math.sin(ang) * 100)
            d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=SKY["teal"], outline=(20, 100, 95), width=2)
            d.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=(80, 90, 160))

    elif p < 0.82:
        # Analogy + takeaway setup
        _label(d, "Like a raincoat inside a chemical factory.", (int(w * 0.36), int(h * 0.10)), size=26)
        _label(d, "Acid digests dinner. Mucus protects you.", (int(w * 0.38), int(h * 0.16)), fill=SKY["acid"], size=24)
        _stomach(d, sx, sy, 1.05, mucus_on=True)

    elif p < 0.90:
        # Final line + ground rushing
        _label(d, "…and that's why your stomach protects itself.", (int(w * 0.32), int(h * 0.10)), size=26)
        _stomach(d, sx, sy - 20, 0.9, mucus_on=True)

    elif p < 0.96:
        # Cartoon impact — dust puff + flat silhouette (no gore)
        d.rectangle((0, 0, w, h), fill=(200, 210, 180))
        d.rectangle((0, int(h * 0.72), w, h), fill=SKY["ground"])
        # Dust cloud
        for i, (dx, dy, r) in enumerate([(-80, 0, 70), (0, -20, 90), (90, 10, 65), (-40, 40, 50), (50, 35, 55)]):
            d.ellipse(
                (w // 2 + dx - r, int(h * 0.68) + dy - r, w // 2 + dx + r, int(h * 0.68) + dy + r),
                fill=SKY["dust"],
            )
        # Flattened cartoon silhouette
        d.ellipse((w // 2 - 100, int(h * 0.74), w // 2 + 100, int(h * 0.82)), fill=(30, 30, 35))
        # Late parachute
        d.arc((w // 2 - 60, int(h * 0.45), w // 2 + 60, int(h * 0.65)), 200, 340, fill=(240, 80, 80), width=8)
        d.line((w // 2, int(h * 0.62), w // 2, int(h * 0.74)), fill=(40, 40, 40), width=3)

    else:
        # Pop back up, wave
        d.rectangle((0, 0, w, int(h * 0.72)), fill=SKY["sky_mid"])
        d.rectangle((0, int(h * 0.72), w, h), fill=SKY["ground"])
        _draw_clouds(d, w, h, t, speed=0.2)
        _label(d, "See you in the next lesson!", (int(w * 0.28), int(h * 0.12)), fill=SKY["ink"], size=32)
        # Dust settling
        d.ellipse((w // 2 - 120, int(h * 0.70), w // 2 + 120, int(h * 0.78)), fill=(180, 160, 120))


SKYDIVE_DEMOS = {
    "skydive_stomach": draw_skydive_stomach_lesson,
}


def get_skydive_demo(demo_id: str):
    return SKYDIVE_DEMOS.get(demo_id)
