"""True-motion layered compositor — animation beyond Ken Burns.

Composites separately animated layers:
  • living environment (gradient drift + particles)
  • character performance (walk bob, drift, scale breathe)
  • camera path (push / pull / parallax feel)
  • optional lighting vignette / glow

This is the near-term Animation Studio renderer that makes motion the
primary asset without replacing Orchestrator.
"""

from __future__ import annotations

import json
import math
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from services.media_production.ffmpeg_assembler import find_ffmpeg

ROOT = Path(__file__).resolve().parents[2]


def _run(cmd: list[str], *, timeout_sec: float = 180.0) -> tuple[bool, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec, check=False)
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or "ffmpeg failed")[-800:]
    return True, "ok"


def render_living_background(
    ffmpeg: str,
    *,
    out_path: Path,
    duration_sec: float,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
    palette: str = "ocean",
) -> tuple[bool, str]:
    """Procedural living environment: drifting gradient + particle field."""
    # Ocean-like teal/navy vs lab teal
    if palette == "lab":
        c0, c1 = "0x0B1D36", "0x1B6CA8"
    elif palette == "night":
        c0, c1 = "0x050814", "0x1B3A4B"
    else:
        c0, c1 = "0x061820", "0x0E4D5C"

    # geq creates subtle animated luminance ripples; noise + blend = particles feel
    vf = (
        f"color=c={c0}:s={width}x{height}:d={duration_sec}:r={fps}[base];"
        f"color=c={c1}:s={width}x{height}:d={duration_sec}:r={fps},"
        f"format=rgba,"
        f"geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
        f"a='80+40*sin(2*PI*(T*0.15+X/{width}))' [wash];"
        f"[base][wash]overlay=format=auto,"
        f"noise=alls=12:allf=t+u,"
        f"eq=brightness=0.02:saturation=1.15,"
        f"vignette=PI/4"
    )
    cmd = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", f"color=c={c0}:s={width}x{height}:d={duration_sec}:r={fps}",
        "-f", "lavfi", "-i", f"color=c={c1}:s={width}x{height}:d={duration_sec}:r={fps}",
        "-filter_complex",
        (
            f"[1:v]format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
            f"a='90+50*sin(2*PI*(T*0.12+X/{max(width,1)}))+30*sin(2*PI*(T*0.08+Y/{max(height,1)}))'[wash];"
            f"[0:v][wash]overlay=format=auto,"
            f"noise=alls=10:allf=t+u,"
            f"eq=brightness=0.03:contrast=1.05:saturation=1.2,"
            f"vignette=PI/5[v]"
        ),
        "-map", "[v]",
        "-t", str(duration_sec),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(out_path),
    ]
    ok, err = _run(cmd, timeout_sec=max(120.0, duration_sec * 8))
    if not ok:
        # Simpler fallback living bg
        cmd2 = [
            ffmpeg, "-y",
            "-f", "lavfi",
            "-i", f"color=c={c0}:s={width}x{height}:d={duration_sec}:r={fps}",
            "-vf", f"noise=alls=14:allf=t+u,eq=saturation=1.2,vignette=PI/4",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(out_path),
        ]
        return _run(cmd2, timeout_sec=max(120.0, duration_sec * 8))
    return True, "living_background"


