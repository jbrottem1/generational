"""Verified local export — SUCCESS only after physical Desktop MP4 proof."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.media_production.execution_mode import (
    canonical_export_dir,
    get_execution_context,
    local_success_requires_verified_export,
)
from services.media_production.ffmpeg_assembler import find_ffmpeg

# Below this average bitrate (bits/sec), treat as truncated / incomplete — not a soft small file.
IMPLAUSIBLE_BITRATE_BPS = 40_000
# Absolute floor for zero/near-zero garbage files (not a general size gate).
NEAR_EMPTY_BYTES = 2_048
def unique_export_path(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem, ext = Path(filename).stem, Path(filename).suffix
    version = 2
    while True:
        candidate = directory / f"{stem}_v{version}{ext}"
        if not candidate.exists():
            return candidate
        version += 1


def wait_for_file(path: Path, *, timeout_sec: float = 5.0, poll_sec: float = 0.05) -> bool:
    """Wait until path exists and size is stable (copy finished)."""
    deadline = time.time() + timeout_sec
    last_size = -1
    stable = 0
    while time.time() < deadline:
        if path.is_file():
            size = path.stat().st_size
            if size > 0 and size == last_size:
                stable += 1
                if stable >= 2:
                    return True
            else:
                stable = 0
            last_size = size
        time.sleep(poll_sec)
    return path.is_file() and path.stat().st_size > 0


def _parse_frame_rate(value: Any) -> float | None:
    text = str(value or "")
    if not text or text == "0/0":
        return None
    if "/" in text:
        num, den = text.split("/", 1)
        try:
            den_f = float(den)
            return float(num) / den_f if den_f else None
        except ValueError:
            return None
    try:
        return float(text)
    except ValueError:
        return None


def ffprobe_mp4(path: Path) -> dict[str, Any]:
    ffmpeg = find_ffmpeg()
    if not ffmpeg or not path.is_file():
        return {"ok": False, "error": "missing ffmpeg or file"}

    ffprobe = ffmpeg.replace("ffmpeg", "ffprobe")
    if not Path(ffprobe).is_file():
        # fallback parse via ffmpeg -i
        proc = subprocess.run(
            [ffmpeg, "-i", str(path), "-hide_banner"],
            capture_output=True,
            text=True,
            check=False,
        )
        text = (proc.stderr or "") + (proc.stdout or "")
        dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
        duration = 0.0
        if dur_match:
            h, m, s = dur_match.groups()
            duration = int(h) * 3600 + int(m) * 60 + float(s)
        res_match = re.search(r"(\d{3,4})x(\d{3,4})", text)
        size = path.stat().st_size
        bitrate = int((size * 8) / duration) if duration > 0 else 0
        return {
            "ok": size > 0 and "Video:" in text and "Audio:" in text,
            "bytes": size,
            "has_video": "Video:" in text,
            "has_audio": "Audio:" in text,
            "duration_sec": duration,
            "width": int(res_match.group(1)) if res_match else None,
            "height": int(res_match.group(2)) if res_match else None,
            "video_codec": "h264" if "h264" in text else None,
            "audio_codec": "aac" if "aac" in text else None,
            "bit_rate": bitrate,
            "fps": None,
            "absolute_path": str(path.resolve()),
        }

    proc = subprocess.run(
        [
            ffprobe,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return {"ok": False, "error": proc.stderr[-300:], "absolute_path": str(path.resolve())}
    meta = json.loads(proc.stdout or "{}")
    streams = meta.get("streams") or []
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    fmt = meta.get("format") or {}
    duration = float(fmt.get("duration") or 0)
    size = path.stat().st_size
    bit_rate = int(float(fmt.get("bit_rate") or 0))
    if bit_rate <= 0 and duration > 0:
        bit_rate = int((size * 8) / duration)
    fps = _parse_frame_rate(video.get("r_frame_rate") if video else None)
    return {
        "ok": size > 0 and video is not None and audio is not None and duration > 0,
        "bytes": size,
        "has_video": video is not None,
        "has_audio": audio is not None,
        "duration_sec": round(duration, 3),
        "width": video.get("width") if video else None,
        "height": video.get("height") if video else None,
        "video_codec": video.get("codec_name") if video else None,
        "audio_codec": audio.get("codec_name") if audio else None,
        "bit_rate": bit_rate,
        "fps": fps,
        "absolute_path": str(path.resolve()),
    }


def assess_export_technical_validity(
    path: Path,
    *,
    probe: dict[str, Any] | None = None,
    expected_duration_sec: float | None = None,
    require_audio: bool = True,
) -> dict[str, Any]:
    """Context-aware technical validity — not a raw file-size threshold.

    Hard-fails only for truncated / corrupt / incomplete evidence.
    Small short-form educational MP4s are allowed when streams and bitrate are sane.
    """
    path = Path(path)
    hard_fails: list[str] = []
    warnings: list[str] = []
    probe = probe or (ffprobe_mp4(path) if path.is_file() else {"ok": False})

    if not path.is_file():
        hard_fails.append("export_missing")
        return {"ok": False, "hard_fails": hard_fails, "warnings": warnings, "probe": probe, "is_placeholder": False}

    size = int(probe.get("bytes") or path.stat().st_size)
    duration = float(probe.get("duration_sec") or 0)
    bitrate = int(probe.get("bit_rate") or 0)
    if bitrate <= 0 and duration > 0:
        bitrate = int((size * 8) / duration)

    if size <= 0:
        hard_fails.append("export_zero_bytes")
    elif size < NEAR_EMPTY_BYTES:
        hard_fails.append("export_truncated")

    if not probe.get("has_video"):
        hard_fails.append("missing_video")
    if require_audio and not probe.get("has_audio"):
        hard_fails.append("missing_audio")
    if duration <= 0.5:
        hard_fails.append("invalid_duration")
    if not (probe.get("width") and probe.get("height")):
        hard_fails.append("invalid_resolution")

    if duration > 0 and bitrate > 0 and bitrate < IMPLAUSIBLE_BITRATE_BPS:
        hard_fails.append("implausible_bitrate")

    if expected_duration_sec is not None and duration > 0:
        expected = float(expected_duration_sec)
        if expected > 1.0 and abs(duration - expected) > max(2.0, expected * 0.35):
            hard_fails.append("duration_mismatch")

    # Cloud agent paths must never be treated as local Desktop success
    resolved = str(path.resolve())
    if "/home/ubuntu/" in resolved or resolved.startswith("/workspace/"):
        hard_fails.append("stale_cloud_path")

    is_placeholder = False
    try:
        head = path.read_bytes()[:64]
        # Extremely small or non-ISO BMFF headers are suspicious
        if size < NEAR_EMPTY_BYTES or (b"ftyp" not in head and size < 10_000):
            is_placeholder = True
            if "export_truncated" not in hard_fails and size < NEAR_EMPTY_BYTES:
                hard_fails.append("incomplete_ffmpeg_output")
    except OSError:
        hard_fails.append("export_path_inaccessible")

    # Soft note: short videos may be modest in bytes — never hard-fail solely on size
    if size < 50_000 and duration > 0 and bitrate >= IMPLAUSIBLE_BITRATE_BPS and not hard_fails:
        warnings.append("small_file_size_context_ok")

    return {
        "ok": not hard_fails,
        "hard_fails": hard_fails,
        "warnings": warnings,
        "probe": probe,
        "is_placeholder": is_placeholder,
        "bit_rate": bitrate,
        "bytes": size,
        "duration_sec": duration,
    }


def verify_canonical_export(path: Path) -> dict[str, Any]:
    """Strict verification checklist from LOCAL-FIRST policy."""
    probe = ffprobe_mp4(path)
    tech = assess_export_technical_validity(path, probe=probe)
    checks = {
        "file_exists": path.is_file(),
        "size_gt_zero": path.is_file() and path.stat().st_size > 0,
        "video_stream": bool(probe.get("has_video")),
        "audio_stream": bool(probe.get("has_audio")),
        "playable": bool(probe.get("ok")),
        "duration": float(probe.get("duration_sec") or 0) > 0.5,
        "resolution": bool(probe.get("width") and probe.get("height")),
        "under_canonical_dir": str(path.resolve()).startswith(str(canonical_export_dir().resolve())),
        "local_execution": get_execution_context().can_claim_export_success,
        "technical_valid": bool(tech.get("ok")),
    }
    passed = all(checks.values())
    return {
        "ok": passed,
        "checks": checks,
        "probe": probe,
        "technical": tech,
        "path": str(path.resolve()),
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }


def export_verified_mp4(source: Path, *, filename: str) -> dict[str, Any]:
    """Copy source to canonical Desktop export after verification."""
    ctx = get_execution_context()
    if not ctx.can_claim_export_success:
        return {
            "ok": False,
            "status": "export_root_unreachable",
            "message": "Desktop media library is unreachable. Expected ~/Desktop/AI Start-Up/Videos/.",
        }

    dest_dir = canonical_export_dir(create=True)
    dest = unique_export_path(dest_dir, filename)
    if not source.is_file():
        return {"ok": False, "error": f"source missing: {source}"}
    shutil.copy2(source, dest)
    verification = verify_canonical_export(dest)
    success = verification["ok"] and local_success_requires_verified_export(dest)
    return {
        "ok": success,
        "status": "export_verified" if success else "verification_failed",
        "export_path": str(dest),
        "verification": verification,
    }


def reveal_export_in_finder(path: Path) -> bool:
    if not Path(path).exists():
        return False
    try:
        subprocess.run(["open", "-R", str(path)], check=False)
        return True
    except Exception:  # noqa: BLE001
        return False
