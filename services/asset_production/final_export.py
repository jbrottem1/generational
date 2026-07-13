"""Ready-to-post MP4 export — Desktop destination only (final file)."""

from __future__ import annotations

import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from core.log import get_logger

logger = get_logger(__name__)

FINAL_EXPORT_DIR = (
    Path.home()
    / "Desktop"
    / "AI Start-up"
    / "videos"
    / "test run generational"
)

_INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
_WHITESPACE = re.compile(r"\s+")


def final_export_dir() -> Path:
    """Return the ready-to-post folder, creating it if needed."""
    FINAL_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    return FINAL_EXPORT_DIR


def sanitize_title(title: str) -> str:
    """Sanitize a project title for use in a filename."""
    text = str(title or "Untitled").strip() or "Untitled"
    text = _INVALID_FILENAME.sub("", text)
    text = text.replace(" ", "_")
    text = re.sub(r"_+", "_", text).strip("._")
    return (text or "Untitled")[:80]


def unique_export_path(directory: Path, stem: str, *, ext: str = ".mp4") -> Path:
    """Never overwrite — add _v2, _v3, … when the name already exists."""
    candidate = directory / f"{stem}{ext}"
    if not candidate.exists():
        return candidate
    version = 2
    while True:
        candidate = directory / f"{stem}_v{version}{ext}"
        if not candidate.exists():
            return candidate
        version += 1


def build_export_filename(title: str, *, when: datetime | None = None) -> str:
    stamp = (when or datetime.now()).strftime("%Y-%m-%d_%H-%M-%S")
    return f"{stamp}_{sanitize_title(title)}"


def _parse_duration_sec(ffmpeg_stderr: str) -> float:
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", ffmpeg_stderr or "")
    if not match:
        return 0.0
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def verify_ready_to_post_mp4(
    mp4_path: str | Path,
    *,
    render_package: dict | None = None,
    qc_passed: bool = False,
    min_duration_sec: float = 0.5,
    min_bytes: int = 500,
) -> dict[str, Any]:
    """Confirm the MP4 is playable, has video + audio, and is ready to post."""
    render = render_package or {}
    path = Path(mp4_path)
    errors: list[str] = []

    if not qc_passed:
        errors.append("Quality control did not pass")
    if render.get("mock"):
        errors.append("Render is marked mock")
    if not path.is_file():
        errors.append(f"MP4 missing: {path}")
        return {"ok": False, "errors": errors, "path": str(path)}

    size = path.stat().st_size
    if size < min_bytes:
        errors.append(f"MP4 too small ({size} bytes)")

    from services.media_production.ffmpeg_assembler import find_ffmpeg

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        errors.append("ffmpeg unavailable — cannot verify playability")
        return {"ok": False, "errors": errors, "path": str(path), "bytes": size}

    proc = subprocess.run(
        [ffmpeg, "-i", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    probe = (proc.stderr or "") + (proc.stdout or "")
    has_video = "Video:" in probe
    has_audio = "Audio:" in probe
    duration = _parse_duration_sec(probe)
    if not has_video:
        errors.append("No video stream detected")
    if not has_audio:
        errors.append("No audio stream detected")
    if duration < min_duration_sec:
        errors.append(f"Invalid duration ({duration}s)")

    return {
        "ok": not errors,
        "errors": errors,
        "path": str(path),
        "bytes": size,
        "has_video": has_video,
        "has_audio": has_audio,
        "duration_sec": duration,
    }


def export_ready_to_post_mp4(
    source_mp4: str | Path,
    *,
    title: str,
    qc_passed: bool,
    render_package: dict | None = None,
    when: datetime | None = None,
) -> dict[str, Any]:
    """Copy a verified ready-to-post MP4 into the Desktop export folder.

    Only the final MP4 is written — no intermediate production files.
    """
    verification = verify_ready_to_post_mp4(
        source_mp4,
        render_package=render_package,
        qc_passed=qc_passed,
    )
    if not verification.get("ok"):
        return {
            "ok": False,
            "error": "; ".join(verification.get("errors") or ["verification failed"]),
            "verification": verification,
            "final_export_path": "",
            "final_export_dir": str(FINAL_EXPORT_DIR),
        }

    dest_dir = final_export_dir()
    stem = build_export_filename(title, when=when)
    dest = unique_export_path(dest_dir, stem)
    shutil.copy2(str(source_mp4), str(dest))

    logger.info(
        "final_export.saved | title=%s dest=%s bytes=%s",
        title,
        dest,
        dest.stat().st_size,
    )
    return {
        "ok": True,
        "final_export_path": str(dest),
        "final_export_dir": str(dest_dir),
        "bytes": dest.stat().st_size,
        "verification": verification,
        "message": "Ready-to-post video saved successfully.",
    }


def reveal_in_finder(path: str | Path) -> bool:
    target = Path(path)
    if not target.exists():
        return False
    subprocess.run(["open", "-R", str(target)], check=False)
    return True


def open_export_folder() -> bool:
    folder = final_export_dir()
    subprocess.run(["open", str(folder)], check=False)
    return True
