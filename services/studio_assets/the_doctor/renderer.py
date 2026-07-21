"""Procedural plate renderer — The Doctor (humanoid cyborg, not generic robot)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.studio_assets.the_doctor.profile import COLOR_SYSTEM, the_doctor_host_profile


def _rgb(key: str) -> tuple[int, int, int]:
    return tuple(COLOR_SYSTEM[key]["rgb"])  # type: ignore[return-value]


def draw_the_doctor_plate(
    *,
    out_path: Path,
    size: int = 1024,
    expression: str = "teaching",
    pose: str = "front_view",
    wardrobe: str = "primary_outfit",
) -> Path:
    from PIL import Image, ImageDraw

    white = _rgb("primary")
    titanium = _rgb("secondary")
    accent = _rgb("accent")
    deep = _rgb("deep_accent")
    eyes = _rgb("visors")
    shadow = _rgb("chassis_shadow")

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = size // 2

    # Pose offsets
    lean = 0
    arm_l = -1.0
    arm_r = 1.0
    sit = False
    if pose in {"left_side"}:
        lean = -40
    elif pose in {"right_side"}:
        lean = 40
    elif pose in {"three_quarter", "hero"}:
        lean = -18
    elif pose in {"pointing", "teaching", "medical_demonstration"}:
        arm_r = 1.55
    elif pose in {"clipboard"}:
        arm_l = -1.35
    elif pose in {"hologram_interaction"}:
        arm_l = -1.2
        arm_r = 1.2
    elif pose in {"hands_behind_back"}:
        arm_l = -0.35
        arm_r = 0.35
    elif pose in {"walking", "running"}:
        arm_l = -1.25
        arm_r = 1.1
    elif pose in {"sitting"}:
        sit = True
    elif pose in {"rear_view"}:
        # Backplate silhouette
        d.ellipse((cx - 110, 160, cx + 110, 390), fill=white + (255,), outline=titanium + (255,), width=6)
        d.rectangle((cx - 55, 360, cx + 55, 720), fill=white + (255,), outline=titanium + (255,), width=5)
        d.line((cx - 20, 220, cx - 20, 340), fill=accent + (220,), width=6)
        d.line((cx + 20, 220, cx + 20, 340), fill=accent + (220,), width=6)
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path)
        return out_path

    cy = int(size * 0.30) + (lean // 3)
    hx = cx + lean

    # Soft ambient glow (trust / warmth — not horror)
    d.ellipse((hx - 200, cy - 180, hx + 200, cy + 220), fill=accent + (28,))

    # Head — friendly rounded medical chassis
    d.ellipse((hx - 118, cy - 105, hx + 118, cy + 135), fill=white + (255,), outline=titanium + (255,), width=6)
    # Cheek soft titanium plates
    d.ellipse((hx - 115, cy + 40, hx - 70, cy + 95), fill=titanium + (90,))
    d.ellipse((hx + 70, cy + 40, hx + 115, cy + 95), fill=titanium + (90,))

    # Crown sensor band
    d.arc((hx - 90, cy - 95, hx + 90, cy - 20), 200, 340, fill=accent + (255,), width=8)

    # Brows
    brow_y = cy - 8
    exp = expression.lower()
    if exp in {"concerned", "serious", "focused"}:
        d.line((hx - 68, brow_y + 6, hx - 18, brow_y - 4), fill=shadow + (255,), width=7)
        d.line((hx + 18, brow_y - 4, hx + 68, brow_y + 6), fill=shadow + (255,), width=7)
    elif exp in {"curious", "thinking", "listening"}:
        d.line((hx - 68, brow_y - 2, hx - 18, brow_y - 16), fill=shadow + (255,), width=7)
        d.line((hx + 18, brow_y, hx + 68, brow_y - 2), fill=shadow + (255,), width=7)
    elif exp in {"surprised", "excited", "laughing"}:
        d.line((hx - 68, brow_y - 14, hx - 18, brow_y - 20), fill=shadow + (255,), width=7)
        d.line((hx + 18, brow_y - 20, hx + 68, brow_y - 14), fill=shadow + (255,), width=7)
    elif exp in {"happy", "smiling", "teaching", "confident"}:
        d.line((hx - 68, brow_y - 4, hx - 18, brow_y - 10), fill=shadow + (255,), width=6)
        d.line((hx + 18, brow_y - 10, hx + 68, brow_y - 4), fill=shadow + (255,), width=6)
    else:
        d.line((hx - 68, brow_y - 2, hx - 18, brow_y - 6), fill=shadow + (255,), width=6)
        d.line((hx + 18, brow_y - 6, hx + 68, brow_y - 2), fill=shadow + (255,), width=6)

    # Eyes — intelligent warm blue cores
    eye_open = exp not in {"blink"}
    for ex in (hx - 58, hx + 16):
        if eye_open:
            d.ellipse((ex, cy + 8, ex + 44, cy + 58), fill=(255, 255, 255, 255), outline=titanium + (255,), width=3)
            core = eyes if exp not in {"concerned", "serious"} else deep
            d.ellipse((ex + 10, cy + 20, ex + 34, cy + 46), fill=core + (255,))
            d.ellipse((ex + 16, cy + 24, ex + 24, cy + 32), fill=(255, 255, 255, 230))
            # micro LED ring
            d.arc((ex + 6, cy + 16, ex + 38, cy + 50), 30, 150, fill=accent + (180,), width=2)
        else:
            d.arc((ex, cy + 22, ex + 44, cy + 52), 200, 340, fill=shadow + (255,), width=5)

    # Nose bridge plate
    d.line((hx, cy + 48, hx - 5, cy + 72), fill=titanium + (200,), width=3)

    # Mouth / visemes-ish shapes
    if exp in {"concerned", "serious"}:
        d.arc((hx - 32, cy + 98, hx + 32, cy + 128), 200, 340, fill=deep + (255,), width=5)
    elif exp in {"surprised"}:
        d.ellipse((hx - 16, cy + 98, hx + 16, cy + 128), outline=deep + (255,), width=4)
    elif exp in {"laughing", "excited", "happy", "smiling", "teaching", "confident"}:
        d.arc((hx - 42, cy + 88, hx + 42, cy + 132), 20, 160, fill=deep + (255,), width=6)
        d.arc((hx - 30, cy + 98, hx + 30, cy + 124), 30, 150, fill=accent + (160,), width=3)
    elif exp in {"thinking", "listening", "focused", "neutral"}:
        d.arc((hx - 28, cy + 100, hx + 28, cy + 122), 15, 165, fill=deep + (220,), width=4)
    else:
        d.arc((hx - 36, cy + 94, hx + 36, cy + 126), 20, 160, fill=deep + (255,), width=5)

    # Chin glow accent (signature)
    d.ellipse((hx - 18, cy + 118, hx + 18, cy + 138), fill=accent + (90,))

    # Neck + torso
    d.polygon(
        [(hx - 40, cy + 130), (hx + 40, cy + 130), (hx + 55, cy + 175), (hx - 55, cy + 175)],
        fill=titanium + (255,),
    )

    # Wardrobe coat variant tint
    coat = white
    trim = accent
    if wardrobe == "formal_laboratory":
        coat = (250, 252, 255)
        trim = deep
    elif wardrobe == "research":
        coat = (236, 242, 248)
        trim = accent
    elif wardrobe == "field_expedition":
        coat = (220, 230, 235)
        trim = (70, 140, 120)
    elif wardrobe == "space_exploration":
        coat = (225, 230, 240)
        trim = (100, 140, 220)
    elif wardrobe == "medical_examination":
        coat = (248, 252, 255)
        trim = (60, 180, 160)
    elif wardrobe == "winter":
        coat = (230, 236, 245)
        trim = deep
    elif wardrobe == "protective_equipment":
        coat = (210, 220, 230)
        trim = (220, 120, 70)

    body_bottom = int(size * (0.78 if sit else 0.90))
    d.polygon(
        [
            (hx - 145, cy + 165),
            (hx + 145, cy + 165),
            (hx + 175, body_bottom),
            (hx - 175, body_bottom),
        ],
        fill=coat + (255,),
        outline=titanium + (255,),
    )
    # Chest medical interface
    d.rounded_rectangle((hx - 55, cy + 210, hx + 55, cy + 290), radius=12, fill=shadow + (40,), outline=trim + (255,), width=4)
    d.ellipse((hx - 18, cy + 230, hx + 18, cy + 266), fill=trim + (220,))
    d.rectangle((hx - 40, cy + 275, hx + 40, cy + 282), fill=trim + (180,))

    # Arms
    ly = cy + 210
    d.line((hx - 100, ly, hx + int(-220 * abs(arm_l)), ly + int(110 * abs(arm_l))), fill=coat + (255,), width=20)
    d.line((hx + 100, ly, hx + int(220 * abs(arm_r) * (1 if arm_r > 0 else -1)), ly + int(90 * abs(arm_r))), fill=coat + (255,), width=20)
    # Hands (humanoid soft mitts — not claws)
    d.ellipse((hx - 245, ly + 95, hx - 195, ly + 145), fill=white + (255,), outline=titanium + (255,), width=3)
    hx_r = hx + int(200 * abs(arm_r))
    d.ellipse((hx_r - 25, ly + 70, hx_r + 25, ly + 120), fill=white + (255,), outline=titanium + (255,), width=3)

    if pose in {"clipboard", "teaching", "medical_demonstration"}:
        d.rectangle((hx - 250, ly + 70, hx - 180, ly + 160), fill=(250, 250, 252, 255), outline=titanium + (255,), width=3)
        d.line((hx - 240, ly + 90, hx - 190, ly + 90), fill=trim + (255,), width=2)
        d.line((hx - 240, ly + 105, hx - 190, ly + 105), fill=trim + (200,), width=2)

    if pose in {"hologram_interaction", "pointing"}:
        d.ellipse((hx + 160, ly + 40, hx + 210, ly + 90), outline=accent + (200,), width=3)
        d.ellipse((hx + 170, ly + 50, hx + 200, ly + 80), fill=accent + (60,))

    # Legs
    if sit:
        d.line((hx - 55, body_bottom - 20, hx - 140, body_bottom + 40), fill=titanium + (255,), width=18)
        d.line((hx + 55, body_bottom - 20, hx + 150, body_bottom + 30), fill=titanium + (255,), width=18)
    elif pose in {"walking", "running"}:
        d.line((hx - 50, body_bottom - 30, hx - 100, int(size * 0.98)), fill=shadow + (255,), width=16)
        d.line((hx + 40, body_bottom - 30, hx + 110, int(size * 0.96)), fill=shadow + (255,), width=16)
    else:
        d.line((hx - 50, body_bottom - 10, hx - 70, int(size * 0.98)), fill=shadow + (255,), width=16)
        d.line((hx + 50, body_bottom - 10, hx + 75, int(size * 0.98)), fill=shadow + (255,), width=16)

    # Signature nameplate (subtle)
    d.rectangle((hx - 48, cy + 175, hx + 48, cy + 192), fill=deep + (180,))
    try:
        d.text((hx - 36, cy + 176), "THE DOCTOR", fill=(255, 255, 255, 255))
    except Exception:
        pass

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def draw_environment_plate(*, out_path: Path, room: str, size: tuple[int, int] = (1280, 720)) -> Path:
    """Stylized set plate for GMRI rooms — living, not empty."""
    from PIL import Image, ImageDraw

    w, h = size
    img = Image.new("RGB", (w, h), (232, 240, 248))
    d = ImageDraw.Draw(img)
    accent = _rgb("accent")
    white = _rgb("primary")
    titanium = _rgb("secondary")
    deep = _rgb("deep_accent")

    # Floor / wall
    d.rectangle((0, int(h * 0.62), w, h), fill=(210, 220, 230))
    d.rectangle((0, 0, w, int(h * 0.62)), fill=(238, 245, 252))
    # Window light
    d.rectangle((int(w * 0.65), 40, w - 40, int(h * 0.45)), fill=(190, 220, 245))
    d.rectangle((int(w * 0.65), 40, w - 40, int(h * 0.45)), outline=titanium, width=3)

    # Room-specific furniture block
    d.rounded_rectangle((80, int(h * 0.35), 420, int(h * 0.70)), radius=16, fill=white, outline=titanium, width=3)
    d.rounded_rectangle((480, int(h * 0.40), 760, int(h * 0.72)), radius=12, fill=(250, 252, 255), outline=accent, width=3)
    # Active screens
    for i, x in enumerate((500, 560, 620, 680)):
        d.rectangle((x, int(h * 0.45), x + 40, int(h * 0.55)), fill=accent if i % 2 == 0 else deep)
    # Plants / life
    d.ellipse((100, int(h * 0.48), 160, int(h * 0.58)), fill=(90, 160, 110))
    d.rectangle((125, int(h * 0.58), 140, int(h * 0.68)), fill=(120, 90, 60))
    # People / robots silhouettes (ambient life)
    for px in (900, 980, 1100):
        d.ellipse((px, int(h * 0.42), px + 28, int(h * 0.48)), fill=titanium)
        d.rectangle((px + 4, int(h * 0.48), px + 24, int(h * 0.68)), fill=white)

    d.text((40, 24), f"GMRI · {room.replace('_', ' ').title()}", fill=deep)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def default_host_for_plates() -> dict[str, Any]:
    return the_doctor_host_profile()
