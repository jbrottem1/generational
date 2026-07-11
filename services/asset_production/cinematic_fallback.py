"""Cinematic fallback stills — real PNG files when AI image providers fail.

Never returns mock:// or blank color beds. Uses ffmpeg lavfi gradients +
optional drawtext so every scene has a unique, frame-filling visual.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from core.log import get_logger
from services.media_production.ffmpeg_assembler import find_ffmpeg

logger = get_logger(__name__)

_INVALID = re.compile(r"[^\w\s\-.,!?']+")

_PALETTES = (
    ("0x0B1D36", "0x1B6CA8"),
    ("0x1A0A2E", "0x7B2CBF"),
    ("0x0D1B1E", "0x2A9D8F"),
    ("0x1C1008", "0xE76F51"),
    ("0x0A1628", "0xF4A261"),
    ("0x101820", "0x457B9D"),
    ("0x1B4332", "0x95D5B2"),
    ("0x210B2C", "0xE0AAFF"),
)


def _safe_label(text: str, limit: int = 42) -> str:
    cleaned = _INVALID.sub("", str(text or "").strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return "Science"
    return cleaned[:limit]


def _palette_for(seed: str) -> tuple[str, str]:
    digest = hashlib.md5(seed.encode("utf-8")).hexdigest()
    idx = int(digest[:8], 16) % len(_PALETTES)
    return _PALETTES[idx]


def generate_cinematic_fallback_still(
    *,
    output_path: str | Path,
    title: str = "",
    overlay: str = "",
    scene_number: int = 1,
    width: int = 1080,
    height: int = 1920,
    seed: str = "",
) -> dict[str, Any]:
    """Write a unique cinematic still PNG. Returns asset-like dict."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = find_ffmpeg()
    if ffmpeg and not (os.path.isfile(ffmpeg) and os.access(ffmpeg, os.X_OK)):
        ffmpeg = ""
    label = _safe_label(overlay or title or f"Scene {scene_number}")
    safe_text = label.replace("'", "").replace(":", " -")
    c1, c2 = _palette_for(seed or f"{title}-{scene_number}-{label}")

    if not ffmpeg:
        return {
            "path": "",
            "provider": "cinematic_fallback",
            "placeholder": True,
            "status": "fallback_no_ffmpeg",
            "error": "ffmpeg unavailable for cinematic fallback",
        }

    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c={c1}:s={width}x{height}:d=1",
        "-f",
        "lavfi",
        "-i",
        f"color=c={c2}:s={width}x{height}:d=1",
        "-filter_complex",
        (
            f"[1]format=rgba,colorchannelmixer=aa=0.5[top];"
            f"[0][top]overlay,"
            f"drawbox=x=0:y=ih*0.62:w=iw:h=ih*0.22:color=black@0.35:t=fill,"
            f"drawtext=text='{safe_text}':"
            f"fontcolor=white:fontsize=44:x=(w-text_w)/2:y=h*0.70:"
            f"borderw=2:bordercolor=black@0.6"
        ),
        "-frames:v",
        "1",
        str(out),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
        if proc.returncode != 0 or not out.exists() or out.stat().st_size < 500:
            simple = [
                ffmpeg,
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c={c1}:s={width}x{height}:d=1",
                "-f",
                "lavfi",
                "-i",
                f"color=c={c2}:s={width}x{height}:d=1",
                "-filter_complex",
                "[1]format=rgba,colorchannelmixer=aa=0.55[top];[0][top]overlay",
                "-frames:v",
                "1",
                str(out),
            ]
            proc = subprocess.run(simple, capture_output=True, text=True, timeout=60, check=False)
            if proc.returncode != 0 or not out.exists() or out.stat().st_size < 500:
                err = (proc.stderr or proc.stdout or "fallback failed")[-400:]
                logger.warning("cinematic_fallback.failed | %s", err)
                return {
                    "path": "",
                    "provider": "cinematic_fallback",
                    "placeholder": True,
                    "status": "failed",
                    "error": err,
                }
        return {
            "path": str(out),
            "local_path": str(out),
            "provider": "cinematic_fallback",
            "placeholder": False,
            "status": "fallback_still",
            "width": width,
            "height": height,
            "prompt": f"cinematic fallback: {label}",
            "media_type": "cinematic_fallback_still",
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("cinematic_fallback.exception")
        return {
            "path": "",
            "provider": "cinematic_fallback",
            "placeholder": True,
            "status": "failed",
            "error": str(exc),
        }
