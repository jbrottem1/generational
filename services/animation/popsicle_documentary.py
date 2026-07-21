"""Educational scene frames for How Popsicles Are Made (16:9 documentary).

Uses layout engine rules: no overlapping text, measured boxes, safe margins,
semantic callouts only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from services.animation.layout_engine import fit_font_size, measure_text, resolve_collisions, TextBox, paint_text_boxes


W, H = 1920, 1080
MARGIN = 64
BG_TOP = (18, 42, 66)
BG_BOTTOM = (12, 28, 48)
ACCENT = (255, 140, 60)
TEXT = (245, 248, 252)
MUTED = (180, 198, 214)
CARD = (28, 52, 78)


def _font(size: int):
    for path in (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


def _gradient(canvas: Image.Image) -> None:
    d = ImageDraw.Draw(canvas)
    for y in range(H):
        t = y / max(H - 1, 1)
        r = int(BG_TOP[0] * (1 - t) + BG_BOTTOM[0] * t)
        g = int(BG_TOP[1] * (1 - t) + BG_BOTTOM[1] * t)
        b = int(BG_TOP[2] * (1 - t) + BG_BOTTOM[2] * t)
        d.line((0, y, W, y), fill=(r, g, b))


def _title_bar(d: ImageDraw.ImageDraw, chapter: str, title: str) -> None:
    d.rounded_rectangle((MARGIN, MARGIN, W - MARGIN, MARGIN + 110), radius=16, fill=CARD)
    d.text((MARGIN + 28, MARGIN + 18), chapter, fill=ACCENT, font=_font(28))
    d.text((MARGIN + 28, MARGIN + 54), title, fill=TEXT, font=_font(42))


def draw_title_card(path: Path) -> Path:
    canvas = Image.new("RGB", (W, H))
    _gradient(canvas)
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((W // 2 - 520, H // 2 - 160, W // 2 + 520, H // 2 + 160), radius=24, fill=CARD)
    d.text((W // 2 - 460, H // 2 - 110), "GENERATIONAL", fill=ACCENT, font=_font(36))
    d.text((W // 2 - 460, H // 2 - 50), "How Popsicles Are Made", fill=TEXT, font=_font(56))
    d.text((W // 2 - 460, H // 2 + 40), "A documentary-style educational benchmark", fill=MUTED, font=_font(28))
    d.text((W // 2 - 460, H // 2 + 90), "Production Benchmark #002", fill=MUTED, font=_font(24))
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)
    return path


def draw_chapter_card(path: Path, chapter: str, title: str, bullets: list[str]) -> Path:
    canvas = Image.new("RGB", (W, H))
    _gradient(canvas)
    d = ImageDraw.Draw(canvas)
    _title_bar(d, chapter, title)
    y = MARGIN + 150
    boxes: list[TextBox] = []
    for bullet in bullets[:6]:
        size, lines = fit_font_size(bullet, W - 2 * MARGIN - 40, 70, preferred=34, minimum=22)
        for line in lines:
            tw, th = measure_text(line, size)
            boxes.append(TextBox(text=f"• {line}" if line == lines[0] else f"  {line}", x=MARGIN + 20, y=y, w=tw + 30, h=th, font_size=size, color=TEXT))
            y += th + 18
    paint_text_boxes(canvas, resolve_collisions(boxes, (MARGIN, MARGIN + 140, W - MARGIN, H - MARGIN)))
    canvas.save(path)
    return path


def draw_ingredient_grid(path: Path) -> Path:
    canvas = Image.new("RGB", (W, H))
    _gradient(canvas)
    d = ImageDraw.Draw(canvas)
    _title_bar(d, "Chapter 2", "What Goes Into a Popsicle?")
    ingredients = [
        ("Water", "The solvent that freezes into ice structure"),
        ("Fruit juice / puree", "Flavor, color, and some natural sugars"),
        ("Sugar", "Sweetness + freezing-point depression"),
        ("Natural flavors", "Concentrated aroma compounds from foods"),
        ("Artificial flavors", "Synthesized aroma molecules (when used)"),
        ("Food coloring", "Visual identity and consistency"),
        ("Stabilizers", "Control ice texture and melt behavior"),
    ]
    cols, rows = 2, 4
    card_w = (W - 2 * MARGIN - 24) // cols
    card_h = 120
    top = MARGIN + 150
    for i, (name, role) in enumerate(ingredients):
        c, r = i % cols, i // cols
        x0 = MARGIN + c * (card_w + 24)
        y0 = top + r * (card_h + 16)
        d.rounded_rectangle((x0, y0, x0 + card_w, y0 + card_h), radius=14, fill=CARD, outline=(60, 90, 120), width=2)
        d.text((x0 + 20, y0 + 18), name, fill=ACCENT, font=_font(30))
        size, lines = fit_font_size(role, card_w - 40, 50, preferred=22, minimum=16)
        yy = y0 + 58
        for line in lines:
            d.text((x0 + 20, yy), line, fill=TEXT, font=_font(size))
            yy += size + 6
    canvas.save(path)
    return path


def draw_factory_flow(path: Path) -> Path:
    canvas = Image.new("RGB", (W, H))
    _gradient(canvas)
    d = ImageDraw.Draw(canvas)
    _title_bar(d, "Chapter 3", "Factory Production Flow")
    steps = [
        "1. Mix",
        "2. Test",
        "3. Fill molds",
        "4. Insert sticks",
        "5. Freeze",
        "6. Package",
        "7. Ship",
    ]
    n = len(steps)
    y = H // 2
    gap = (W - 2 * MARGIN) // n
    for i, step in enumerate(steps):
        cx = MARGIN + gap * i + gap // 2
        d.ellipse((cx - 70, y - 70, cx + 70, y + 70), fill=CARD, outline=ACCENT, width=4)
        size, lines = fit_font_size(step, 120, 80, preferred=22, minimum=16)
        tw, th = measure_text(lines[0], size)
        d.text((cx - tw // 2, y - th // 2), lines[0], fill=TEXT, font=_font(size))
        if i < n - 1:
            d.line((cx + 78, y, cx + gap - 78, y), fill=ACCENT, width=5)
            # Arrow head
            d.polygon([(cx + gap - 78, y), (cx + gap - 98, y - 12), (cx + gap - 98, y + 12)], fill=ACCENT)
    d.text((MARGIN, H - 100), "Educational overview of common frozen-novelty manufacturing stages", fill=MUTED, font=_font(24))
    canvas.save(path)
    return path


def draw_freezing_science(path: Path) -> Path:
    canvas = Image.new("RGB", (W, H))
    _gradient(canvas)
    d = ImageDraw.Draw(canvas)
    _title_bar(d, "Chapter 4", "Why Freezing Works")
    # Left: pure water
    d.rounded_rectangle((MARGIN, 180, W // 2 - 24, H - MARGIN), radius=18, fill=CARD)
    d.text((MARGIN + 28, 210), "Pure water", fill=ACCENT, font=_font(34))
    d.text((MARGIN + 28, 270), "Freezes at 0°C / 32°F", fill=TEXT, font=_font(28))
    # Crystal sketch
    d.polygon([(220, 420), (300, 360), (380, 420), (340, 520), (260, 520)], outline=(140, 200, 255), width=4)
    d.text((MARGIN + 28, 580), "Ordered ice crystals form easily", fill=MUTED, font=_font(24))
    # Right: sugared water
    d.rounded_rectangle((W // 2 + 24, 180, W - MARGIN, H - MARGIN), radius=18, fill=CARD)
    d.text((W // 2 + 52, 210), "Water + sugar", fill=ACCENT, font=_font(34))
    d.text((W // 2 + 52, 270), "Freezing point drops", fill=TEXT, font=_font(28))
    d.ellipse((W // 2 + 180, 400, W // 2 + 280, 500), outline=(255, 200, 80), width=4)
    d.ellipse((W // 2 + 300, 450, W // 2 + 360, 510), outline=(255, 200, 80), width=3)
    d.text((W // 2 + 52, 560), "Sugar interferes with crystal packing", fill=MUTED, font=_font(24))
    d.text((W // 2 + 52, 600), "→ softer bite, different melt", fill=MUTED, font=_font(24))
    # Semantic arrow from left to right concept
    d.line((W // 2 - 40, 450, W // 2 + 40, 450), fill=ACCENT, width=5)
    d.polygon([(W // 2 + 40, 450), (W // 2 + 20, 438), (W // 2 + 20, 462)], fill=ACCENT)
    canvas.save(path)
    return path


def draw_crystal_compare(path: Path) -> Path:
    canvas = Image.new("RGB", (W, H))
    _gradient(canvas)
    d = ImageDraw.Draw(canvas)
    _title_bar(d, "Chapter 4", "Ice Crystal Size = Texture")
    d.rounded_rectangle((MARGIN, 180, W // 2 - 24, H - MARGIN), radius=18, fill=CARD)
    d.text((MARGIN + 30, 210), "Small crystals", fill=ACCENT, font=_font(36))
    for i in range(18):
        x = MARGIN + 80 + (i % 6) * 70
        y = 320 + (i // 6) * 80
        d.ellipse((x, y, x + 28, y + 28), outline=(160, 210, 255), width=3)
    d.text((MARGIN + 30, H - 140), "Smoother mouthfeel", fill=TEXT, font=_font(28))
    d.rounded_rectangle((W // 2 + 24, 180, W - MARGIN, H - MARGIN), radius=18, fill=CARD)
    d.text((W // 2 + 54, 210), "Large crystals", fill=ACCENT, font=_font(36))
    for i in range(6):
        x = W // 2 + 120 + (i % 3) * 160
        y = 360 + (i // 3) * 180
        d.ellipse((x, y, x + 90, y + 90), outline=(160, 210, 255), width=4)
    d.text((W // 2 + 54, H - 140), "Icy / coarse sensation", fill=TEXT, font=_font(28))
    canvas.save(path)
    return path


def draw_facts_board(path: Path, facts: list[str]) -> Path:
    canvas = Image.new("RGB", (W, H))
    _gradient(canvas)
    d = ImageDraw.Draw(canvas)
    _title_bar(d, "Chapter 5", "Verified Interesting Facts")
    y = 180
    boxes: list[TextBox] = []
    for i, fact in enumerate(facts[:5], 1):
        size, lines = fit_font_size(f"{i}. {fact}", W - 2 * MARGIN - 40, 90, preferred=30, minimum=20)
        for j, line in enumerate(lines):
            tw, th = measure_text(line, size)
            boxes.append(TextBox(text=line, x=MARGIN + 24, y=y, w=tw, h=th, font_size=size, color=TEXT))
            y += th + 10
        y += 24
    paint_text_boxes(canvas, resolve_collisions(boxes, (MARGIN, 160, W - MARGIN, H - MARGIN)))
    canvas.save(path)
    return path


def draw_future_board(path: Path) -> Path:
    canvas = Image.new("RGB", (W, H))
    _gradient(canvas)
    d = ImageDraw.Draw(canvas)
    _title_bar(d, "Chapter 6", "The Future of Frozen Desserts")
    themes = [
        ("Healthier recipes", "Less added sugar; fruit-forward formulas"),
        ("Natural colors", "Plant pigments instead of synthetic dyes"),
        ("Sustainable packaging", "Recyclable wraps; less plastic waste"),
        ("Smarter manufacturing", "Tighter temperature control; less waste"),
    ]
    for i, (title, body) in enumerate(themes):
        y0 = 180 + i * 180
        d.rounded_rectangle((MARGIN, y0, W - MARGIN, y0 + 150), radius=16, fill=CARD)
        d.text((MARGIN + 28, y0 + 28), title, fill=ACCENT, font=_font(34))
        d.text((MARGIN + 28, y0 + 80), body, fill=TEXT, font=_font(26))
    canvas.save(path)
    return path


def draw_process_closeup(path: Path, title: str, subtitle: str, motif: str) -> Path:
    canvas = Image.new("RGB", (W, H))
    _gradient(canvas)
    d = ImageDraw.Draw(canvas)
    _title_bar(d, "Factory Close-Up", title)
    # Motif drawings
    cx, cy = W // 2, H // 2 + 40
    if motif == "tank":
        d.rounded_rectangle((cx - 220, cy - 160, cx + 220, cy + 160), radius=20, fill=(40, 70, 95), outline=ACCENT, width=5)
        d.ellipse((cx - 80, cy - 40, cx + 80, cy + 40), outline=(120, 180, 220), width=4)
    elif motif == "mold":
        for i in range(5):
            x = cx - 300 + i * 140
            d.rounded_rectangle((x, cy - 120, x + 100, cy + 140), radius=12, fill=(50, 80, 110), outline=ACCENT, width=3)
            d.rectangle((x + 40, cy + 140, x + 60, cy + 220), fill=(180, 140, 90))
    elif motif == "freeze":
        d.ellipse((cx - 180, cy - 140, cx + 180, cy + 140), outline=(140, 200, 255), width=6)
        for ang in range(0, 360, 45):
            import math
            x1 = cx + int(100 * math.cos(math.radians(ang)))
            y1 = cy + int(100 * math.sin(math.radians(ang)))
            x2 = cx + int(160 * math.cos(math.radians(ang)))
            y2 = cy + int(160 * math.sin(math.radians(ang)))
            d.line((x1, y1, x2, y2), fill=(140, 200, 255), width=3)
    elif motif == "pack":
        d.rounded_rectangle((cx - 200, cy - 100, cx + 200, cy + 100), radius=8, fill=(60, 90, 70), outline=ACCENT, width=4)
        d.text((cx - 90, cy - 20), "CARTON", fill=TEXT, font=_font(36))
    else:
        d.ellipse((cx - 120, cy - 120, cx + 120, cy + 120), fill=ACCENT)
    d.text((MARGIN + 20, H - 90), subtitle, fill=MUTED, font=_font(26))
    canvas.save(path)
    return path


def build_all_scenes(out_dir: Path) -> list[dict[str, Any]]:
    """Create all documentary scene stills and return assemble plan entries."""
    out_dir.mkdir(parents=True, exist_ok=True)
    plan: list[dict[str, Any]] = []

    def add(name: str, builder, weight: float, effect: str = "documentary_slow_zoom", **kwargs):
        path = out_dir / f"{name}.png"
        builder(path, **kwargs) if kwargs else builder(path)
        plan.append(
            {
                "scene_id": name,
                "path": str(path),
                "duration_sec": weight,
                "effect": {"effect": effect, "zoom": {"start_scale": 1.0, "end_scale": 1.06}},
            }
        )

    add("00_title", draw_title_card, 8.0, "ken_burns")
    add(
        "01_history",
        draw_chapter_card,
        14.0,
        chapter="Chapter 1",
        title="The History of the Popsicle",
        bullets=[
            "An accidental frozen drink on a stick",
            "Frank Epperson, credited inventor (1905 story)",
            "From neighborhood treat to patented confection",
            "The Epsicle becomes the Popsicle",
        ],
    )
    add("01b_history_detail", draw_chapter_card, 16.0, chapter="Chapter 1", title="From Accident to Industry", bullets=[
        "Bay Area childhood experiment with flavored powder + water",
        "Stirring stick left in overnight — mixture froze",
        "Years later: public sales and a 1920s patent",
        "A handheld frozen drink — no spoon required",
    ])
    add("02_ingredients", draw_ingredient_grid, 20.0)
    add("03_factory", draw_factory_flow, 16.0)
    add("03b_mix", draw_process_closeup, 12.0, title="Ingredient Mixing", subtitle="Batches are blended for consistent sweetness and flavor", motif="tank")
    add("03c_fill", draw_process_closeup, 12.0, title="Mold Filling & Stick Insertion", subtitle="Liquid mix enters molds; sticks are placed before full freeze", motif="mold")
    add("03d_freeze", draw_process_closeup, 12.0, title="Freezing Tunnel", subtitle="Rapid cold sets the structure for demolding and packaging", motif="freeze")
    add("03e_pack", draw_process_closeup, 10.0, title="Packaging & Shipping", subtitle="Wrapped, cased, and kept cold through distribution", motif="pack")
    add("04_science", draw_freezing_science, 18.0)
    add("04b_crystals", draw_crystal_compare, 16.0)
    add(
        "05_facts",
        draw_facts_board,
        18.0,
        facts=[
            "Popsicle began as a brand name for a patented ice pop on a stick.",
            "Sugar does more than sweeten — it changes how water freezes.",
            "Ice pops usually freeze still in molds, unlike churned ice cream.",
            "Crystal size is a major reason one pop feels smooth and another feels icy.",
            "Stabilizers help manage texture as temperature swings during storage.",
        ],
    )
    add("06_future", draw_future_board, 16.0)
    add(
        "07_outro",
        draw_chapter_card,
        10.0,
        chapter="Takeaway",
        title="A Simple Treat — Serious Food Science",
        bullets=[
            "History, ingredients, factories, and physics meet in one snack",
            "Freezing is chemistry you can taste",
            "Thanks for learning with Generational",
        ],
    )
    return plan
