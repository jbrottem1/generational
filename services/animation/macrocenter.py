"""MacroCenter V2 — denser living HQ + show-don't-tell lessons.

Law: every second earns its place. Visual reveals every 2–4s.
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFont

MC = {
    "void": (14, 18, 28),
    "hub": (24, 32, 48),
    "hub2": (32, 44, 64),
    "warm": (255, 200, 145),
    "teal": (56, 210, 190),
    "teal_dim": (36, 130, 125),
    "violet": (150, 125, 235),
    "coral": (255, 110, 95),
    "green": (80, 220, 140),
    "ink": (236, 242, 250),
    "ink_dim": (150, 168, 190),
    "glass": (100, 145, 185),
    "plant": (65, 170, 115),
    "floor": (16, 22, 34),
    "floor_line": (55, 80, 110),
    "lipid_head": (65, 195, 210),
    "lipid_tail": (235, 170, 95),
    "cyto": (42, 85, 115),
    "spot": (255, 230, 190),
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
    d.text(xy, text, fill=fill or MC["ink"], font=_font(size))


def _phospholipid(d, x, y, angle_deg: float, scale: float = 1.0):
    rad = math.radians(angle_deg)
    head_r = int(13 * scale)
    hx = x + int(math.cos(rad) * 6 * scale)
    hy = y + int(math.sin(rad) * 6 * scale)
    d.ellipse((hx - head_r, hy - head_r, hx + head_r, hy + head_r), fill=MC["lipid_head"], outline=MC["teal"], width=2)
    for off in (-0.28, 0.28):
        tr = rad + math.pi + off
        tx = hx + int(math.cos(tr) * 36 * scale)
        ty = hy + int(math.sin(tr) * 36 * scale)
        d.line((hx, hy, tx, ty), fill=MC["lipid_tail"], width=max(3, int(4 * scale)))


def draw_macrocenter(canvas: Image.Image, t: float, *, camera: float = 0.0, focus_spot: bool = True, quiet: bool = False) -> int:
    """Living MacroCenter HQ. ``quiet`` dims secondary chrome so the lesson owns attention."""
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    cam = max(0.0, min(1.0, camera))
    shift = int(cam * w * 0.05)

    d.rectangle((0, 0, w, h), fill=MC["void"])
    floor_y = int(h * 0.78)
    d.rectangle((0, 0, w, floor_y), fill=MC["hub"])

    # Ceiling light wash → focus toward stage
    for i in range(8):
        y0 = 8 + i * 14
        c = 22 + i * 3
        d.rectangle((0, y0, w, y0 + 12), fill=(c, 28 + i, 44 + i))

    # Space observation deck
    wx0, wy0 = int(w * 0.40) - shift // 2, int(h * 0.04)
    wx1, wy1 = int(w * 0.98) - shift // 2, int(h * 0.28)
    d.rounded_rectangle((wx0, wy0, wx1, wy1), radius=12, fill=(8, 12, 22), outline=MC["glass"], width=3)
    # Galaxy spiral
    gcx, gcy = (wx0 + wx1) // 2, (wy0 + wy1) // 2
    for i in range(40):
        ang = t * 0.4 + i * 0.35
        rad = 8 + i * 2.2
        sx = gcx + int(math.cos(ang) * rad)
        sy = gcy + int(math.sin(ang) * rad * 0.45)
        col = MC["teal"] if i % 3 == 0 else (MC["violet"] if i % 3 == 1 else MC["ink_dim"])
        d.ellipse((sx - 2, sy - 2, sx + 2, sy + 2), fill=col)
    _label(d, "OBS DECK", (wx0 + 12, wy0 + 6), fill=MC["ink_dim"], size=16)

    # Wing markers (skip in quiet / excellence focus)
    if not quiet:
        for i, (name, col) in enumerate([("BIO", MC["teal"]), ("PHYS", MC["violet"]), ("CHEM", MC["warm"])]):
            bx = int(w * 0.04) + i * int(w * 0.11)
            d.rounded_rectangle((bx, int(h * 0.30), bx + 90, int(h * 0.345)), radius=6, fill=MC["hub2"], outline=col, width=2)
            _label(d, name, (bx + 18, int(h * 0.308)), fill=col, size=20)

    # Massive holographic display frame (stage)
    bx0 = int(w * 0.40) - shift
    by0 = int(h * 0.36)
    bx1 = int(w * 0.97) - shift
    by1 = int(h * 0.74)
    # Outer glow rings
    d.rounded_rectangle((bx0 - 4, by0 - 4, bx1 + 4, by1 + 4), radius=18, outline=MC["teal_dim"], width=2)
    d.rounded_rectangle((bx0, by0, bx1, by1), radius=16, fill=(18, 26, 40), outline=MC["teal"], width=3)
    # Scanline
    scan_y = by0 + int((by1 - by0) * ((t * 0.35) % 1.0))
    d.line((bx0 + 8, scan_y, bx1 - 8, scan_y), fill=MC["teal_dim"], width=1)
    # AI interface chrome
    d.rounded_rectangle((bx0 + 12, by0 + 10, bx0 + 160, by0 + 42), radius=6, fill=(30, 45, 65), outline=MC["teal"], width=1)
    _label(d, "HOLO · LIVE", (bx0 + 24, by0 + 14), fill=MC["teal"], size=18)
    pulse = 0.5 + 0.5 * math.sin(t * 4)
    d.ellipse((bx0 + 140, by0 + 18, bx0 + 152, by0 + 30), fill=MC["green"] if pulse > 0.3 else MC["teal_dim"])

    # Energy core
    cx, cy = int(w * 0.16), int(h * 0.52)
    pr = int(48 * (0.88 + 0.12 * math.sin(t * 2.6)))
    d.ellipse((cx - pr - 12, cy - pr - 12, cx + pr + 12, cy + pr + 12), outline=MC["violet"], width=2)
    d.ellipse((cx - pr, cy - pr, cx + pr, cy + pr), fill=MC["violet"])
    d.ellipse((cx - pr // 2, cy - pr // 2, cx + pr // 2, cy + pr // 2), fill=MC["teal"])
    d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=MC["warm"])

    # DNA display (left wall) — quiet mode: still, not competing
    dx, dy = int(w * 0.28), int(h * 0.48)
    spin = 0.0 if quiet else t * 1.5
    for i in range(12):
        frac = i / 11
        y = dy - 70 + int(frac * 140)
        ang = frac * 4 * math.pi + spin
        xa = dx + int(math.sin(ang) * 22)
        xb = dx + int(math.sin(ang + math.pi) * 22)
        d.line((xa, y, xb, y), fill=MC["warm"], width=2)
        d.ellipse((xa - 4, y - 4, xa + 4, y + 4), fill=MC["violet"])
        d.ellipse((xb - 4, y - 4, xb + 4, y + 4), fill=MC["teal"])

    # Microscopic chamber portal
    mx, my = int(w * 0.08), int(h * 0.68)
    d.ellipse((mx - 35, my - 35, mx + 35, my + 35), outline=MC["coral"], width=3)
    d.ellipse((mx - 22, my - 22, mx + 22, my + 22), fill=(40, 30, 50))
    if not quiet:
        _label(d, "MICRO", (mx - 28, my + 38), fill=MC["coral"], size=14)

    # Robotic assistant — calm park in quiet mode
    if quiet:
        rx, ry = cx + 70, cy - 40
    else:
        rx = cx + int(math.cos(t * 0.85) * 95)
        ry = cy - 50 + int(math.sin(t * 0.85) * 28)
    d.rounded_rectangle((rx - 20, ry - 16, rx + 20, ry + 16), radius=8, fill=(75, 90, 115), outline=MC["teal"], width=2)
    d.ellipse((rx - 7, ry - 7, rx + 7, ry + 7), fill=MC["warm"])
    d.line((rx, ry + 16, rx, ry + 36), fill=MC["ink_dim"], width=3)

    # Plants
    for px in (int(w * 0.05), int(w * 0.32)):
        base = floor_y - 4
        sway = int(5 * math.sin(t * 1.1 + px * 0.01))
        d.rectangle((px - 10, base - 16, px + 10, base), fill=(55, 45, 35))
        d.ellipse((px - 30 + sway, base - 95, px + 30 + sway, base - 20), fill=MC["plant"])

    # Spotlight on teaching stage
    if focus_spot:
        sx0 = int(w * 0.48) - shift
        d.polygon(
            [(sx0 + 40, int(h * 0.08)), (sx0 + 280, int(h * 0.08)), (int(w * 0.92) - shift, floor_y), (sx0 - 20, floor_y)],
            fill=(40, 48, 58),
        )

    # Floor
    d.rectangle((0, floor_y, w, h), fill=MC["floor"])
    d.line((0, floor_y, w, floor_y), fill=MC["floor_line"], width=3)
    d.rectangle((int(w * 0.42), floor_y + 6, int(w * 0.95), floor_y + 16), fill=(38, 55, 78))

    _label(d, "MACROCENTER", (int(w * 0.42) - shift, 4), fill=MC["teal"], size=24)
    _label(d, "Generational Universe", (int(w * 0.42) - shift, 28), fill=MC["ink_dim"], size=16)
    return floor_y


def draw_cell_membrane_lesson(canvas: Image.Image, t: float, duration: float) -> None:
    """V1 lesson retained for compatibility."""
    draw_cell_membrane_v2_lesson(canvas, t, duration)


def draw_cell_membrane_v2_lesson(canvas: Image.Image, t: float, duration: float) -> None:
    """V2: Smart Security System — show allow/block, bilayer, gates. Dense reveals."""
    p = t / max(duration, 0.1)
    # Camera: snap focus quickly (retention), not slow tourism
    if p < 0.08:
        cam = 0.15
    elif p < 0.55:
        cam = 0.15 + (p - 0.08) / 0.47 * 0.70
    else:
        cam = 0.85 - (p - 0.55) / 0.45 * 0.25

    floor_y = draw_macrocenter(canvas, t, camera=cam, focus_spot=True)
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    shift = int(cam * w * 0.05)
    hx = int(w * 0.68) - shift
    hy = int(h * 0.54)
    stage_top = int(h * 0.40)

    # --- Beat timeline: new meaningful visual every ~2–4s of a ~36s short ---
    if p < 0.08:
        # Hook HUD
        _label(d, "SMART SECURITY", (int(w * 0.44) - shift, stage_top), fill=MC["teal"], size=32)
        _label(d, "every cell · every second", (int(w * 0.44) - shift, stage_top + 40), fill=MC["warm"], size=22)
        r = 55 + int(6 * math.sin(t * 5))
        d.ellipse((hx - r, hy - r, hx + r, hy + r), outline=MC["teal"], width=4)

    elif p < 0.18:
        # Cell appears
        _label(d, "Watch the membrane work.", (int(w * 0.44) - shift, stage_top), size=28)
        r = 105
        d.ellipse((hx - r, hy - r, hx + r, hy + r), fill=MC["cyto"], outline=MC["lipid_head"], width=9)
        d.ellipse((hx - 32, hy - 32, hx + 32, hy + 32), fill=MC["violet"])
        for i in range(14):
            ang = i / 14 * 2 * math.pi + t * 0.5
            _phospholipid(d, hx + int(math.cos(ang) * (r - 2)), hy + int(math.sin(ang) * (r - 2)), math.degrees(ang), 0.5)

    elif p < 0.32:
        # ALLOW — nutrient passes (SHOW)
        local = (p - 0.18) / 0.14
        _label(d, "Nutrient → ALLOWED", (int(w * 0.44) - shift, stage_top), fill=MC["green"], size=30)
        r = 105
        d.ellipse((hx - r, hy - r, hx + r, hy + r), fill=MC["cyto"], outline=MC["lipid_head"], width=9)
        # Gate
        gx, gy = hx - r, hy
        d.rounded_rectangle((gx - 16, gy - 28, gx + 16, gy + 28), radius=8, fill=MC["green"], outline=MC["ink"], width=2)
        nx = hx - 160 + int(local * 200)
        ny = hy
        d.ellipse((nx - 16, ny - 16, nx + 16, ny + 16), fill=MC["teal"])
        d.ellipse((nx - 6, ny - 6, nx + 6, ny + 6), fill=MC["warm"])
        # Green flash ring
        if local > 0.55:
            fr = int(r + 20 * (local - 0.55))
            d.ellipse((hx - fr, hy - fr, hx + fr, hy + fr), outline=MC["green"], width=3)

    elif p < 0.46:
        # BLOCK — invader rejected (SHOW)
        local = (p - 0.32) / 0.14
        _label(d, "Invader → BLOCKED", (int(w * 0.44) - shift, stage_top), fill=MC["coral"], size=30)
        r = 105
        d.ellipse((hx - r, hy - r, hx + r, hy + r), fill=MC["cyto"], outline=MC["lipid_head"], width=9)
        gx, gy = hx + int(r * 0.85), hy - 20
        d.rounded_rectangle((gx - 18, gy - 30, gx + 18, gy + 30), radius=8, fill=MC["coral"], outline=MC["ink"], width=2)
        # Bounce back
        bx = hx + 90 + int(local * 70)
        by = hy - 30
        d.ellipse((bx - 18, by - 18, bx + 18, by + 18), fill=MC["coral"])
        # Spikes
        for ang in range(0, 360, 60):
            rad = math.radians(ang + t * 40)
            d.line(
                (bx + int(math.cos(rad) * 14), by + int(math.sin(rad) * 14),
                 bx + int(math.cos(rad) * 26), by + int(math.sin(rad) * 26)),
                fill=(180, 40, 40),
                width=3,
            )
        d.line((bx - 22, by - 22, bx + 22, by + 22), fill=MC["ink"], width=5)
        d.line((bx + 22, by - 22, bx - 22, by + 22), fill=MC["ink"], width=5)

    elif p < 0.62:
        # Bilayer reveal (macro)
        _label(d, "How? Living bilayer.", (int(w * 0.44) - shift, stage_top), fill=MC["warm"], size=28)
        _label(d, "heads love water · tails hide", (int(w * 0.44) - shift, stage_top + 36), fill=MC["ink_dim"], size=22)
        mid = hy + 10
        left, right = hx - 170, hx + 170
        for x in range(left, right, 26):
            d.ellipse((x - 11, mid - 52, x + 11, mid - 28), fill=MC["lipid_head"], outline=MC["teal"], width=2)
            d.line((x, mid - 28, x - 5, mid - 4), fill=MC["lipid_tail"], width=4)
            d.line((x, mid - 28, x + 5, mid - 4), fill=MC["lipid_tail"], width=4)
        for x in range(left + 13, right, 26):
            d.ellipse((x - 11, mid + 28, x + 11, mid + 54), fill=MC["lipid_head"], outline=MC["teal"], width=2)
            d.line((x, mid + 30, x - 5, mid + 4), fill=MC["lipid_tail"], width=4)
            d.line((x, mid + 30, x + 5, mid + 4), fill=MC["lipid_tail"], width=4)
        # Water dots outside/inside
        for i in range(6):
            d.ellipse((left + 10 + i * 50, mid - 75, left + 18 + i * 50, mid - 67), fill=MC["glass"])
            d.ellipse((left + 20 + i * 50, mid + 65, left + 28 + i * 50, mid + 73), fill=MC["glass"])

    elif p < 0.78:
        # Gate / key
        local = (p - 0.62) / 0.16
        _label(d, "Gates open for the right key.", (int(w * 0.42) - shift, stage_top), fill=MC["violet"], size=28)
        r = 100
        d.ellipse((hx - r, hy - r, hx + r, hy + r), fill=MC["cyto"], outline=MC["lipid_head"], width=8)
        # Channel
        d.rounded_rectangle((hx - 22, hy - r - 5, hx + 22, hy - r + 55), radius=10, fill=MC["violet"], outline=MC["ink"], width=2)
        # Key molecule docking
        ky = hy - r - 40 + int(local * 70)
        d.polygon([(hx - 14, ky), (hx + 14, ky), (hx + 8, ky + 22), (hx - 8, ky + 22)], fill=MC["warm"])
        if local > 0.7:
            _label(d, "OPEN", (hx - 30, hy + 20), fill=MC["green"], size=26)

    elif p < 0.90:
        # Takeaway badge
        _label(d, "Cell membrane = smart security", (int(w * 0.42) - shift, stage_top), fill=MC["teal"], size=28)
        _label(d, "Life stays inside.", (int(w * 0.48) - shift, stage_top + 40), fill=MC["warm"], size=28)
        r = 90
        d.ellipse((hx - r, hy - r + 20, hx + r, hy + r + 20), fill=MC["cyto"], outline=MC["lipid_head"], width=8)
        d.ellipse((hx - 28, hy - 8, hx + 28, hy + 48), fill=MC["violet"])
        # Shield icon
        d.polygon([(hx, hy - 50), (hx + 40, hy - 30), (hx + 30, hy + 20), (hx, hy + 40), (hx - 30, hy + 20), (hx - 40, hy - 30)], outline=MC["teal"], width=4)

    else:
        _label(d, "Next: the keys to those gates.", (int(w * 0.44) - shift, stage_top), fill=MC["ink"], size=28)
        _label(d, "MACROCENTER", (int(w * 0.50) - shift, stage_top + 44), fill=MC["teal"], size=26)
        r = 70 + int(5 * math.sin(t * 3))
        d.ellipse((hx - r, hy - r + 30, hx + r, hy + r + 30), outline=MC["teal"], width=3)

    _ = floor_y


def draw_stomach_excellence_lesson(canvas: Image.Image, t: float, duration: float) -> None:
    """Project Excellence — Why doesn't your stomach digest itself?

    Show-first mystery. One clear focus. Quiet MacroCenter.
    """
    p = t / max(duration, 0.1)
    if p < 0.10:
        cam = 0.25
    elif p < 0.70:
        cam = 0.25 + (p - 0.10) / 0.60 * 0.55
    else:
        cam = 0.80 - (p - 0.70) / 0.30 * 0.20

    floor_y = draw_macrocenter(canvas, t, camera=cam, focus_spot=True, quiet=True)
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    shift = int(cam * w * 0.05)
    hx = int(w * 0.68) - shift
    hy = int(h * 0.55)
    top = int(h * 0.40)

    acid = (255, 200, 70)
    mucus = (120, 220, 200)
    wall = (220, 120, 130)
    food = (180, 110, 70)

    def stomach(cx, cy, scale=1.0, mucus_on=False):
        rw, rh = int(110 * scale), int(85 * scale)
        d.ellipse((cx - rw, cy - rh, cx + rw, cy + rh), fill=(90, 45, 55), outline=wall, width=5)
        if mucus_on:
            # Inner mucus shield
            d.ellipse(
                (cx - rw + 18, cy - rh + 16, cx + rw - 18, cy + rh - 16),
                outline=mucus,
                width=8,
            )
            # Soft glow dashes
            for i in range(8):
                ang = i / 8 * 2 * math.pi + t * 0.8
                px = cx + int(math.cos(ang) * (rw - 28))
                py = cy + int(math.sin(ang) * (rh - 22))
                d.ellipse((px - 5, py - 5, px + 5, py + 5), fill=mucus)

    if p < 0.12:
        # SHOW: acid dissolving food — no lecture yet
        _label(d, "Watch.", (int(w * 0.48) - shift, top), fill=MC["warm"], size=34)
        local = p / 0.12
        # Acid pool
        d.ellipse((hx - 100, hy - 40, hx + 100, hy + 70), fill=(60, 50, 30), outline=acid, width=4)
        fr = int(40 * (1.0 - local * 0.7))
        d.ellipse((hx - fr, hy - 10 - fr // 2, hx + fr, hy - 10 + fr // 2), fill=food)
        if local > 0.4:
            _label(d, "acid dissolves food", (int(w * 0.46) - shift, top + 44), fill=acid, size=22)

    elif p < 0.28:
        # Mystery: same acid, wall intact
        _label(d, "So why not YOU?", (int(w * 0.46) - shift, top), fill=MC["coral"], size=32)
        stomach(hx, hy, 1.05, mucus_on=False)
        # Bubbling acid inside
        d.ellipse((hx - 55, hy - 25, hx + 55, hy + 40), fill=(70, 55, 25))
        for i in range(5):
            bx = hx - 40 + i * 20
            by = hy + int(8 * math.sin(t * 4 + i))
            d.ellipse((bx - 6, by - 6, bx + 6, by + 6), fill=acid)
        # Food dissolving inside
        local = (p - 0.12) / 0.16
        fr = int(28 * (1.0 - local))
        if fr > 4:
            d.ellipse((hx - fr, hy - fr, hx + fr, hy + fr), fill=food)

    elif p < 0.48:
        # REVEAL: mucus shield
        _label(d, "A living shield — mucus.", (int(w * 0.44) - shift, top), fill=mucus, size=30)
        stomach(hx, hy, 1.08, mucus_on=True)
        d.ellipse((hx - 50, hy - 20, hx + 50, hy + 35), fill=(70, 55, 25))
        _label(d, "acid stays here", (hx - 55, hy + 55), fill=acid, size=18)
        _label(d, "you stay here", (hx - 50, hy - 100), fill=mucus, size=18)

    elif p < 0.68:
        # Cell renewal
        _label(d, "And the wall rebuilds — constantly.", (int(w * 0.42) - shift, top), fill=MC["teal"], size=26)
        stomach(hx, hy, 1.05, mucus_on=True)
        # Fresh cells along lining
        for i in range(10):
            ang = -0.8 + i * 0.18
            px = hx + int(math.cos(ang) * 78)
            py = hy + int(math.sin(ang) * 58) - 10
            pulse = 0.7 + 0.3 * math.sin(t * 3 + i)
            r = int(8 * pulse)
            d.ellipse((px - r, py - r, px + r, py + r), fill=MC["warm"] if i % 2 == 0 else MC["teal"])
        _label(d, "new cells replace old ones", (int(w * 0.44) - shift, top + 40), fill=MC["ink_dim"], size=22)

    elif p < 0.86:
        # Side-by-side clarity
        _label(d, "Acid digests dinner. Mucus protects you.", (int(w * 0.40) - shift, top), fill=MC["ink"], size=26)
        # Left: food gone
        d.ellipse((hx - 160, hy - 50, hx - 40, hy + 50), fill=(50, 40, 25), outline=acid, width=3)
        _label(d, "food", (hx - 130, hy + 60), fill=food, size=20)
        d.line((hx - 130, hy - 10, hx - 70, hy + 20), fill=MC["coral"], width=4)
        d.line((hx - 70, hy - 10, hx - 130, hy + 20), fill=MC["coral"], width=4)
        # Right: protected stomach
        stomach(hx + 70, hy, 0.85, mucus_on=True)
        _label(d, "you", (hx + 50, hy + 75), fill=mucus, size=20)

    else:
        _label(d, "That's why your stomach doesn't digest itself.", (int(w * 0.40) - shift, top), fill=MC["teal"], size=26)
        _label(d, "Next: when the shield fails.", (int(w * 0.46) - shift, top + 42), fill=MC["warm"], size=24)
        stomach(hx, hy + 10, 0.95, mucus_on=True)

    _ = floor_y


def draw_brain_energy_lesson(canvas: Image.Image, t: float, duration: float) -> None:
    """Why your brain uses so much energy — show-first communicator lesson."""
    p = t / max(duration, 0.1)
    if p < 0.10:
        cam = 0.20
    elif p < 0.75:
        cam = 0.20 + (p - 0.10) / 0.65 * 0.60
    else:
        cam = 0.80 - (p - 0.75) / 0.25 * 0.25

    floor_y = draw_macrocenter(canvas, t, camera=cam, focus_spot=True, quiet=True)
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    shift = int(cam * w * 0.05)
    hx = int(w * 0.68) - shift
    hy = int(h * 0.54)
    top = int(h * 0.40)
    spark = MC["warm"]
    neuron = MC["teal"]

    def brain(cx, cy, scale=1.0, glow=0.0):
        rw, rh = int(95 * scale), int(75 * scale)
        d.ellipse((cx - rw, cy - rh, cx + rw // 3, cy + rh), fill=(200, 140, 160), outline=(160, 80, 100), width=4)
        d.ellipse((cx - rw // 4, cy - rh, cx + rw, cy + rh), fill=(210, 150, 170), outline=(160, 80, 100), width=4)
        # Folds
        d.arc((cx - rw + 10, cy - rh + 15, cx - 10, cy + 10), 200, 340, fill=(160, 80, 100), width=3)
        d.arc((cx - 20, cy - rh + 20, cx + rw - 15, cy + 15), 200, 340, fill=(160, 80, 100), width=3)
        if glow > 0:
            gr = int(rw + 20 + 15 * glow)
            d.ellipse((cx - gr, cy - gr, cx + gr, cy + gr), outline=spark, width=3)

    if p < 0.12:
        # Hook — body vs tiny brain tease
        _label(d, "Your body is doing something", (int(w * 0.42) - shift, top), fill=MC["ink"], size=28)
        _label(d, "incredible right now…", (int(w * 0.46) - shift, top + 40), fill=MC["warm"], size=28)
        # Silhouette body
        d.ellipse((hx - 35, hy - 120, hx + 35, hy - 50), fill=MC["ink_dim"])  # head
        d.rectangle((hx - 45, hy - 50, hx + 45, hy + 80), fill=MC["hub2"])  # torso

    elif p < 0.28:
        # SHOW: energy drain visualization — brain glowing, stealing fuel
        _label(d, "Watch where the energy goes.", (int(w * 0.44) - shift, top), fill=MC["teal"], size=28)
        brain(hx, hy, 1.1, glow=0.5 + 0.5 * math.sin(t * 4))
        # Energy particles streaming INTO brain
        for i in range(12):
            local = (p - 0.12) / 0.16
            ang = i / 12 * 2 * math.pi + t
            dist = 160 - local * 90
            px = hx + int(math.cos(ang) * dist)
            py = hy + int(math.sin(ang) * dist * 0.7)
            d.ellipse((px - 7, py - 7, px + 7, py + 7), fill=spark if i % 2 == 0 else neuron)

    elif p < 0.42:
        # Punchline reveal — 2% / 20%
        _label(d, "Wait… WHAT?", (int(w * 0.50) - shift, top), fill=MC["coral"], size=34)
        brain(hx - 40, hy, 0.95, glow=1.0)
        # Pie / share callout
        d.rounded_rectangle((hx + 50, hy - 70, hx + 200, hy + 70), radius=12, fill=(30, 40, 58), outline=MC["warm"], width=3)
        _label(d, "2%", (hx + 90, hy - 55), fill=MC["ink_dim"], size=26)
        _label(d, "of your weight", (hx + 70, hy - 20), fill=MC["ink_dim"], size=18)
        _label(d, "≈ 20%", (hx + 75, hy + 10), fill=MC["warm"], size=32)
        _label(d, "of your energy", (hx + 70, hy + 48), fill=MC["warm"], size=18)

    elif p < 0.62:
        # Why — neurons firing / ion pumps
        _label(d, "Here's why.", (int(w * 0.50) - shift, top), fill=MC["teal"], size=30)
        _label(d, "Billions of cells… never off.", (int(w * 0.42) - shift, top + 40), fill=MC["ink_dim"], size=24)
        # Neuron network
        nodes = [(hx - 80, hy - 40), (hx, hy - 60), (hx + 70, hy - 30), (hx - 40, hy + 30), (hx + 50, hy + 40), (hx + 10, hy)]
        for a, b in [(0, 1), (1, 2), (0, 3), (1, 5), (5, 2), (3, 5), (5, 4), (2, 4)]:
            d.line([nodes[a], nodes[b]], fill=neuron, width=3)
        for i, (nx, ny) in enumerate(nodes):
            pulse = 6 + int(4 * abs(math.sin(t * 5 + i)))
            d.ellipse((nx - pulse, ny - pulse, nx + pulse, ny + pulse), fill=spark if i % 2 else neuron)
        # Tiny ATP sparks
        for i in range(6):
            ax = hx - 90 + int((t * 40 + i * 30) % 200)
            ay = hy + 70
            d.ellipse((ax - 4, ay - 4, ax + 4, ay + 4), fill=MC["violet"])

    elif p < 0.80:
        # Real world
        _label(d, "Thinking is expensive.", (int(w * 0.46) - shift, top), fill=MC["warm"], size=30)
        _label(d, "Focus. Memory. Even daydreaming.", (int(w * 0.42) - shift, top + 42), fill=MC["ink"], size=24)
        brain(hx, hy, 1.05, glow=0.8)
        # Fuel icons
        d.rounded_rectangle((hx - 130, hy + 90, hx - 40, hy + 140), radius=8, fill=(40, 55, 70), outline=neuron, width=2)
        _label(d, "glucose", (hx - 118, hy + 105), fill=neuron, size=20)
        d.rounded_rectangle((hx + 20, hy + 90, hx + 120, hy + 140), radius=8, fill=(40, 55, 70), outline=spark, width=2)
        _label(d, "oxygen", (hx + 40, hy + 105), fill=spark, size=20)

    else:
        # Takeaway punchline
        _label(d, "Your brain is a power-hungry genius.", (int(w * 0.40) - shift, top), fill=MC["teal"], size=28)
        _label(d, "Small organ. Huge energy bill.", (int(w * 0.44) - shift, top + 42), fill=MC["warm"], size=26)
        brain(hx, hy + 15, 1.0, glow=1.0)

    _ = floor_y


MACROCENTER_DEMOS = {
    "macro_cell_membrane": draw_cell_membrane_lesson,
    "macro_cell_membrane_v2": draw_cell_membrane_v2_lesson,
    "excellence_stomach": draw_stomach_excellence_lesson,
    "excellence_brain_energy": draw_brain_energy_lesson,
}


def get_macrocenter_demo(demo_id: str):
    return MACROCENTER_DEMOS.get(demo_id)
