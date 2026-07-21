"""FFmpeg-based final assembly — multi-scene cinematic stills + narration → MP4.

Uses system ``ffmpeg`` when present, otherwise the binary bundled by
``imageio-ffmpeg``. Assembles ALL resolved scene visuals with per-scene
motion (Ken Burns / zoom / pan). Color beds are rejected for production
quality — callers must supply real visuals.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from core.log import get_logger
from services.media_production.formats import resolve_output_format
from services.media_production.persistence import absolute_media_path

logger = get_logger(__name__)

ROOT = Path(__file__).resolve().parents[2]

_STILL_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
_VIDEO_EXTS = {".mp4", ".mov", ".webm"}


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


def _collect_scene_visuals(scene_render_plan: list) -> list[dict[str, Any]]:
    """Return ordered list of {path, duration_sec, effect, scene_id} for real files only."""
    items: list[dict[str, Any]] = []
    for scene in scene_render_plan or []:
        if not isinstance(scene, dict):
            continue
        asset = (
            scene.get("resolved_asset")
            or scene.get("asset")
            or scene.get("visual")
            or {}
        )
        if not isinstance(asset, dict):
            asset = {}
        candidate = None
        for key in (
            "path",
            "uri",
            "local_path",
            "image_path",
            "video_path",
            "approved_asset_path",
            "image",
        ):
            raw = str(asset.get(key) or scene.get(key) or "")
            if not raw or raw.startswith(("mock://", "runtime://")):
                continue
            candidate = _abs(raw)
            if candidate and candidate.suffix.lower() in (_STILL_EXTS | _VIDEO_EXTS):
                # Prefer real files even when provider incorrectly left placeholder=True
                break
            candidate = None
        if not candidate:
            continue
        effect = scene.get("effect") or {}
        if isinstance(effect, str):
            effect = {"effect": effect}
        duration = float(
            scene.get("duration_sec")
            or scene.get("length_sec")
            or (effect.get("duration_sec") if isinstance(effect, dict) else 0)
            or 3.0
        )
        items.append(
            {
                "path": candidate,
                "duration_sec": max(0.8, duration),
                "effect": effect if isinstance(effect, dict) else {},
                "scene_id": scene.get("scene_id") or scene.get("scene_number") or len(items) + 1,
            }
        )
    return items


def _collect_audio(audio_mix_plan: dict, scene_render_plan: list) -> Path | None:
    tracks = (audio_mix_plan or {}).get("tracks") or {}
    narration = tracks.get("narration") or {}
    for seg in narration.get("segments") or []:
        candidate = _abs(str(seg.get("path") or seg.get("uri") or ""))
        if candidate:
            return candidate
    for scene in scene_render_plan or []:
        for key in ("narration_path", "audio_path"):
            candidate = _abs(str(scene.get(key) or ""))
            if candidate and candidate.suffix.lower() in {".mp3", ".wav", ".m4a", ".aac"}:
                return candidate
    return None


def _zoompan_filter(effect: dict, *, width: int, height: int, frames: int, fps: int) -> str:
    """Build a zoompan expression from MotionPlanner-style effect dict."""
    name = str(effect.get("effect") or "cinematic_push_in").lower()
    if name in {"", "static", "none", "ken_burns"}:
        # Ken Burns is legacy slideshow default — prefer cinematic push unless forced
        if name == "ken_burns" and effect.get("force_ken_burns"):
            pass
        else:
            name = "cinematic_push_in"
            effect = {**effect, "effect": name}
    zoom = effect.get("zoom") if isinstance(effect.get("zoom"), dict) else {}
    z0 = float(zoom.get("start_scale") or 1.0)
    # V2 quality: stronger default drift so stills never read as slideshow
    z1 = float(zoom.get("end_scale") or 1.12)
    pan = effect.get("pan") if isinstance(effect.get("pan"), dict) else {}
    direction = str(pan.get("direction") or "none")
    amount = float(pan.get("amount_pct") or 10.0) / 100.0

    # zoom progresses across frames
    if abs(z1 - z0) < 0.001 and name not in ("pan_left", "pan_right", "whip_pan"):
        z1 = z0 + 0.10  # never fully static

    z_expr = f"'{z0}+({z1}-{z0})*on/{max(frames - 1, 1)}'"

    if direction == "left" or name in ("pan_left",):
        x_expr = f"'iw/2-(iw/zoom/2)-({amount}*iw)*on/{max(frames - 1, 1)}'"
        y_expr = "'ih/2-(ih/zoom/2)'"
    elif direction == "right" or name in ("pan_right", "whip_pan"):
        x_expr = f"'iw/2-(iw/zoom/2)+({amount}*iw)*on/{max(frames - 1, 1)}'"
        y_expr = "'ih/2-(ih/zoom/2)'"
    else:
        # Classic Ken Burns diagonal drift
        x_expr = f"'iw/2-(iw/zoom/2)+({amount * 0.5}*iw)*on/{max(frames - 1, 1)}'"
        y_expr = f"'ih/2-(ih/zoom/2)-({amount * 0.35}*ih)*on/{max(frames - 1, 1)}'"

    return (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"zoompan=z={z_expr}:x={x_expr}:y={y_expr}:d={frames}:s={width}x{height}:fps={fps}"
    )


def _render_scene_clip(
    ffmpeg: str,
    item: dict[str, Any],
    *,
    width: int,
    height: int,
    fps: int,
    out_path: Path,
    timeout_sec: float,
) -> tuple[bool, str]:
    path: Path = item["path"]
    duration = float(item["duration_sec"])
    frames = max(1, int(duration * fps))
    effect = item.get("effect") or {}

    if path.suffix.lower() in _VIDEO_EXTS:
        cmd = [
            ffmpeg, "-y",
            "-i", str(path),
            "-t", str(duration),
            "-vf",
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps={fps}",
            "-an",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(out_path),
        ]
    else:
        vf = _zoompan_filter(effect, width=width, height=height, frames=frames, fps=fps)
        cmd = [
            ffmpeg, "-y",
            "-loop", "1",
            "-i", str(path),
            "-vf", vf,
            "-t", str(duration),
            "-an",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(out_path),
        ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec, check=False)
    if proc.returncode != 0 or not out_path.exists() or out_path.stat().st_size < 100:
        return False, (proc.stderr or proc.stdout or "scene clip failed")[-500:]
    return True, f"scene→clip {path.name} effect={effect.get('effect') or 'cinematic_push_in'} d={duration:.2f}s"


def assemble_mp4(
    *,
    title: str,
    output_path: str,
    timeline: dict,
    scene_render_plan: list,
    audio_mix_plan: dict,
    output_format: dict | None = None,
    timeout_sec: float = 600.0,
    allow_color_bed: bool = False,
) -> dict[str, Any]:
    """Assemble a real multi-scene MP4 when ffmpeg + assets exist."""
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
            "visual_count": 0,
        }

    visuals = _collect_scene_visuals(scene_render_plan)
    audio = _collect_audio(audio_mix_plan, scene_render_plan)
    log: list[str] = []

    if not visuals:
        if not allow_color_bed:
            return {
                "ok": False,
                "mock": True,
                "error": "No resolved visual assets — refusing color-bed render",
                "output_path": str(output_path),
                "log": ["rejected_color_bed"],
                "visual_count": 0,
            }
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
        return _run_ffmpeg(cmd, out, output_path, duration, width, height, fps, ffmpeg, log, visuals, audio, timeout_sec)

    # Distribute timeline duration across scenes proportionally
    total_weight = sum(float(v["duration_sec"]) for v in visuals) or 1.0
    for item in visuals:
        item["duration_sec"] = max(0.8, duration * (float(item["duration_sec"]) / total_weight))

    with tempfile.TemporaryDirectory(prefix="gen_assemble_") as tmp:
        tmp_dir = Path(tmp)
        clip_paths: list[Path] = []
        for index, item in enumerate(visuals):
            clip = tmp_dir / f"scene_{index:02d}.mp4"
            ok, msg = _render_scene_clip(
                ffmpeg, item, width=width, height=height, fps=fps, out_path=clip, timeout_sec=timeout_sec
            )
            log.append(msg)
            if not ok:
                # Skip broken scene but continue if others work
                logger.warning("ffmpeg.scene_clip_failed | %s", msg)
                continue
            clip_paths.append(clip)

        if not clip_paths:
            return {
                "ok": False,
                "mock": True,
                "error": "All scene clips failed to render",
                "output_path": str(output_path),
                "log": log,
                "visual_count": 0,
            }

        if len(clip_paths) == 1:
            # Single scene — mux audio
            cmd = [ffmpeg, "-y", "-i", str(clip_paths[0])]
            if audio:
                cmd += ["-i", str(audio), "-c:v", "copy", "-c:a", "aac", "-shortest"]
            else:
                cmd += ["-c:v", "copy", "-an"]
            cmd.append(str(out))
            log.append(f"single_scene→mp4 scenes=1 source={visuals[0]['path'].name}")
            return _run_ffmpeg(cmd, out, output_path, duration, width, height, fps, ffmpeg, log, visuals, audio, timeout_sec)

        # Concat demuxer
        list_file = tmp_dir / "concat.txt"
        list_file.write_text(
            "".join(f"file '{p.as_posix()}'\n" for p in clip_paths),
            encoding="utf-8",
        )
        concat_out = tmp_dir / "concat.mp4"
        concat_cmd = [
            ffmpeg, "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-an",
            str(concat_out),
        ]
        proc = subprocess.run(concat_cmd, capture_output=True, text=True, timeout=timeout_sec, check=False)
        log.append(f"concat_exit={proc.returncode} scenes={len(clip_paths)}")
        if proc.returncode != 0 or not concat_out.exists():
            err = (proc.stderr or proc.stdout or "concat failed")[-800:]
            return {
                "ok": False,
                "mock": True,
                "error": err,
                "output_path": str(output_path),
                "log": log,
                "visual_count": len(visuals),
            }

        cmd = [ffmpeg, "-y", "-i", str(concat_out)]
        if audio:
            cmd += ["-i", str(audio), "-c:v", "copy", "-c:a", "aac", "-shortest"]
        else:
            cmd += ["-c:v", "copy", "-an"]
        cmd.append(str(out))
        log.append(f"multi_scene→mp4 scenes={len(clip_paths)} visuals={len(visuals)}")
        return _run_ffmpeg(cmd, out, output_path, duration, width, height, fps, ffmpeg, log, visuals, audio, timeout_sec)


def _run_ffmpeg(
    cmd: list[str],
    out: Path,
    output_path: str,
    duration: float,
    width: int,
    height: int,
    fps: int,
    ffmpeg: str,
    log: list[str],
    visuals: list,
    audio: Path | None,
    timeout_sec: float,
) -> dict[str, Any]:
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
                "visual_count": len(visuals),
            }
        rel = str(out.relative_to(ROOT)) if out.is_relative_to(ROOT) else str(out)
        color_bed = any("color_bed" in str(x) for x in log)
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
            "color_bed": color_bed,
            "manifest": {
                "title": "",
                "format": {"fps": fps, "resolution": {"width": width, "height": height}},
                "visuals": [str(v["path"]) for v in visuals[:40]],
                "audio": str(audio) if audio else "",
                "scene_count": len(visuals),
            },
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "mock": True,
            "error": f"ffmpeg timed out after {timeout_sec}s",
            "output_path": str(output_path),
            "log": log,
            "visual_count": len(visuals),
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("ffmpeg.assemble_failed")
        return {
            "ok": False,
            "mock": True,
            "error": str(exc),
            "output_path": str(output_path),
            "log": log,
            "visual_count": len(visuals),
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
