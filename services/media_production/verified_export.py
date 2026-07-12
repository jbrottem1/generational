"""Verified local export — SUCCESS only after physical Desktop MP4 proof."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.media_production.execution_mode import (
    canonical_export_dir,
    get_execution_context,
    local_success_requires_verified_export,
)
from services.media_production.ffmpeg_assembler import find_ffmpeg


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
        return {
            "ok": path.stat().st_size > 0 and "Video:" in text and "Audio:" in text,
            "bytes": path.stat().st_size,
            "has_video": "Video:" in text,
            "has_audio": "Audio:" in text,
            "duration_sec": duration,
            "width": int(res_match.group(1)) if res_match else None,
            "height": int(res_match.group(2)) if res_match else None,
            "video_codec": "h264" if "h264" in text else None,
            "audio_codec": "aac" if "aac" in text else None,
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
        return {"ok": False, "error": proc.stderr[-300:]}
    meta = json.loads(proc.stdout or "{}")
    streams = meta.get("streams") or []
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    fmt = meta.get("format") or {}
    duration = float(fmt.get("duration") or 0)
    return {
        "ok": path.stat().st_size > 0 and video is not None and audio is not None,
        "bytes": path.stat().st_size,
        "has_video": video is not None,
        "has_audio": audio is not None,
        "duration_sec": round(duration, 3),
        "width": video.get("width") if video else None,
        "height": video.get("height") if video else None,
        "video_codec": video.get("codec_name") if video else None,
        "audio_codec": audio.get("codec_name") if audio else None,
    }


def verify_canonical_export(path: Path) -> dict[str, Any]:
    """Strict verification checklist from LOCAL-FIRST policy."""
    probe = ffprobe_mp4(path)
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
    }
    passed = all(checks.values())
    return {
        "ok": passed,
        "checks": checks,
        "probe": probe,
        "path": str(path.resolve()),
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }


def export_verified_mp4(source: Path, *, filename: str) -> dict[str, Any]:
    """Copy source to canonical Desktop export after verification."""
    ctx = get_execution_context()
    if not ctx.can_render_media:
        return {
            "ok": False,
            "status": "awaiting_local_render",
            "message": "Cloud runtime cannot claim local Desktop export.",
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
