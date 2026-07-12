"""Offline smoke narration — amplitude-modulated audio for CI / no-API renders."""

from __future__ import annotations

import math
import struct
import subprocess
import wave
from pathlib import Path
from typing import Any


def _beat_duration(text: str) -> float:
    words = max(1, len(text.split()))
    return max(1.4, words * 0.38)


def build_smoke_narration(
    beats: list[dict[str, Any]],
    out_path: Path,
    *,
    ffmpeg: str,
    sample_rate: int = 24000,
) -> tuple[Path, float]:
    """Synthesize speech-like amplitude envelope without TTS (smoke / CI only)."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wav_path = out_path.with_suffix(".wav")

    samples: list[int] = []
    for beat in beats:
        text = str(beat.get("text") or "").strip()
        if not text:
            continue
        dur = _beat_duration(text)
        n = int(dur * sample_rate)
        for i in range(n):
            t = i / sample_rate
            env = 0.15 + 0.85 * abs(math.sin(t * 11.0)) * abs(math.sin(t * 4.7))
            val = int(env * 7000 * math.sin(2 * math.pi * 165 * t))
            samples.append(max(-32767, min(32767, val)))
        pause = float(beat.get("pause_after_sec") or 0.0)
        samples.extend([0] * int(pause * sample_rate))

    if not samples:
        raise RuntimeError("No narration beats")

    with wave.open(str(wav_path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))

    duration = len(samples) / sample_rate
    subprocess.run(
        [ffmpeg, "-y", "-i", str(wav_path), "-codec:a", "libmp3lame", "-q:a", "4", str(out_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if not out_path.is_file():
        out_path = wav_path
    return out_path, duration