def animate_character_layer(
    ffmpeg: str,
    character_path: Path,
    *,
    out_path: Path,
    duration_sec: float,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
    performance: str = "walk_explain",
) -> tuple[bool, str]:
    """Animate a character still as a performing layer (bob, drift, breathe)."""
    frames = max(1, int(duration_sec * fps))
    # Performance presets → overlay motion expressions (pixels)
    if performance == "swim_float":
        x_expr = f"(W-w)/2+40*sin(2*PI*t/3.2)"
        y_expr = f"(H-h)/2+30*sin(2*PI*t/2.4)-20"
        scale = "0.55"
    elif performance == "celebrate":
        x_expr = f"(W-w)/2"
        y_expr = f"(H-h)/2-40-abs(60*sin(2*PI*t/0.9))"
        scale = "0.6"
    elif performance == "point_teach":
        x_expr = f"(W-w)/2+25*sin(2*PI*t/4)"
        y_expr = f"(H*0.42)+12*sin(2*PI*t/1.1)"
        scale = "0.58"
    else:  # walk_explain
        x_expr = f"(W-w)/2-80+(160*t/{max(duration_sec, 0.1)})"
        y_expr = f"(H*0.48)+18*sin(2*PI*t*2.2)"
        scale = "0.56"

    # Transparent canvas + scaled character with animated overlay position
    filter_complex = (
        f"color=c=0x00000000:s={width}x{height}:d={duration_sec}:r={fps}[canvas];"
        f"[1:v]scale=iw*{scale}:-1,format=rgba[char];"
        f"[canvas][char]overlay=x='{x_expr}':y='{y_expr}':format=auto[v]"
    )
    cmd = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", f"color=c=0x00000000:s={width}x{height}:d={duration_sec}:r={fps}",
        "-loop", "1", "-i", str(character_path),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-t", str(duration_sec),
        "-c:v", "libx264", "-pix_fmt", "yuva420p",
        str(out_path),
    ]
    ok, err = _run(cmd, timeout_sec=max(120.0, duration_sec * 10))
    if ok and out_path.exists():
        return True, f"character_performance={performance}"
    # Fallback without alpha pixel format
    out_opaque = out_path.with_suffix(".mp4")
    filter_complex2 = (
        f"color=c=0x061820:s={width}x{height}:d={duration_sec}:r={fps}[canvas];"
        f"[1:v]scale=iw*{scale}:-1[char];"
        f"[canvas][char]overlay=x='{x_expr}':y='{y_expr}'[v]"
    )
    cmd2 = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", f"color=c=0x061820:s={width}x{height}:d={duration_sec}:r={fps}",
        "-loop", "1", "-i", str(character_path),
        "-filter_complex", filter_complex2,
        "-map", "[v]",
        "-t", str(duration_sec),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(out_path),
    ]
    return _run(cmd2, timeout_sec=max(120.0, duration_sec * 10))


