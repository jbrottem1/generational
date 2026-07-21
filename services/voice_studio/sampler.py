"""Generate Voice Studio narration samples via existing synthesize_voice."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from services.media_production.voice import synthesize_voice
from services.voice_studio.scoring import sanitize_voice_filename

ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = ROOT / "data" / "voice_studio" / "samples"

# ~15 seconds of educational narration at a measured pace
DEFAULT_SAMPLE_TEXT = (
    "Artificial intelligence is not a machine that thinks like a human. "
    "It is a system that learns patterns from data and uses those patterns to make useful predictions. "
    "When you understand that one idea, hype becomes easier to sort from evidence."
)

COMPARISON_TEXT = (
    "Artificial intelligence is not a machine that thinks like a human. "
    "It is a system that learns patterns from data and uses those patterns to make useful predictions."
)


def generate_voice_sample(
    voice: dict[str, Any],
    *,
    text: str = "",
    out_dir: Path | None = None,
    mode: str = "sample",
) -> dict[str, Any]:
    """Synthesize one sample for a voice using the existing ElevenLabs path."""
    voice_id = str(voice.get("voice_id") or "").strip()
    name = str(voice.get("name") or "voice")
    if not voice_id:
        return {"ok": False, "error": "missing voice_id", "voice_id": "", "name": name}

    dest_dir = out_dir or (SAMPLES_DIR / mode)
    dest_dir.mkdir(parents=True, exist_ok=True)
    script = (text or DEFAULT_SAMPLE_TEXT).strip()

    result = synthesize_voice(
        script,
        profile={
            "provider_voice_id": voice_id,
            "voice_id": voice_id,
            "narrator_profile": "professor",
            "profile_id": f"voice_studio_{sanitize_voice_filename(name, voice_id)}",
        },
        settings={"preferred_provider": "elevenlabs"},
        narrator="professor",
        preferred_provider="elevenlabs",
        allow_fallback=False,
    )
    src = Path(str(result.get("path") or ""))
    dest = dest_dir / f"{sanitize_voice_filename(name, voice_id)}.mp3"
    if src.exists():
        shutil.copy2(src, dest)
        path = dest
    else:
        path = src

    return {
        "ok": bool(result.get("ok")) and path.exists(),
        "provider": result.get("provider"),
        "placeholder": result.get("placeholder"),
        "error": result.get("error") or "",
        "voice_id": voice_id,
        "name": name,
        "path": str(path) if path else "",
        "duration_sec": result.get("duration_sec"),
        "audio_qa": result.get("audio_qa"),
    }


def generate_samples_for_voices(
    voices: list[dict[str, Any]],
    *,
    text: str = "",
    mode: str = "sample",
) -> list[dict[str, Any]]:
    rows = []
    for voice in voices:
        rows.append(generate_voice_sample(voice, text=text, mode=mode))
    return rows
