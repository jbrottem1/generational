"""Persist generated media bytes/URLs under data/media/."""

from __future__ import annotations

import base64
import hashlib
import re
import urllib.request
from pathlib import Path
from typing import Any

from core.log import get_logger

logger = get_logger(__name__)

ROOT = Path(__file__).resolve().parents[2]
MEDIA_ROOT = ROOT / "data" / "media"


def media_root() -> Path:
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    return MEDIA_ROOT


def _safe_slug(value: str, fallback: str = "asset") -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", (value or "").strip())[:80].strip("-")
    return slug or fallback


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def write_bytes(data: bytes, *, kind: str, name: str, ext: str) -> str:
    """Write bytes to data/media/{kind}/{name}.{ext}; return relative path."""
    folder = media_root() / _safe_slug(kind, "misc")
    folder.mkdir(parents=True, exist_ok=True)
    digest = content_hash(data)
    filename = f"{_safe_slug(name)}_{digest}.{ext.lstrip('.')}"
    path = folder / filename
    if not path.exists():
        path.write_bytes(data)
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write_b64(b64: str, *, kind: str, name: str, ext: str) -> str:
    if not b64:
        return ""
    raw = base64.b64decode(b64)
    return write_bytes(raw, kind=kind, name=name, ext=ext)


def download_url(url: str, *, kind: str, name: str, ext: str, timeout_sec: float = 60.0) -> str:
    if not url or url.startswith(("mock://", "runtime://")):
        return ""
    try:
        with urllib.request.urlopen(url, timeout=timeout_sec) as resp:
            data = resp.read()
        if not data:
            return ""
        return write_bytes(data, kind=kind, name=name, ext=ext)
    except Exception as exc:  # noqa: BLE001
        logger.warning("media.download_failed | url=%s error=%s", url[:120], exc)
        return ""


def persist_audio_payload(data: dict[str, Any], *, name: str = "voice") -> dict[str, Any]:
    """Ensure audio_b64 / audio_url become a local path when possible."""
    out = dict(data)
    path = str(out.get("path") or "")
    if path and not path.startswith(("mock://", "runtime://")) and Path(path).exists():
        out["path"] = path
        out["placeholder"] = False
        return out

    b64 = str(out.get("audio_b64") or "")
    fmt = str(out.get("format") or "mp3").lstrip(".")
    if b64:
        local = write_b64(b64, kind="voice", name=name, ext=fmt)
        if local:
            out["path"] = local
            out["placeholder"] = False
            return out

    url = str(out.get("audio_url") or out.get("uri") or "")
    if url:
        local = download_url(url, kind="voice", name=name, ext=fmt)
        if local:
            out["path"] = local
            out["audio_url"] = url
            out["placeholder"] = False
            return out

    # Local-first recovery when TTS providers return no bytes (quota / demo).
    local = _synthesize_local_fallback_audio(
        text=str(out.get("text") or out.get("plain_text") or ""),
        duration_sec=float(out.get("duration_sec") or 0),
        name=name,
    )
    if local:
        out["path"] = local
        out["format"] = "mp3"
        out["provider"] = out.get("provider") or "local_tts_fallback"
        out["local_fallback"] = True
    return out


def _synthesize_local_fallback_audio(*, text: str, duration_sec: float, name: str) -> str:
    """macOS `say` → mp3, else ffmpeg tone sized to narration duration."""
    import shutil
    import subprocess
    import tempfile

    words = max(1, len((text or "").split()))
    duration = float(duration_sec) if duration_sec and duration_sec > 0 else round(words / 2.5, 2)
    duration = max(2.0, min(duration, 90.0))
    ffmpeg = shutil.which("ffmpeg")
    folder = media_root() / "voice"
    folder.mkdir(parents=True, exist_ok=True)
    digest = content_hash((text or f"silence:{duration}").encode("utf-8"))
    out = folder / f"{_safe_slug(name)}_{digest}_local.mp3"
    if out.exists() and out.stat().st_size > 200:
        try:
            return str(out.relative_to(ROOT))
        except ValueError:
            return str(out)

    try:
        say = shutil.which("say")
        if say and (text or "").strip():
            with tempfile.TemporaryDirectory() as tmp:
                aiff = Path(tmp) / "narration.aiff"
                proc = subprocess.run(
                    [say, "-o", str(aiff), text.strip()[:2500]],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )
                if proc.returncode == 0 and aiff.exists() and ffmpeg:
                    enc = subprocess.run(
                        [ffmpeg, "-y", "-i", str(aiff), "-codec:a", "libmp3lame", "-q:a", "4", str(out)],
                        capture_output=True,
                        text=True,
                        timeout=120,
                        check=False,
                    )
                    if enc.returncode == 0 and out.exists() and out.stat().st_size > 200:
                        try:
                            return str(out.relative_to(ROOT))
                        except ValueError:
                            return str(out)
        if ffmpeg:
            enc = subprocess.run(
                [
                    ffmpeg, "-y",
                    "-f", "lavfi",
                    "-i", f"sine=frequency=180:duration={duration}",
                    "-af", "volume=0.15",
                    "-codec:a", "libmp3lame",
                    "-q:a", "6",
                    str(out),
                ],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            if enc.returncode == 0 and out.exists() and out.stat().st_size > 200:
                try:
                    return str(out.relative_to(ROOT))
                except ValueError:
                    return str(out)
    except Exception as exc:  # noqa: BLE001
        logger.warning("media.local_tts_fallback_failed | error=%s", exc)
    return ""


def persist_image_payload(data: dict[str, Any], *, name: str = "image") -> dict[str, Any]:
    out = dict(data)
    b64 = str(out.get("b64_json") or out.get("image_b64") or "")
    if b64:
        local = write_b64(b64, kind="images", name=name, ext="png")
        if local:
            out["path"] = local
            out["uri"] = local
            out["placeholder"] = False
            out["status"] = "generated"
            return out
    url = str(out.get("image_url") or out.get("uri") or out.get("path") or "")
    if url and not url.startswith(("mock://", "runtime://")):
        local = download_url(url, kind="images", name=name, ext="png")
        if local:
            out["path"] = local
            out["uri"] = local
            out["image_url"] = url
            out["placeholder"] = False
            out["status"] = "generated"
            return out
        if Path(url).exists():
            out["path"] = url
            out["placeholder"] = False
            out["status"] = "generated"
    return out


def persist_video_payload(data: dict[str, Any], *, name: str = "video") -> dict[str, Any]:
    out = dict(data)
    url = str(out.get("video_url") or out.get("uri") or out.get("path") or "")
    if url and not url.startswith(("mock://", "runtime://")):
        local = download_url(url, kind="video", name=name, ext="mp4")
        if local:
            out["path"] = local
            out["uri"] = local
            out["placeholder"] = False
            out["status"] = "generated"
            out["async"] = False
            return out
        if Path(url).exists():
            out["path"] = url
            out["placeholder"] = False
            out["status"] = "generated"
    return out


def absolute_media_path(path: str) -> Path | None:
    if not path or path.startswith(("mock://", "runtime://", "http://", "https://")):
        return None
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = ROOT / path
    return candidate if candidate.exists() else None
