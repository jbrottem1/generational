"""Biology Academy demo overlays — Generational Method visual teaching.

Clean lab aesthetic. One concept per lesson. No pipeline redesign.
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFont

# Educational palette — intentional, readable, uncluttered
PAL = {
    "bg": (232, 238, 244),
    "floor": (200, 210, 220),
    "floor_line": (150, 162, 176),
    "board": (248, 251, 255),
    "board_edge": (110, 130, 150),
    "ink": (28, 42, 62),
    "accent": (20, 120, 140),  # teal — life / highlight
    "cell": (90, 180, 170),
    "nucleus": (70, 90, 160),
    "membrane": (40, 110, 120),
    "dna_a": (90, 70, 180),
    "dna_b": (50, 140, 200),
    "base": (240, 180, 60),
    "invader": (200, 55, 55),
    "defender": (50, 110, 200),
    "antibody": (80, 170, 220),
    "muscle": (210, 90, 90),
    "muscle_dark": (150, 50, 55),
    "lung": (230, 150, 150),
    "rbc": (200, 45, 55),
    "o2": (70, 150, 220),
    "label": (30, 50, 80),
    "warn": (160, 40, 40),
}


def _font(size: int = 28):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", size)
    except Exception:  # noqa: BLE001
        try:
            return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
        except Exception:  # noqa: BLE001
            return ImageFont.load_default()


def _label(d: ImageDraw.ImageDraw, text: str, xy, fill=None, size: int = 28):
    d.text(xy, text, fill=fill or PAL["label"], font=_font(size))


def draw_lab_floor(canvas: Image.Image) -> int:
    """Modern lab backdrop + whiteboard; return floor_y."""
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    floor_y = int(h * 0.78)
    d.rectangle((0, 0, w, floor_y), fill=PAL["bg"])
    d.rectangle((0, floor_y, w, h), fill=PAL["floor"])
    d.line((0, floor_y, w, floor_y), fill=PAL["floor_line"], width=3)
    # Whiteboard
    d.rounded_rectangle(
        (int(w * 0.40), int(h * 0.08), int(w * 0.96), int(h * 0.40)),
        radius=10,
        fill=PAL["board"],
        outline=PAL["board_edge"],
        width=3,
    )
    # Microscope silhouette on bench (lab prop)
    mx, my = int(w * 0.88), floor_y - 20
    d.ellipse((mx - 28, my - 18, mx + 28, my + 8), fill=(90, 100, 115))
    d.rectangle((mx - 10, my - 90, mx + 10, my - 10), fill=(70, 80, 95))
    d.ellipse((mx - 22, my - 110, mx + 22, my - 75), fill=(55, 65, 80), outline=(40, 50, 60), width=2)
    d.rectangle((mx + 8, my - 100, mx + 55, my - 88), fill=(60, 70, 85))
    return floor_y


def _cell(d, cx, cy, r, *, nucleus=True, highlight=False):
    fill = PAL["cell"] if not highlight else (110, 200, 185)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill, outline=PAL["membrane"], width=4)
    # membrane detail
    d.ellipse((cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6), outline=(60, 140, 135), width=2)
    if nucleus:
        nr = int(r * 0.38)
        d.ellipse((cx - nr, cy - nr, cx + nr, cy + nr), fill=PAL["nucleus"], outline=(40, 55, 110), width=2)


def draw_cells_lesson(canvas: Image.Image, t: float, duration: float) -> None:
    """Why every living thing is made of cells."""
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    floor_y = draw_lab_floor(canvas)
    p = t / max(duration, 0.1)

    # Microscope view circle (right stage)
    vx, vy, vr = int(w * 0.68), int(h * 0.55), 200
    d.ellipse((vx - vr, vy - vr, vx + vr, vy + vr), fill=(245, 250, 252), outline=(80, 100, 120), width=5)

    if p < 0.12:
        _label(d, "What are YOU made of?", (int(w * 0.44), int(h * 0.14)), size=30)
        # Single mysterious blob
        _cell(d, vx, vy, 70)
    elif p < 0.35:
        _label(d, "Zoom in… CELLS", (int(w * 0.46), int(h * 0.14)), fill=PAL["accent"], size=30)
        # Growing cluster
        local = (p - 0.12) / 0.23
        n = 1 + int(local * 6)
        positions = [(0, 0), (-70, -40), (75, -30), (-50, 55), (60, 50), (-90, 20), (20, -80)]
        for i, (dx, dy) in enumerate(positions[:n]):
            _cell(d, vx + dx, vy + dy, 42, highlight=(i == 0))
    elif p < 0.55:
        _label(d, "Building blocks of life", (int(w * 0.44), int(h * 0.12)), size=28)
        _label(d, "membrane · nucleus · machinery", (int(w * 0.44), int(h * 0.20)), size=24)
        _cell(d, vx - 40, vy, 85, highlight=True)
        _label(d, "CELL", (vx - 70, vy + 100), fill=PAL["accent"], size=26)
    elif p < 0.75:
        _label(d, "You · trees · bacteria · whales", (int(w * 0.42), int(h * 0.12)), size=26)
        _label(d, "All built from cells", (int(w * 0.46), int(h * 0.20)), fill=PAL["accent"], size=28)
        for i, (dx, dy, r) in enumerate([(-80, -50, 35), (70, -40, 40), (-20, 40, 50), (90, 45, 30), (-90, 30, 28)]):
            _cell(d, vx + dx, vy + dy, r, nucleus=(i % 2 == 0))
    else:
        _label(d, "Life's unit:", (int(w * 0.48), int(h * 0.14)), size=28)
        _label(d, "the CELL", (int(w * 0.50), int(h * 0.22)), fill=PAL["accent"], size=36)
        for dx, dy in [(-60, -30), (55, -25), (-30, 45), (50, 40)]:
            _cell(d, vx + dx, vy + dy, 38)


def _dna_helix(d, cx, cy, height, t, *, turns=3):
    """Draw a clean double helix."""
    pts_a, pts_b = [], []
    steps = 40
    for i in range(steps + 1):
        frac = i / steps
        y = cy - height // 2 + int(frac * height)
        ang = frac * turns * 2 * math.pi + t * 1.8
        amp = 38
        xa = cx + int(math.sin(ang) * amp)
        xb = cx + int(math.sin(ang + math.pi) * amp)
        pts_a.append((xa, y))
        pts_b.append((xb, y))
        if i % 3 == 0:
            d.line((xa, y, xb, y), fill=PAL["base"], width=3)
    for i in range(len(pts_a) - 1):
        d.line([pts_a[i], pts_a[i + 1]], fill=PAL["dna_a"], width=5)
        d.line([pts_b[i], pts_b[i + 1]], fill=PAL["dna_b"], width=5)


def draw_dna_lesson(canvas: Image.Image, t: float, duration: float) -> None:
    """DNA: the instruction manual of life."""
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    draw_lab_floor(canvas)
    p = t / max(duration, 0.1)

    hx, hy = int(w * 0.68), int(h * 0.52)

    if p < 0.10:
        _label(d, "How does a cell know what to do?", (int(w * 0.42), int(h * 0.14)), size=26)
        # Closed book metaphor
        d.rounded_rectangle((hx - 70, hy - 90, hx + 70, hy + 90), radius=6, fill=(180, 90, 60), outline=(100, 40, 20), width=3)
        _label(d, "???", (hx - 28, hy - 20), fill=(255, 230, 200), size=32)
    elif p < 0.40:
        _label(d, "DNA — the instruction manual", (int(w * 0.42), int(h * 0.12)), fill=PAL["accent"], size=28)
        _dna_helix(d, hx, hy, 280, t)
        _label(d, "double helix", (hx - 55, hy + 160), size=24)
    elif p < 0.65:
        _label(d, "A · T · C · G  — four letters", (int(w * 0.42), int(h * 0.12)), size=28)
        _label(d, "Sequence = the recipe", (int(w * 0.44), int(h * 0.20)), fill=PAL["accent"], size=26)
        _dna_helix(d, hx - 40, hy, 240, t)
        # Base letter callouts
        for i, (letter, col) in enumerate([("A", (220, 80, 80)), ("T", (80, 140, 220)), ("C", (80, 180, 120)), ("G", (220, 160, 50))]):
            bx = int(w * 0.82)
            by = int(h * 0.42) + i * 55
            d.rounded_rectangle((bx, by, bx + 70, by + 44), radius=8, fill=col)
            _label(d, letter, (bx + 22, by + 6), fill=(255, 255, 255), size=28)
    elif p < 0.85:
        _label(d, "Same alphabet. Different books.", (int(w * 0.42), int(h * 0.12)), size=26)
        _label(d, "You · oak tree · fruit fly", (int(w * 0.44), int(h * 0.20)), fill=PAL["accent"], size=26)
        _dna_helix(d, hx, hy, 260, t * 0.8)
    else:
        _label(d, "DNA = life's written instructions", (int(w * 0.42), int(h * 0.14)), fill=PAL["accent"], size=28)
        _dna_helix(d, hx, hy, 260, t)


def draw_immune_lesson(canvas: Image.Image, t: float, duration: float) -> None:
    """How your immune system finds invaders."""
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    draw_lab_floor(canvas)
    p = t / max(duration, 0.1)

    # Tissue field
    fx, fy, fr = int(w * 0.68), int(h * 0.55), 210
    d.ellipse((fx - fr, fy - fr, fx + fr, fy + fr), fill=(245, 235, 235), outline=(180, 140, 140), width=4)

    # Invader (virus-like)
    ix, iy = fx + 40, fy - 30
    if p < 0.15:
        _label(d, "Something doesn't belong…", (int(w * 0.42), int(h * 0.14)), size=28)
        d.ellipse((ix - 35, iy - 35, ix + 35, iy + 35), fill=PAL["invader"], outline=(120, 20, 20), width=3)
        for ang in range(0, 360, 45):
            rad = math.radians(ang)
            d.line(
                (ix + int(math.cos(rad) * 30), iy + int(math.sin(rad) * 30),
                 ix + int(math.cos(rad) * 48), iy + int(math.sin(rad) * 48)),
                fill=(160, 30, 30),
                width=4,
            )
        _label(d, "INVADER", (ix - 50, iy + 50), fill=PAL["warn"], size=24)
    elif p < 0.40:
        _label(d, "Immune cells patrol & check IDs", (int(w * 0.42), int(h * 0.12)), size=26)
        d.ellipse((ix - 35, iy - 35, ix + 35, iy + 35), fill=PAL["invader"], outline=(120, 20, 20), width=3)
        # Approaching defender
        local = (p - 0.15) / 0.25
        dx = fx - 120 + int(local * 100)
        dy = fy + 40
        d.ellipse((dx - 40, dy - 40, dx + 40, dy + 40), fill=PAL["defender"], outline=(20, 50, 120), width=3)
        _label(d, "white blood cell", (dx - 70, dy + 48), fill=PAL["defender"], size=22)
        # Scan beam
        d.line((dx + 30, dy - 10, ix - 30, iy + 10), fill=PAL["antibody"], width=3)
    elif p < 0.65:
        _label(d, "Match found → TAG it", (int(w * 0.44), int(h * 0.12)), fill=PAL["accent"], size=28)
        d.ellipse((ix - 35, iy - 35, ix + 35, iy + 35), fill=PAL["invader"], outline=(120, 20, 20), width=3)
        # Antibodies Y shapes attaching
        for ox, oy in [(-50, -20), (45, -25), (-30, 40), (40, 35)]:
            ax, ay = ix + ox, iy + oy
            d.line((ax, ay, ax - 12, ay - 22), fill=PAL["antibody"], width=4)
            d.line((ax, ay, ax + 12, ay - 22), fill=PAL["antibody"], width=4)
            d.line((ax, ay, ax, ay + 20), fill=PAL["antibody"], width=4)
        d.ellipse((fx - 80, fy + 50, fx - 10, fy + 120), fill=PAL["defender"], outline=(20, 50, 120), width=3)
        _label(d, "antibodies", (ix - 40, iy + 70), fill=PAL["antibody"], size=22)
    elif p < 0.85:
        _label(d, "Destroy · remember · protect", (int(w * 0.42), int(h * 0.12)), size=28)
        # Invader fading / broken
        d.ellipse((ix - 25, iy - 25, ix + 25, iy + 25), fill=(220, 140, 140), outline=(120, 20, 20), width=2)
        d.line((ix - 30, iy - 30, ix + 30, iy + 30), fill=PAL["warn"], width=5)
        d.line((ix + 30, iy - 30, ix - 30, iy + 30), fill=PAL["warn"], width=5)
        d.ellipse((fx - 90, fy + 20, fx - 20, fy + 90), fill=PAL["defender"], outline=(20, 50, 120), width=3)
        _label(d, "memory ready", (fx - 100, fy + 100), fill=PAL["defender"], size=22)
    else:
        _label(d, "Find. Tag. Eliminate.", (int(w * 0.46), int(h * 0.14)), fill=PAL["accent"], size=30)
        d.ellipse((fx - 50, fy - 40, fx + 20, fy + 30), fill=PAL["defender"], outline=(20, 50, 120), width=3)
        _label(d, "Your immune system", (fx - 80, fy + 50), size=24)


def draw_muscle_lesson(canvas: Image.Image, t: float, duration: float) -> None:
    """Why muscles actually grow — micro-damage → repair → stronger."""
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    floor_y = draw_lab_floor(canvas)
    p = t / max(duration, 0.1)

    mx, my = int(w * 0.68), int(h * 0.52)

    def fibers(damage=0.0, thicker=0.0):
        for i in range(5):
            y = my - 90 + i * 40
            thick = 14 + int(thicker * 10)
            color = PAL["muscle"] if i % 2 == 0 else PAL["muscle_dark"]
            d.rounded_rectangle((mx - 100, y, mx + 100, y + thick), radius=6, fill=color)
            if damage > 0 and i in (1, 3):
                # micro-tears
                for tx in range(-60, 70, 35):
                    d.line((mx + tx, y + 2, mx + tx + 8, y + thick - 2), fill=(255, 200, 200), width=2)

    if p < 0.12:
        _label(d, "Lift heavy. Muscle grows. How?", (int(w * 0.42), int(h * 0.14)), size=28)
        fibers(0, 0)
        _label(d, "muscle fibers", (mx - 60, my + 120), size=24)
    elif p < 0.35:
        _label(d, "Training = tiny controlled stress", (int(w * 0.42), int(h * 0.12)), size=26)
        fibers(0.8, 0)
        _label(d, "micro-damage", (mx - 55, my + 120), fill=PAL["warn"], size=24)
        # Dumbbell icon
        bx, by = int(w * 0.88), floor_y - 80
        d.rectangle((bx - 8, by - 40, bx + 8, by + 40), fill=(80, 85, 95))
        d.ellipse((bx - 28, by - 50, bx + 12, by - 20), fill=(60, 65, 75))
        d.ellipse((bx - 12, by + 20, bx + 28, by + 50), fill=(60, 65, 75))
    elif p < 0.60:
        _label(d, "Body repairs… and overbuilds", (int(w * 0.42), int(h * 0.12)), fill=PAL["accent"], size=28)
        local = (p - 0.35) / 0.25
        fibers(0.3 * (1 - local), local)
        # Repair sparkles
        for sx, sy in [(mx - 40, my - 60), (mx + 50, my), (mx - 20, my + 50)]:
            d.ellipse((sx, sy, sx + 10, sy + 10), fill=PAL["o2"])
        _label(d, "repair + adapt", (mx - 55, my + 120), fill=PAL["accent"], size=24)
    elif p < 0.82:
        _label(d, "Rest + protein = growth signal", (int(w * 0.42), int(h * 0.12)), size=26)
        fibers(0, 1.0)
        _label(d, "thicker fibers", (mx - 55, my + 120), fill=PAL["muscle"], size=24)
    else:
        _label(d, "Stress → repair → stronger", (int(w * 0.44), int(h * 0.14)), fill=PAL["accent"], size=30)
        fibers(0, 1.0)


def draw_oxygen_lesson(canvas: Image.Image, t: float, duration: float) -> None:
    """Journey of oxygen: lungs → blood → cells."""
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    draw_lab_floor(canvas)
    p = t / max(duration, 0.1)

    # Pathway stations
    lung_x, lung_y = int(w * 0.52), int(h * 0.48)
    heart_x, heart_y = int(w * 0.72), int(h * 0.42)
    cell_x, cell_y = int(w * 0.82), int(h * 0.62)

    def lungs():
        d.ellipse((lung_x - 55, lung_y - 70, lung_x - 5, lung_y + 50), fill=PAL["lung"], outline=(160, 80, 80), width=3)
        d.ellipse((lung_x + 5, lung_y - 70, lung_x + 55, lung_y + 50), fill=PAL["lung"], outline=(160, 80, 80), width=3)
        d.line((lung_x, lung_y - 90, lung_x, lung_y - 20), fill=(120, 90, 90), width=6)

    def heart():
        d.ellipse((heart_x - 35, heart_y - 25, heart_x + 5, heart_y + 25), fill=(180, 40, 50))
        d.ellipse((heart_x - 5, heart_y - 25, heart_x + 35, heart_y + 25), fill=(180, 40, 50))
        d.polygon(
            [(heart_x - 32, heart_y + 5), (heart_x + 32, heart_y + 5), (heart_x, heart_y + 45)],
            fill=(180, 40, 50),
        )

    def tissue_cell():
        _cell(d, cell_x, cell_y, 45)

    def rbc(x, y, with_o2=True):
        d.ellipse((x - 22, y - 14, x + 22, y + 14), fill=PAL["rbc"], outline=(120, 20, 30), width=2)
        if with_o2:
            d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=PAL["o2"])

    if p < 0.12:
        _label(d, "One breath. Where does O₂ go?", (int(w * 0.42), int(h * 0.14)), size=28)
        lungs()
        # Inhale arrows
        for i in range(3):
            ax = lung_x - 40 + i * 40
            d.line((ax, lung_y - 130, ax, lung_y - 95), fill=PAL["o2"], width=4)
            d.polygon([(ax - 8, lung_y - 100), (ax + 8, lung_y - 100), (ax, lung_y - 85)], fill=PAL["o2"])
    elif p < 0.35:
        _label(d, "Lungs → blood (red blood cells)", (int(w * 0.42), int(h * 0.12)), fill=PAL["accent"], size=26)
        lungs()
        local = (p - 0.12) / 0.23
        x = int(lung_x + local * (heart_x - lung_x))
        y = int(lung_y + local * (heart_y - lung_y))
        rbc(x, y)
        heart()
    elif p < 0.60:
        _label(d, "Heart pumps O₂-rich blood out", (int(w * 0.42), int(h * 0.12)), size=26)
        lungs()
        heart()
        local = (p - 0.35) / 0.25
        x = int(heart_x + local * (cell_x - heart_x))
        y = int(heart_y + local * (cell_y - heart_y))
        rbc(x, y)
        tissue_cell()
        d.line((heart_x + 30, heart_y + 20, cell_x - 40, cell_y - 20), fill=(200, 80, 90), width=3)
    elif p < 0.82:
        _label(d, "Cells take O₂ → make energy", (int(w * 0.42), int(h * 0.12)), fill=PAL["accent"], size=28)
        lungs()
        heart()
        tissue_cell()
        rbc(cell_x - 70, cell_y - 10, with_o2=False)
        # Energy spark
        d.ellipse((cell_x - 8, cell_y - 8, cell_x + 8, cell_y + 8), fill=(255, 200, 60))
        _label(d, "ATP energy", (cell_x - 40, cell_y + 55), size=22)
    else:
        _label(d, "Air → blood → cells → energy", (int(w * 0.42), int(h * 0.14)), fill=PAL["accent"], size=28)
        lungs()
        heart()
        tissue_cell()
        rbc(int((lung_x + heart_x) / 2), int((lung_y + heart_y) / 2) - 20)
        rbc(int((heart_x + cell_x) / 2), int((heart_y + cell_y) / 2))


BIOLOGY_DEMOS = {
    "bio_cells": draw_cells_lesson,
    "fluid_cells": draw_cells_lesson,  # Fluid Motion benchmark — same demo, better motion
    "bio_dna": draw_dna_lesson,
    "bio_immune": draw_immune_lesson,
    "bio_muscle": draw_muscle_lesson,
    "bio_oxygen": draw_oxygen_lesson,
}


def get_biology_demo(demo_id: str):
    return BIOLOGY_DEMOS.get(demo_id)
