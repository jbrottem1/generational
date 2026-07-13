"""Communicator delivery — intentional pauses between spoken beats.

Improves HOW the professor speaks without redesigning the pipeline.
"""

from __future__ import annotations

import base64
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def synthesize_segment(text: str, out_path: Path, *, voice: str = "nova", model: str = "tts-1-hd") -> Path:
    from services.provider_runtime.engine_api import runtime_synthesize_voice

    result = runtime_synthesize_voice(
        text,
        profile={"provider": "openai_tts", "voice": voice},
        settings={"model": model, "voice": voice},
        mode="ai",
    )
    path = Path(str(result.get("path") or ""))
    if path.is_file():
        out_path.write_bytes(path.read_bytes())
        return out_path
    b64 = str(result.get("audio_b64") or "")
    if b64:
        out_path.write_bytes(base64.b64decode(b64))
        return out_path
    # fallback
    if model != "tts-1":
        return synthesize_segment(text, out_path, voice=voice, model="tts-1")
    raise RuntimeError(f"Voice failed: {result.get('error') or result}")



def build_paused_narration(
    beats: list[dict[str, Any]],
    out_path: Path,
    *,
    ffmpeg: str,
    voice: str = "nova",
    model: str = "tts-1-hd",
) -> tuple[Path, float]:
    """Concatenate spoken beats with intentional silence.

    Each beat: {"text": str, "pause_after_sec": float}
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="comm_voice_") as tmp:
        tmp_path = Path(tmp)
        parts: list[Path] = []
        for i, beat in enumerate(beats):
            text = str(beat.get("text") or "").strip()
            if not text:
                continue
            seg = tmp_path / f"seg_{i:02d}.mp3"
            synthesize_segment(text, seg, voice=voice, model=model)
            parts.append(seg)
            pause = float(beat.get("pause_after_sec") or 0.0)
            if pause > 0.05:
                sil = tmp_path / f"sil_{i:02d}.wav"
                subprocess.run(
                    [
                        ffmpeg, "-y",
                        "-f", "lavfi",
                        "-i", f"anullsrc=r=24000:cl=mono",
                        "-t", f"{pause:.3f}",
                        str(sil),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if sil.exists():
                    parts.append(sil)

        if not parts:
            raise RuntimeError("No narration beats")

        # Normalize to wav then concat
        wavs: list[Path] = []
        for j, p in enumerate(parts):
            w = tmp_path / f"w_{j:02d}.wav"
            subprocess.run(
                [ffmpeg, "-y", "-i", str(p), "-ar", "24000", "-ac", "1", str(w)],
                capture_output=True,
                text=True,
                check=False,
            )
            if w.exists():
                wavs.append(w)

        list_file = tmp_path / "concat.txt"
        list_file.write_text("".join(f"file '{w}'\n" for w in wavs), encoding="utf-8")
        concat_wav = tmp_path / "full.wav"
        proc = subprocess.run(
            [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(concat_wav)],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0 or not concat_wav.exists():
            # fallback: filter_complex amix chain via sequential
            raise RuntimeError(f"concat failed: {(proc.stderr or '')[-400:]}")

        subprocess.run(
            [ffmpeg, "-y", "-i", str(concat_wav), "-c:a", "libmp3lame", "-q:a", "3", str(out_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if not out_path.exists():
            out_path.write_bytes(concat_wav.read_bytes())

    # duration
    from services.animation.lip_sync import load_mono_wav

    samples, sr = load_mono_wav(out_path)
    return out_path, len(samples) / float(sr)
