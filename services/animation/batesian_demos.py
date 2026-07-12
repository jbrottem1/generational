"""Biology Foundation demos — Batesian mimicry benchmark series.

White studio + whiteboard diagrams. Scientific labels only — no scenery.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from services.animation.foundation_studio import draw_white_studio
from services.animation.whiteboard import BoardAction, board_rect, render_board_actions


def _font(size: int = 28):
    for path in (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ):
        try:
            return ImageFont.truetype(path, size)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


def _snake(d: ImageDraw.ImageDraw, x: int, y: int, bands: list[tuple[int, int, int]], label: str, danger: bool):
    """Simple horizontal banded snake silhouette."""
    w, h = 160, 28
    d.rounded_rectangle((x, y, x + w, y + h), radius=10, outline=(30, 35, 45), width=2)
    bw = w // max(1, len(bands))
    for i, color in enumerate(bands):
        d.rectangle((x + i * bw + 2, y + 2, x + (i + 1) * bw - 1, y + h - 2), fill=color)
    tag = "DANGEROUS" if danger else "HARMLESS"
    tag_c = (180, 40, 40) if danger else (40, 100, 60)
    d.text((x, y - 22), label, fill=(20, 28, 40), font=_font(20))
    d.text((x, y + h + 4), tag, fill=tag_c, font=_font(18))


def _insect(d: ImageDraw.ImageDraw, x: int, y: int, *, wasp: bool, label: str):
    """Simple insect body — wasp (danger) vs hoverfly (mimic)."""
    body = (240, 200, 40) if wasp else (230, 190, 50)
    stripe = (30, 30, 30)
    d.ellipse((x, y, x + 70, y + 36), fill=body, outline=(30, 35, 45), width=2)
    for i in range(3):
        sx = x + 12 + i * 16
        d.line((sx, y + 4, sx, y + 32), fill=stripe, width=3)
    # Wings
    d.ellipse((x + 50, y - 8, x + 95, y + 18), outline=(100, 140, 180), width=2)
    d.text((x, y + 42), label, fill=(20, 28, 40), font=_font(18))
    tag = "MODEL (sting)" if wasp else "MIMIC (harmless)"
    d.text((x, y + 62), tag, fill=(180, 40, 40) if wasp else (40, 100, 60), font=_font(16))


# --- Video 1: Batesian Mimicry definition ---
BATESIAN_101_ACTIONS: list[BoardAction] = [
    BoardAction("write", "What if pretending saves your life?", start=0.00, end=0.08, row=0, size=30, color=(20, 40, 90)),
    BoardAction("equation", "Batesian Mimicry", start=0.18, end=0.32, row=1, size=46, color=(20, 40, 90)),
    BoardAction("underline", "Batesian Mimicry", start=0.32, end=0.38, row=1, size=46, color=(200, 50, 40)),
    BoardAction("write", "Harmless mimic  ← looks like →  Harmful model", start=0.40, end=0.55, row=2, size=26),
    BoardAction("write", "Predators learn: bright = avoid", start=0.55, end=0.68, row=3, size=28, color=(40, 90, 60)),
    BoardAction("write", "Hoverfly · Scarlet kingsnake", start=0.68, end=0.80, row=4, size=28),
    BoardAction("circle", "Batesian Mimicry", start=0.80, end=0.88, row=1, size=46),
    BoardAction("write", "Safety by resemblance.", start=0.88, end=0.96, row=5, size=30, color=(20, 40, 80)),
]


def draw_batesian_101(canvas: Image.Image, t: float, duration: float) -> None:
    draw_white_studio(canvas)
    p = t / max(duration, 0.1)
    render_board_actions(canvas, BATESIAN_101_ACTIONS, p)
    if 0.45 < p < 0.85:
        d = ImageDraw.Draw(canvas)
        x0, _y0, _x1, y1 = board_rect(*canvas.size)
        _insect(d, x0 + 40, y1 - 130, wasp=True, label="Wasp")
        _insect(d, x0 + 200, y1 - 130, wasp=False, label="Hoverfly")
        d.text((x0 + 130, y1 - 145), "≈", fill=(20, 40, 90), font=_font(36))


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
    if 0.20 < p < 0.78:
        d = ImageDraw.Draw(canvas)
        x0, y0, _x1, _y1 = board_rect(*canvas.size)
        # Coral: red-yellow-black pattern (simplified warning)
        coral = [(200, 40, 40), (240, 200, 40), (30, 30, 35), (200, 40, 40), (240, 200, 40)]
        # Kingsnake mimic: red-black-yellow-ish bands (simplified)
        king = [(200, 40, 40), (30, 30, 35), (240, 180, 50), (30, 30, 35), (200, 40, 40)]
        _snake(d, x0 + 36, y0 + 200, coral, "Coral snake", danger=True)
        _snake(d, x0 + 36, y0 + 280, king, "Scarlet kingsnake", danger=False)
        if p > 0.50:
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
    if 0.18 < p < 0.55:
        d = ImageDraw.Draw(canvas)
        x0, _y0, _x1, y1 = board_rect(*canvas.size)
        _insect(d, x0 + 50, y1 - 120, wasp=True, label="Bee / wasp")
        _insect(d, x0 + 220, y1 - 120, wasp=False, label="Mimic fly")
    if 0.64 < p < 0.90:
        d = ImageDraw.Draw(canvas)
        x0, y0, _x1, _y1 = board_rect(*canvas.size)
        # Simple arrows: predator ←→ prey
        d.text((x0 + 40, y0 + 300), "Predator learning  ⇄  Prey deception", fill=(20, 40, 90), font=_font(24))


BATESIAN_DEMOS = {
    "foundation_batesian_101": draw_batesian_101,
    "foundation_coral_102": draw_coral_102,
    "foundation_bluffing_103": draw_bluffing_103,
}


def get_batesian_demo(demo_id: str):
    return BATESIAN_DEMOS.get(demo_id)
