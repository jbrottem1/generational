"""Animated physics concept demos for Generational Physics Academy.

Drawn onto performer canvases — does not replace the lip-sync engine.
"""

from __future__ import annotations

import math
from typing import Callable

from PIL import Image, ImageDraw, ImageFont


DemoDrawer = Callable[[Image.Image, float, float], None]


def _font(size: int = 36):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", size)
    except Exception:  # noqa: BLE001
        try:
            return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
        except Exception:  # noqa: BLE001
            return ImageFont.load_default()


def _label(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], fill=(20, 30, 50)):
    draw.text(xy, text, fill=fill, font=_font(34))


def draw_force_demo(canvas: Image.Image, t: float, duration: float) -> None:
    """Push a box — force arrow grows, box slides."""
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    # Soft ground
    d.rectangle((0, int(h * 0.78), w, h), fill=(220, 228, 235))
    # Progress of push in mid episode
    phase = min(1.0, max(0.0, (t - duration * 0.25) / max(0.1, duration * 0.45)))
    box_x = int(w * 0.42 + phase * w * 0.28)
    box_y = int(h * 0.62)
    d.rounded_rectangle((box_x, box_y, box_x + 160, box_y + 120), radius=12, fill=(70, 130, 200), outline=(20, 40, 70), width=4)
    # Force arrow
    ax0 = box_x - 140
    ax1 = box_x - 20
    mid = box_y + 60
    d.line((ax0, mid, ax1, mid), fill=(220, 60, 50), width=10)
    d.polygon([(ax1, mid - 18), (ax1 + 28, mid), (ax1, mid + 18)], fill=(220, 60, 50))
    _label(d, "FORCE", (ax0, mid - 55), fill=(180, 40, 40))
    if phase > 0.2:
        _label(d, "motion", (box_x + 20, box_y - 45))


def draw_gravity_demo(canvas: Image.Image, t: float, duration: float) -> None:
    """Objects fall under gravity."""
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    d.rectangle((0, int(h * 0.82), w, h), fill=(210, 200, 180))
    # Falling ball with ease-in
    cycle = 2.4
    local = (t % cycle) / cycle
    y = int(h * 0.22 + (local ** 1.7) * h * 0.52)
    x = int(w * 0.62)
    d.ellipse((x - 45, y - 45, x + 45, y + 45), fill=(240, 90, 70), outline=(40, 20, 20), width=4)
    # Gravity arrow
    d.line((x + 80, int(h * 0.30), x + 80, int(h * 0.55)), fill=(50, 50, 120), width=8)
    d.polygon([(x + 80, int(h * 0.58)), (x + 68, int(h * 0.52)), (x + 92, int(h * 0.52))], fill=(50, 50, 120))
    _label(d, "GRAVITY", (x + 95, int(h * 0.38)), fill=(40, 40, 100))


def draw_velocity_demo(canvas: Image.Image, t: float, duration: float) -> None:
    """Cars at different speeds — velocity = distance/time."""
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    d.rectangle((0, int(h * 0.70), w, int(h * 0.78)), fill=(60, 60, 70))
    # Road dashes
    for i in range(8):
        x = int((t * 120 + i * 140) % (w + 140) - 70)
        d.rectangle((x, int(h * 0.735), x + 50, int(h * 0.745)), fill=(240, 220, 80))

    def car(x: int, y: int, color):
        d.rounded_rectangle((x, y, x + 140, y + 55), radius=10, fill=color, outline=(20, 20, 20), width=3)
        d.ellipse((x + 18, y + 42, x + 48, y + 72), fill=(30, 30, 30))
        d.ellipse((x + 95, y + 42, x + 125, y + 72), fill=(30, 30, 30))

    slow_x = int((t * 90) % (w + 160) - 80)
    fast_x = int((t * 220) % (w + 160) - 80)
    car(slow_x, int(h * 0.58), (80, 160, 220))
    car(fast_x, int(h * 0.48), (220, 90, 70))
    _label(d, "slow", (max(20, slow_x), int(h * 0.54)))
    _label(d, "fast = higher velocity", (max(20, fast_x), int(h * 0.44)), fill=(160, 40, 40))


def draw_momentum_demo(canvas: Image.Image, t: float, duration: float) -> None:
    """Bowling ball vs ping pong — same speed, different momentum."""
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    d.rectangle((0, int(h * 0.78), w, h), fill=(230, 230, 235))
    # Approach then collide metaphor
    phase = (t % 5.0) / 5.0
    bowl_x = int(w * 0.20 + phase * w * 0.35)
    ping_x = int(w * 0.75 - phase * w * 0.15)
    by = int(h * 0.62)
    d.ellipse((bowl_x - 70, by - 70, bowl_x + 70, by + 70), fill=(40, 40, 50), outline=(0, 0, 0), width=4)
    d.ellipse((ping_x - 22, by - 22, ping_x + 22, by + 22), fill=(255, 120, 140), outline=(0, 0, 0), width=3)
    _label(d, "heavy → big momentum", (bowl_x - 80, by - 110))
    _label(d, "light → small momentum", (ping_x - 100, by + 40), fill=(160, 50, 70))
    _label(d, "p = m × v", (int(w * 0.35), int(h * 0.28)), fill=(30, 60, 100))


def draw_potential_energy_demo(canvas: Image.Image, t: float, duration: float) -> None:
    """Lift an object — higher = more stored energy."""
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    d.rectangle((0, int(h * 0.82), w, h), fill=(200, 210, 200))
    # Shelf heights
    d.rectangle((int(w * 0.55), int(h * 0.55), int(w * 0.92), int(h * 0.58)), fill=(120, 90, 60))
    d.rectangle((int(w * 0.55), int(h * 0.35), int(w * 0.92), int(h * 0.38)), fill=(120, 90, 60))
    # Ball rises then rests
    cycle = min(1.0, t / max(0.1, duration * 0.55))
    y = int(h * 0.72 - cycle * h * 0.40)
    x = int(w * 0.70)
    d.ellipse((x - 40, y - 40, x + 40, y + 40), fill=(90, 180, 100), outline=(20, 60, 30), width=4)
    # Energy bar
    bar_h = int(cycle * 220)
    d.rectangle((int(w * 0.48), int(h * 0.70) - bar_h, int(w * 0.52), int(h * 0.70)), fill=(255, 180, 40), outline=(120, 80, 0), width=2)
    _label(d, "POTENTIAL ENERGY", (int(w * 0.48), int(h * 0.22)), fill=(140, 90, 10))
    if cycle > 0.5:
        _label(d, "higher = more stored", (int(w * 0.55), int(h * 0.28)))


DEMOS: dict[str, DemoDrawer] = {
    "force": draw_force_demo,
    "gravity": draw_gravity_demo,
    "velocity": draw_velocity_demo,
    "momentum": draw_momentum_demo,
    "potential_energy": draw_potential_energy_demo,
}


def get_demo(demo_id: str) -> DemoDrawer | None:
    return DEMOS.get(demo_id)
