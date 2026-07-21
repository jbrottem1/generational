"""Narration audio QA — reject silent / corrupt / unusable TTS output."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def validate_narration_audio(
    path: str | Path | None,
    *,
    timing: dict | None = None,
    min_duration_sec: float = 0.4,
    require_renderer_compatible: bool = True,
) -> dict[str, Any]:
    """Validate a narration file for pipeline use."""
    report: dict[str, Any] = {
        "ok": False,
        "file_exists": False,
        "format_ok": False,
        "non_zero_duration": False,
        "renderer_compatible": False,
        "synchronization_metadata": False,
        "caption_timing_compatible": False,
        "not_silent": False,
        "loudness_ok": False,
        "duration_sec": 0.0,
        "bytes": 0,
        "hard_fails": [],
        "warnings": [],
    }
    if not path:
        report["hard_fails"].append("missing_path")
        return report
    p = Path(str(path))
    if not p.is_absolute():
        p = ROOT / p
    report["path"] = str(p)
    if not p.exists() or not p.is_file():
        report["hard_fails"].append("file_missing")
        return report
    report["file_exists"] = True
    size = p.stat().st_size
    report["bytes"] = size
    if size < 200:
        report["hard_fails"].append("file_too_small")
        return report

    suffix = p.suffix.lower()
    report["format_ok"] = suffix in {".mp3", ".wav", ".m4a", ".aac", ".ogg"}
    if not report["format_ok"]:
        report["hard_fails"].append(f"unsupported_format:{suffix or 'none'}")

    duration = _probe_duration(p)
    report["duration_sec"] = duration
    report["non_zero_duration"] = duration >= min_duration_sec
    if not report["non_zero_duration"]:
        report["hard_fails"].append("zero_or_short_duration")

    # Renderer compatibility: readable via ffprobe + common codec
    report["renderer_compatible"] = bool(report["format_ok"] and report["non_zero_duration"] and _has_audio_stream(p))
    if require_renderer_compatible and not report["renderer_compatible"]:
        report["hard_fails"].append("not_renderer_compatible")

    loud = _probe_loudness(p)
    report["mean_volume_db"] = loud.get("mean_volume")
    report["max_volume_db"] = loud.get("max_volume")
    # Reject near-silence (mean below -50 dB) when ffmpeg available
    mean = loud.get("mean_volume")
    if mean is None:
        report["not_silent"] = report["non_zero_duration"] and size > 2000
        report["loudness_ok"] = report["not_silent"]
        report["warnings"].append("loudness_unverified")
    else:
        report["not_silent"] = float(mean) > -50.0
        report["loudness_ok"] = float(mean) > -45.0
        if not report["not_silent"]:
            report["hard_fails"].append("silent_or_near_silent")
        max_v = loud.get("max_volume")
        if max_v is not None and float(max_v) >= -0.5:
            report["warnings"].append("possible_clipping")

    timing = timing or {}
    words = timing.get("word_timestamps") or timing.get("words") or []
    report["synchronization_metadata"] = bool(words) or bool(timing.get("sentence_timestamps"))
    if not report["synchronization_metadata"]:
        report["warnings"].append("no_word_timestamps")
    report["caption_timing_compatible"] = report["non_zero_duration"]

    report["ok"] = not report["hard_fails"]
    return report


def _probe_duration(path: Path) -> float:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        # Fallback: mp3 rough from size @ 128kbps
        return max(0.0, path.stat().st_size * 8 / 128000)
    try:
        proc = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if proc.returncode != 0:
            return 0.0
        data = json.loads(proc.stdout or "{}")
        return float((data.get("format") or {}).get("duration") or 0)
    except Exception:  # noqa: BLE001
        return 0.0


def _has_audio_stream(path: Path) -> bool:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return path.suffix.lower() in {".mp3", ".wav", ".m4a", ".aac"}
    try:
        proc = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "a",
                "-show_entries",
                "stream=codec_type",
                "-of",
                "csv=p=0",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        return "audio" in (proc.stdout or "").lower() or proc.returncode == 0 and bool(proc.stdout.strip())
    except Exception:  # noqa: BLE001
        return False


def _probe_loudness(path: Path) -> dict[str, float | None]:
    """Return mean/max volume via ffmpeg volumedetect when available."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return {"mean_volume": None, "max_volume": None}
    try:
        proc = subprocess.run(
            [
                ffmpeg,
                "-i",
                str(path),
                "-af",
                "volumedetect",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        text = (proc.stderr or "") + (proc.stdout or "")
        mean = max_v = None
        for line in text.splitlines():
            if "mean_volume:" in line:
                try:
                    mean = float(line.split("mean_volume:")[1].split("dB")[0].strip())
                except ValueError:
                    pass
            if "max_volume:" in line:
                try:
                    max_v = float(line.split("max_volume:")[1].split("dB")[0].strip())
                except ValueError:
                    pass
        return {"mean_volume": mean, "max_volume": max_v}
    except Exception:  # noqa: BLE001
        return {"mean_volume": None, "max_volume": None}
