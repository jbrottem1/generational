"""Expressive character plate renderer — stylized hosts (not sticks / abstract blobs)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def draw_host_plate(
    host: dict[str, Any],
    *,
    out_path: Path,
    size: int = 1024,
    expression: str = "smile",
) -> Path:
    """Draw a full-face stylized host with hair, brows, clothing, silhouette."""
    # Permanent Studio Asset #0001 — always use the locked Doctor renderer / plates.
    if str(host.get("id") or "").upper() == "CHAR-0001":
        from services.studio_assets.the_doctor.renderer import draw_the_doctor_plate

        perm = Path(__file__).resolve().parents[2] / "data" / "studio_assets" / "CHAR-0001-THE-DOCTOR"
        # Prefer official expression plate when available; else draw into out_path
        exp_map = {
            "smile": "smiling",
            "grin": "happy",
            "delight": "excited",
            "focus": "focused",
            "concern": "concerned",
            "curiosity": "curious",
            "raised_brow": "curious",
            "aha": "excited",
            "soft_smile": "smiling",
            "wide_eyes": "surprised",
            "awe": "surprised",
            "puzzled": "thinking",
        }
        exp = exp_map.get(expression, expression)
        canon = perm / "CHARACTER_EXPRESSIONS" / f"{exp}.png"
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if canon.is_file():
            from shutil import copyfile

            copyfile(canon, out_path)
            return out_path
        return draw_the_doctor_plate(out_path=out_path, size=size, expression=exp, pose="front_view")

    from PIL import Image, ImageDraw

    pal = host.get("palette") or {}
    skin = tuple(pal.get("skin") or (255, 214, 180))
    hair = tuple(pal.get("hair") or (40, 32, 28))
    coat = tuple(pal.get("coat") or (28, 48, 86))
    accent = tuple(pal.get("accent") or (48, 170, 160))

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = size // 2, int(size * 0.34)

    # Hair mass (silhouette)
    d.ellipse((cx - 150, cy - 170, cx + 150, cy + 40), fill=hair + (255,))
    # Head
    d.ellipse((cx - 120, cy - 110, cx + 120, cy + 140), fill=skin + (255,), outline=(40, 30, 25, 255), width=5)

    # Eyebrows — expressive by emotion
    brow_y = cy - 10
    if expression in {"concern", "frown", "skeptical"}:
        d.line((cx - 70, brow_y + 8, cx - 20, brow_y - 6), fill=(30, 20, 15, 255), width=8)
        d.line((cx + 20, brow_y - 6, cx + 70, brow_y + 8), fill=(30, 20, 15, 255), width=8)
    elif expression in {"raised_brow", "curiosity", "puzzled", "aha"}:
        d.line((cx - 70, brow_y - 4, cx - 20, brow_y - 18), fill=(30, 20, 15, 255), width=8)
        d.line((cx + 20, brow_y - 2, cx + 70, brow_y - 2), fill=(30, 20, 15, 255), width=8)
    elif expression in {"surprise", "awe", "wide_eyes"}:
        d.line((cx - 70, brow_y - 16, cx - 20, brow_y - 20), fill=(30, 20, 15, 255), width=8)
        d.line((cx + 20, brow_y - 20, cx + 70, brow_y - 16), fill=(30, 20, 15, 255), width=8)
    else:
        d.line((cx - 70, brow_y - 2, cx - 20, brow_y - 8), fill=(30, 20, 15, 255), width=7)
        d.line((cx + 20, brow_y - 8, cx + 70, brow_y - 2), fill=(30, 20, 15, 255), width=7)

    # Eyes (distinct + liveliness)
    eye_open = expression not in {"blink"}
    for ex in (cx - 55, cx + 15):
        if eye_open:
            d.ellipse((ex, cy + 10, ex + 42, cy + 55), fill=(255, 255, 255, 255), outline=(20, 20, 20, 255), width=3)
            pupil = (ex + 14, cy + 24, ex + 30, cy + 42)
            d.ellipse(pupil, fill=(25, 35, 55, 255))
            d.ellipse((ex + 18, cy + 26, ex + 24, cy + 32), fill=(255, 255, 255, 255))  # catchlight
        else:
            d.arc((ex, cy + 20, ex + 42, cy + 50), 200, 340, fill=(20, 20, 20, 255), width=5)

    # Nose
    d.line((cx, cy + 45, cx - 6, cy + 70), fill=(180, 120, 100, 255), width=3)

    # Mouth by expression
    if expression in {"frown", "concern"}:
        d.arc((cx - 35, cy + 95, cx + 35, cy + 125), 200, 340, fill=(120, 50, 50, 255), width=5)
    elif expression in {"surprise", "awe", "wide_eyes"}:
        d.ellipse((cx - 18, cy + 95, cx + 18, cy + 125), outline=(80, 30, 30, 255), width=4)
    elif expression in {"grin", "delight", "excitement", "proud"}:
        d.arc((cx - 45, cy + 85, cx + 45, cy + 130), 20, 160, fill=(140, 40, 50, 255), width=6)
        d.arc((cx - 35, cy + 95, cx + 35, cy + 125), 30, 150, fill=(255, 220, 220, 255), width=3)
    else:  # smile / focus / soft_smile
        d.arc((cx - 40, cy + 90, cx + 40, cy + 125), 20, 160, fill=(120, 40, 40, 255), width=5)

    # Glasses for Atlas
    if "glasses" in str((host.get("signature_clothing") or {}).get("accessory") or "").lower():
        d.ellipse((cx - 70, cy + 5, cx - 10, cy + 60), outline=accent + (255,), width=5)
        d.ellipse((cx + 10, cy + 5, cx + 70, cy + 60), outline=accent + (255,), width=5)
        d.line((cx - 10, cy + 32, cx + 10, cy + 32), fill=accent + (255,), width=4)

    # Goggles on forehead for Piper
    if "goggles" in str((host.get("signature_clothing") or {}).get("accessory") or "").lower():
        d.ellipse((cx - 80, cy - 90, cx - 20, cy - 40), outline=accent + (255,), width=6)
        d.ellipse((cx + 20, cy - 90, cx + 80, cy - 40), outline=accent + (255,), width=6)
        d.line((cx - 20, cy - 65, cx + 20, cy - 65), fill=accent + (255,), width=5)

    # Ear glow / hoodie hood for Nova
    if host.get("id") == "CHAR-NOVA":
        d.ellipse((cx - 160, cy - 40, cx - 110, cy + 40), fill=coat + (180,))
        d.ellipse((cx + 110, cy - 40, cx + 160, cy + 40), fill=coat + (180,))
        d.arc((cx - 130, cy - 150, cx + 130, cy + 20), 200, 340, fill=coat + (255,), width=28)

    # Neck + torso clothing
    d.polygon(
        [(cx - 50, cy + 130), (cx + 50, cy + 130), (cx + 70, cy + 180), (cx - 70, cy + 180)],
        fill=skin + (255,),
    )
    # Coat / body
    d.polygon(
        [
            (cx - 140, cy + 170),
            (cx + 140, cy + 170),
            (cx + 180, int(size * 0.92)),
            (cx - 180, int(size * 0.92)),
        ],
        fill=coat + (255,),
        outline=(20, 20, 20, 255),
    )
    # Accent trim
    d.rectangle((cx - 20, cy + 200, cx + 20, int(size * 0.88)), fill=accent + (255,))

    # Arms with hands (gesture readiness)
    d.line((cx - 100, cy + 220, cx - 220, cy + 320), fill=coat + (255,), width=18)
    d.line((cx + 100, cy + 220, cx + 230, cy + 280), fill=coat + (255,), width=18)
    d.ellipse((cx - 245, cy + 300, cx - 195, cy + 350), fill=skin + (255,), outline=(40, 30, 20, 255), width=3)
    d.ellipse((cx + 210, cy + 255, cx + 260, cy + 305), fill=skin + (255,), outline=(40, 30, 20, 255), width=3)

    # Legs / shoes for silhouette
    d.line((cx - 50, int(size * 0.90), cx - 80, int(size * 0.98)), fill=(30, 30, 35, 255), width=16)
    d.line((cx + 50, int(size * 0.90), cx + 90, int(size * 0.98)), fill=(30, 30, 35, 255), width=16)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def draw_cast_plates(
    hosts: list[dict[str, Any]],
    *,
    plates_dir: Path,
    expression: str = "smile",
) -> dict[str, str]:
    paths: dict[str, str] = {}
    for host in hosts:
        cid = str(host.get("id") or "CHAR")
        path = plates_dir / f"{cid.lower()}_plate.png"
        draw_host_plate(host, out_path=path, expression=expression)
        paths[cid] = str(path)
    return paths
