"""FFmpeg-based final assembly — stills + narration → MP4.

Uses system ``ffmpeg`` when present, otherwise the binary bundled by
``imageio-ffmpeg`` (optional dependency). Falls back cleanly when neither
is available so MockRenderer can keep the dry-run contract.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from core.log import get_logger
from services.media_production.formats import resolve_output_format
from services.media_production.persistence import absolute_media_path, media_root

logger = get_logger(__name__)

ROOT = Path(__file__).resolve().parents[2]


def find_ffmpeg() -> str:
    """Return path to an ffmpeg binary, or empty string."""
    which = shutil.which("ffmpeg")
    if which:
        return which
    try:
        import imageio_ffmpeg  # type: ignore

        return str(imageio_ffmpeg.get_ffmpeg_exe() or "")
    except Exception:  # noqa: BLE001
        return ""


def ffmpeg_available() -> bool:
    return bool(find_ffmpeg())


def _abs(path: str) -> Path | None:
    return absolute_media_path(path)


def _collect_visuals(scene_render_plan: list) -> list[Path]:
    visuals: list[Path] = []
    for scene in scene_render_plan or []:
        asset = (
            scene.get("resolved_asset")
            or scene.get("asset")
            or scene.get("visual")
            or {}
        )
        if not isinstance(asset, dict):
            asset = {}
        for key in ("path", "uri", "local_path", "image_path", "video_path"):
            candidate = _abs(str(asset.get(key) or scene.get(key) or ""))
            if candidate and candidate.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov"}:
                visuals.append(candidate)
                break
    return visuals


def _collect_audio(audio_mix_plan: dict, scene_render_plan: list) -> Path | None:
    tracks = (audio_mix_plan or {}).get("tracks") or {}
    narration = tracks.get("narration") or {}
    for seg in narration.get("segments") or []:
        candidate = _abs(str(seg.get("path") or seg.get("uri") or ""))
        if candidate:
            return candidate
    for scene in scene_render_plan or []:
        for key in ("narration_path", "audio_path", "path"):
            if "audio" in key or key == "narration_path":
                candidate = _abs(str(scene.get(key) or ""))
                if candidate and candidate.suffix.lower() in {".mp3", ".wav", ".m4a", ".aac"}:
                    return candidate
    return None


def assemble_mp4(
    *,
    title: str,
    output_path: str,
    timeline: dict,
    scene_render_plan: list,
    audio_mix_plan: dict,
    output_format: dict | None = None,
    timeout_sec: float = 600.0,
) -> dict[str, Any]:
    """Assemble a real MP4 when ffmpeg + assets exist; otherwise report why not."""
    ffmpeg = find_ffmpeg()
    fmt = resolve_output_format(
        aspect=str((output_format or {}).get("aspect_ratio") or "vertical"),
        width=int(((output_format or {}).get("resolution") or {}).get("width") or 0),
        height=int(((output_format or {}).get("resolution") or {}).get("height") or 0),
        fps=int((output_format or {}).get("fps") or 30),
    )
    width = int(fmt["resolution"]["width"])
    height = int(fmt["resolution"]["height"])
    fps = int(fmt["fps"])
    duration = float((timeline or {}).get("total_duration_sec") or 0) or 5.0

    out = Path(output_path)
    if not out.is_absolute():
        out = ROOT / output_path
    out.parent.mkdir(parents=True, exist_ok=True)

    if not ffmpeg:
        return {
            "ok": False,
            "mock": True,
            "error": "ffmpeg not available — install ffmpeg or pip install imageio-ffmpeg",
            "output_path": str(output_path),
            "log": [],
        }

    visuals = _collect_visuals(scene_render_plan)
    audio = _collect_audio(audio_mix_plan, scene_render_plan)
    log: list[str] = []

    # Prefer first still/video; fall back to solid color background.
    cmd: list[str]
    if visuals:
        first = visuals[0]
        if first.suffix.lower() in {".mp4", ".mov"}:
            cmd = [
                ffmpeg, "-y",
                "-i", str(first),
            ]
            if audio:
                cmd += ["-i", str(audio)]
            cmd += [
                "-t", str(duration),
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                       f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps={fps}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
            ]
            if audio:
                cmd += ["-c:a", "aac", "-shortest"]
            else:
                cmd += ["-an"]
            cmd.append(str(out))
            log.append(f"video_clip→mp4 source={first.name}")
        else:
            # Ken Burns-ish slow zoom on still
            frames = max(1, int(duration * fps))
            cmd = [
                ffmpeg, "-y",
                "-loop", "1",
                "-i", str(first),
            ]
            if audio:
                cmd += ["-i", str(audio)]
            cmd += [
                "-vf",
                f"scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height},"
                f"zoompan=z='min(zoom+0.0004,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d={frames}:s={width}x{height}:fps={fps}",
                "-t", str(duration),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
            ]
            if audio:
                cmd += ["-c:a", "aac", "-shortest"]
            else:
                cmd += ["-an"]
            cmd.append(str(out))
            log.append(f"still→mp4 kenburns source={first.name} scenes={len(visuals)}")
    else:
        # Color bed + optional narration (still a real playable MP4)
        cmd = [
            ffmpeg, "-y",
            "-f", "lavfi",
            "-i", f"color=c=0x101820:s={width}x{height}:d={duration}:r={fps}",
        ]
        if audio:
            cmd += ["-i", str(audio), "-c:a", "aac", "-shortest"]
        else:
            cmd += ["-an"]
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)]
        log.append("color_bed→mp4 (no visual assets resolved)")

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
        log.append(f"ffmpeg_exit={proc.returncode}")
        if proc.returncode != 0 or not out.exists() or out.stat().st_size < 100:
            err = (proc.stderr or proc.stdout or "ffmpeg failed")[-800:]
            return {
                "ok": False,
                "mock": True,
                "error": err,
                "output_path": str(output_path),
                "log": log,
                "command": cmd,
            }
        rel = str(out.relative_to(ROOT)) if out.is_relative_to(ROOT) else str(out)
        return {
            "ok": True,
            "mock": False,
            "error": "",
            "output_path": rel,
            "absolute_path": str(out),
            "bytes": out.stat().st_size,
            "duration_sec": duration,
            "resolution": f"{width}x{height}",
            "ffmpeg": ffmpeg,
            "log": log,
            "visual_count": len(visuals),
            "has_audio": bool(audio),
            "manifest": {
                "title": title,
                "format": fmt,
                "visuals": [str(v) for v in visuals[:20]],
                "audio": str(audio) if audio else "",
            },
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "mock": True,
            "error": f"ffmpeg timed out after {timeout_sec}s",
            "output_path": str(output_path),
            "log": log,
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("ffmpeg.assemble_failed")
        return {
            "ok": False,
            "mock": True,
            "error": str(exc),
            "output_path": str(output_path),
            "log": log,
        }


def write_assembly_sidecar(result: dict[str, Any], output_path: str) -> str:
    """Write a JSON sidecar next to the MP4 for analytics / QC."""
    out = Path(output_path)
    if not out.is_absolute():
        out = ROOT / output_path
    side = out.with_suffix(".assembly.json")
    side.parent.mkdir(parents=True, exist_ok=True)
    side.write_text(json.dumps(result, indent=2), encoding="utf-8")
    try:
        return str(side.relative_to(ROOT))
    except ValueError:
        return str(side)