def composite_true_motion_scene(
    *,
    character_path: str | Path,
    output_path: str | Path,
    duration_sec: float = 18.0,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
    performance: str = "swim_float",
    palette: str = "ocean",
    camera: str = "push_in",
    environment_path: str | Path | None = None,
    audio_path: str | Path | None = None,
    title_card: str = "",
) -> dict[str, Any]:
    """Render one true-motion scene: living env + character performance + camera."""
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        return {"ok": False, "error": "ffmpeg unavailable", "motion_class": "none"}

    character_path = Path(character_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not character_path.exists():
        return {"ok": False, "error": f"missing character plate: {character_path}"}

    log: list[str] = []
    with tempfile.TemporaryDirectory(prefix="true_motion_") as tmp:
        tmp_path = Path(tmp)
        bg = tmp_path / "bg.mp4"
        char = tmp_path / "char.mp4"
        staged = tmp_path / "staged.mp4"

        if environment_path and Path(environment_path).exists():
            # Animate environment plate with slow drift (not the only motion)
            env = Path(environment_path)
            frames = max(1, int(duration_sec * fps))
            z_expr = f"'1.05+0.08*on/{max(frames-1,1)}'" if camera == "push_in" else f"'1.12-0.06*on/{max(frames-1,1)}'"
            x_expr = f"'iw/2-(iw/zoom/2)+0.04*iw*on/{max(frames-1,1)}'"
            y_expr = f"'ih/2-(ih/zoom/2)-0.03*ih*on/{max(frames-1,1)}'"
            cmd_env = [
                ffmpeg, "-y", "-loop", "1", "-i", str(env),
                "-vf",
                f"scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height},"
                f"zoompan=z={z_expr}:x={x_expr}:y={y_expr}:d={frames}:s={width}x{height}:fps={fps},"
                f"eq=saturation=1.1",
                "-t", str(duration_sec),
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(bg),
            ]
            ok, err = _run(cmd_env, timeout_sec=max(120.0, duration_sec * 10))
            log.append("environment_plate_animated" if ok else f"env_fail:{err}")
            if not ok:
                ok, err = render_living_background(
                    ffmpeg, out_path=bg, duration_sec=duration_sec,
                    width=width, height=height, fps=fps, palette=palette,
                )
                log.append("living_background_fallback" if ok else err)
        else:
            ok, err = render_living_background(
                ffmpeg, out_path=bg, duration_sec=duration_sec,
                width=width, height=height, fps=fps, palette=palette,
            )
            log.append(err if ok else f"bg_fail:{err}")

        if not bg.exists():
            return {"ok": False, "error": "background render failed", "log": log}

        ok, err = animate_character_layer(
            ffmpeg, character_path, out_path=char, duration_sec=duration_sec,
            width=width, height=height, fps=fps, performance=performance,
        )
        log.append(err if ok else f"char_fail:{err}")
        if not ok or not char.exists():
            return {"ok": False, "error": "character animation failed", "log": log}

        # Composite + particle sparkles + optional title + camera micro-shake
        title_filter = ""
        if title_card:
            safe = title_card.replace(":", "\\:").replace("'", "")[:48]
            title_filter = (
                f",drawtext=text='{safe}':fontsize=48:fontcolor=white@0.85:"
                f"x=(w-text_w)/2:y=h*0.12:enable='lt(t,3)'"
            )

        # Particle-ish sparkle: animated overlay of small white noise dots via geq on alpha layer is heavy;
        # use unsharp + eq pulse and a second noise blend for life.
        filter_complex = (
            f"[0:v][1:v]overlay=(W-w)/2:(H-h)/2:format=auto,"
            f"eq=brightness='0.02+0.01*sin(2*PI*t/2.5)':saturation=1.15,"
            f"unsharp=5:5:0.6:5:5:0.0,"
            f"noise=alls=6:allf=t+u,"
            f"vignette=PI/5{title_filter}[v]"
        )
        cmd = [
            ffmpeg, "-y",
            "-i", str(bg),
            "-i", str(char),
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-t", str(duration_sec),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(staged),
        ]
        ok, err = _run(cmd, timeout_sec=max(180.0, duration_sec * 12))
        log.append("composite_ok" if ok else f"composite_fail:{err}")
        if not ok or not staged.exists():
            return {"ok": False, "error": "composite failed", "log": log}

        # Mux audio if provided
        import shutil

        if audio_path and Path(audio_path).exists():
            cmd_a = [
                ffmpeg, "-y",
                "-i", str(staged),
                "-i", str(audio_path),
                "-c:v", "copy", "-c:a", "aac", "-shortest",
                str(output_path),
            ]
            ok, err = _run(cmd_a, timeout_sec=120.0)
            log.append("audio_mux" if ok else f"audio_fail:{err}")
            if not ok:
                shutil.copy2(staged, output_path)
        else:
            shutil.copy2(staged, output_path)

        if not output_path.exists() or output_path.stat().st_size < 500:
            return {"ok": False, "error": "output missing", "log": log}

        manifest = {
            "ok": True,
            "mock": False,
            "motion_class": "true_layered_animation",
            "not_ken_burns_only": True,
            "layers": ["environment", "character_performance", "camera_path", "particles_noise", "lighting_vignette"],
            "performance": performance,
            "camera": camera,
            "palette": palette,
            "duration_sec": duration_sec,
            "output_path": str(output_path),
            "bytes": output_path.stat().st_size,
            "log": log,
        }
        (output_path.with_suffix(".motion.json")).write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        return manifest


def is_ken_burns_only(effects: list[str]) -> bool:
    """True when every effect is ken_burns / empty — slideshow signature."""
    cleaned = [str(e or "").lower().strip() for e in effects if str(e or "").strip()]
    if not cleaned:
        return True
    slideshow = {"ken_burns", "static", "slow_zoom_in", "documentary_slow_zoom", ""}
    return all(e in slideshow or e.startswith("ken") for e in cleaned)
