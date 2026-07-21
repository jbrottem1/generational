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


def _palette_colors(palette: str, *, lighting_mood: str = "") -> tuple[str, str]:
    key = str(palette or "ocean").lower().strip()
    mood = str(lighting_mood or "").lower().strip()
    if mood in {"moonlight", "storm"} or key in {"night"}:
        return "0x050814", "0x1B3A4B"
    if mood == "golden_hour" or key in {"gold", "treasure"}:
        return "0x1A1408", "0xC48A2A"
    if mood == "firelight":
        return "0x1A0A08", "0xB84A18"
    if key in {"lab"}:
        return "0x0B1D36", "0x1B6CA8"
    if key in {"ireland", "irish", "fog", "mist", "countryside", "forest"}:
        # Misty greens / slate hills — ambient life, not flat backdrop
        return "0x0A2E24", "0x3D6B4F"
    if key in {"castle", "medieval"}:
        return "0x1A1520", "0x4A5568"
    return "0x061820", "0x0E4D5C"


def _lighting_grade(mood: str) -> str:
    """ffmpeg eq/curves snippet for motivated mood (V2)."""
    m = str(mood or "soft_daylight").lower()
    if m == "golden_hour":
        return "eq=brightness=0.04:contrast=1.12:saturation=1.35:gamma_r=1.08:gamma_b=0.92"
    if m == "moonlight":
        return "eq=brightness=-0.04:contrast=1.18:saturation=0.85:gamma_b=1.12"
    if m == "storm":
        return "eq=brightness=-0.06:contrast=1.25:saturation=0.7"
    if m == "firelight":
        return "eq=brightness=0.02:contrast=1.2:saturation=1.4:gamma_r=1.15:gamma_b=0.85"
    if m in {"volumetric_sunlight", "god_rays"}:
        return "eq=brightness=0.05:contrast=1.1:saturation=1.2"
    if m == "cinematic_contrast":
        return "eq=brightness=-0.02:contrast=1.3:saturation=1.05"
    return "eq=brightness=0.02:contrast=1.1:saturation=1.2"


def plate_is_static_fallback(path: Path | None) -> bool:
    """True when environment plate is a near-solid cinematic fallback still."""
    if not path or not Path(path).is_file():
        return True
    try:
        from PIL import Image
        import numpy as np

        arr = np.asarray(Image.open(path).convert("RGB").resize((64, 64)))
        # Unique colors on a tiny grid; solid plates collapse to 1–3 colors.
        uniq = len({tuple(px) for px in arr.reshape(-1, 3)})
        return uniq <= 8 or float(arr.std()) < 8.0
    except Exception:  # noqa: BLE001
        return Path(path).stat().st_size < 40_000


def render_title_overlay(
    text: str,
    *,
    out_path: Path,
    width: int = 1080,
    height: int = 1920,
) -> Path | None:
    """PIL motion-graphic title plate — avoids ffmpeg drawtext (often unavailable)."""
    safe = " ".join(str(text or "").replace("\n", " ").split())[:56]
    if not safe:
        return None
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 52)
        except Exception:  # noqa: BLE001
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 52)
            except Exception:  # noqa: BLE001
                font = ImageFont.load_default()
        bbox = d.textbbox((0, 0), safe, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pad_x, pad_y = 36, 18
        x0 = max(24, (width - tw) // 2 - pad_x)
        y0 = int(height * 0.10)
        x1 = min(width - 24, x0 + tw + 2 * pad_x)
        y1 = y0 + th + 2 * pad_y
        d.rounded_rectangle((x0, y0, x1, y1), radius=18, fill=(8, 24, 18, 200))
        d.text((x0 + pad_x, y0 + pad_y), safe, fill=(245, 248, 240, 255), font=font)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path)
        return out_path
    except Exception:  # noqa: BLE001
        return None


def render_living_background(
    ffmpeg: str,
    *,
    out_path: Path,
    duration_sec: float,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
    palette: str = "ocean",
    lighting_mood: str = "soft_daylight",
) -> tuple[bool, str]:
    """Living environment: FG/MG/BG depth, clouds, birds, wind scroll, mood grade."""
    c0, c1 = _palette_colors(palette, lighting_mood=lighting_mood)
    grade = _lighting_grade(lighting_mood)
    h = max(height, 1)
    # Grounded layers: sky, hills, foreground grass — not floating abstract blobs.
    cmd = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", f"color=c={c0}:s={width}x{height}:d={duration_sec}:r={fps}",
        "-f", "lavfi", "-i", f"color=c={c1}:s={width}x{height}:d={duration_sec}:r={fps}",
        "-f", "lavfi", "-i", f"color=c=0xDDE8DE:s={max(280, width // 2)}x{max(70, height // 22)}:d={duration_sec}:r={fps}",
        "-f", "lavfi", "-i", f"color=c=0xF5F0C8:s=36x36:d={duration_sec}:r={fps}",
        "-f", "lavfi", "-i", f"color=c=0x1A4A32:s={width}x{max(120, height // 8)}:d={duration_sec}:r={fps}",
        "-filter_complex",
        (
            # Background sky + hills (atmospheric banding)
            f"[0:v]format=rgba,geq="
            f"r='if(lt(Y,{int(h*0.38)}),10,if(lt(Y,{int(h*0.58)}),28,14))':"
            f"g='if(lt(Y,{int(h*0.38)}),38,if(lt(Y,{int(h*0.58)}),88,48))':"
            f"b='if(lt(Y,{int(h*0.38)}),58,if(lt(Y,{int(h*0.58)}),48,30))':"
            f"a='255'[sky];"
            f"[1:v]format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
            f"a='70+55*sin(2*PI*(T*0.12+X/{max(width,1)}))"
            f"+30*sin(2*PI*(T*0.08+Y/{max(height,1)}))'[wash];"
            # Midground clouds (soft, horizon-bound)
            f"[2:v]format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
            f"a='if(lt(hypot(X-W/2,Y-H/2),min(W,H)/2.2),140,0)',split=2[cloud1][cloud2];"
            # Background birds (small, slow — ambient life)
            f"[3:v]format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
            f"a='if(lt(hypot(X-18,Y-18),14),200,0)'[bird];"
            # Foreground grass band (grounded, not floating)
            f"[4:v]format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
            f"a='if(gt(Y,H*0.35),180+40*sin(2*PI*(T*1.1+X/40)),0)'[grass];"
            f"[sky][wash]overlay=format=auto[land];"
            f"[land][cloud1]overlay=x='-180+({width}+360)*(t/10-floor(t/10))':"
            f"y='{int(h*0.10)}+18*sin(2*PI*t/4)':format=auto[c1];"
            f"[c1][cloud2]overlay=x='{int(width*0.5)}+60*sin(2*PI*t/6)':"
            f"y='{int(h*0.18)}+14*cos(2*PI*t/3)':format=auto[c2];"
            f"[c2][bird]overlay=x='{int(width*0.08)}+({int(width*0.75)})*(t/{max(duration_sec,0.1)})':"
            f"y='{int(h*0.24)}+35*sin(2*PI*t*0.9)':format=auto[c3];"
            f"[c3][grass]overlay=x='0':y='{int(h*0.88)}+6*sin(2*PI*t*1.4)':format=auto,"
            f"scroll=horizontal=0.012:vertical=0.004,"
            f"noise=alls=10:allf=t+u,"
            f"{grade},"
            f"vignette=PI/5[v]"
        ),
        "-map", "[v]",
        "-t", str(duration_sec),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(out_path),
    ]
    ok, err = _run(cmd, timeout_sec=max(120.0, duration_sec * 10))
    if not ok:
        cmd2 = [
            ffmpeg, "-y",
            "-f", "lavfi",
            "-i", f"color=c={c0}:s={width}x{height}:d={duration_sec}:r={fps}",
            "-f", "lavfi",
            "-i", f"color=c={c1}:s=320x160:d={duration_sec}:r={fps}",
            "-filter_complex",
            (
                f"[0:v][1:v]overlay=x='40+({width}-360)*t/{max(duration_sec,0.1)}':"
                f"y='{int(height*0.18)}+24*sin(2*PI*t)',"
                f"scroll=horizontal=0.014:vertical=0.005,"
                f"noise=alls=12:allf=t+u,{grade},vignette=PI/4[v]"
            ),
            "-map", "[v]", "-t", str(duration_sec),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(out_path),
        ]
        return _run(cmd2, timeout_sec=max(120.0, duration_sec * 8))
    return True, f"living_background:{palette}:{lighting_mood or 'soft_daylight'}"


def _character_motion_exprs(
    performance: str,
    *,
    duration_sec: float,
    shot_size: str = "dynamic_medium",
    emotion: str = "focus",
    performance_path: dict[str, Any] | None = None,
) -> tuple[str, str, str]:
    """Return (x_expr, y_expr, scale_num) — actor path preferred over camera drift."""
    # Character Performance Engine: blocking path keyframes (actor-driven)
    if isinstance(performance_path, dict) and len(performance_path.get("keyframes") or []) >= 2:
        try:
            from services.character_performance_engine.true_motion_bridge import (
                path_to_ffmpeg_exprs,
            )

            return path_to_ffmpeg_exprs(
                performance_path,
                duration_sec=duration_sec,
                shot_size=shot_size,
            )
        except Exception:  # noqa: BLE001
            pass

    # Closer shots → larger scale; wider → smaller figure in living world
    base = {
        "intimate_close_up": 0.92,
        "hero_low_angle": 0.84,
        "dynamic_medium": 0.74,
        "high_angle_vulnerable": 0.62,
        "establishing_wide": 0.48,
    }.get(str(shot_size or "dynamic_medium"), 0.74)
    breathe = "8*sin(2*PI*t/3.2)"  # idle breathe
    if performance == "swim_float":
        x_expr = "(W-w)/2+50*sin(2*PI*t/3.0)"
        y_expr = f"(H-h)/2+40*sin(2*PI*t/2.2)-20+{breathe}"
        scale_num = f"{base:.2f}"
    elif performance == "celebrate":
        x_expr = "(W-w)/2+28*sin(2*PI*t/1.6)"
        y_expr = f"(H-h)/2-40-abs(70*sin(2*PI*t/0.85))+{breathe}"
        scale_num = f"{min(0.95, base + 0.04):.2f}"
    elif performance == "point_teach":
        x_expr = "(W-w)/2+40*sin(2*PI*t/2.8)"
        y_expr = f"(H*0.38)+18*sin(2*PI*t/1.05)+{breathe}"
        scale_num = f"{base:.2f}"
    else:  # walk_explain — weight transfer on walk cycle
        travel = 220 if emotion != "awe" else 140
        x_expr = f"(W-w)/2-{travel // 2}+({travel}*t/{max(duration_sec, 0.1)})"
        y_expr = f"(H*0.48)+24*sin(2*PI*t*2.0)+{breathe}"
        scale_num = f"{base:.2f}"
    return x_expr, y_expr, scale_num


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
    """Animate a character still as a performing layer (bob, drift, breathe).

    Note: intermediate alpha MP4s are unreliable; prefer compositing the PNG
    directly in composite_true_motion_scene. This helper remains for tests/CLI.
    """
    x_expr, y_expr, scale_num = _character_motion_exprs(performance, duration_sec=duration_sec)

    # Magenta key canvas — survives opaque encode; keyed at composite time if needed
    filter_complex = (
        f"color=c=0xFF00FF:s={width}x{height}:d={duration_sec}:r={fps}[canvas];"
        f"[1:v]scale=iw*{scale_num}:-1,format=rgba,"
        f"rotate='0.04*sin(2*PI*t/1.8)':c=none:ow=rotw(iw):oh=roth(ih)[char];"
        f"[canvas][char]overlay=x='{x_expr}':y='{y_expr}':format=auto[v]"
    )
    cmd = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", f"color=c=0xFF00FF:s={width}x{height}:d={duration_sec}:r={fps}",
        "-loop", "1", "-i", str(character_path),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-t", str(duration_sec),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(out_path),
    ]
    ok, err = _run(cmd, timeout_sec=max(120.0, duration_sec * 10))
    if ok and out_path.exists():
        return True, f"character_performance={performance}"
    return False, err


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
    lighting_mood: str = "soft_daylight",
    shot_size: str = "dynamic_medium",
    emotion: str = "focus",
    cinematic_v2: bool = True,
    performance_path: dict[str, Any] | None = None,
    actor_driven: bool = False,
) -> dict[str, Any]:
    """Render one true-motion scene: living env + character performance + camera.

    When ``performance_path`` (Character Performance Engine) is provided, the
    character follows blocking keyframes. Camera follows action and must not
    replace actor locomotion.
    """
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
        title_png = tmp_path / "title.png"

        env = Path(environment_path) if environment_path else None
        use_plate = bool(env and env.exists() and not plate_is_static_fallback(env))
        if use_plate:
            # Texture plate: animate with camera-informed zoompan
            frames = max(1, int(duration_sec * fps))
            cam = str(camera or "push_in").lower()
            if cam in {"pull_out", "reveal"}:
                z_expr = f"'1.18-0.12*on/{max(frames-1,1)}'"
                x_expr = f"'iw/2-(iw/zoom/2)-0.05*iw*on/{max(frames-1,1)}'"
                y_expr = f"'ih/2-(ih/zoom/2)+0.04*ih*on/{max(frames-1,1)}'"
            elif cam in {"orbit", "parallax"}:
                z_expr = f"'1.10+0.04*sin(2*PI*on/{max(frames,1)})'"
                x_expr = f"'iw/2-(iw/zoom/2)+0.08*iw*sin(2*PI*on/{max(frames,1)})'"
                y_expr = f"'ih/2-(ih/zoom/2)+0.05*ih*cos(2*PI*on/{max(frames,1)})'"
            elif cam in {"tracking", "handheld"}:
                z_expr = f"'1.08+0.05*on/{max(frames-1,1)}'"
                x_expr = f"'iw/2-(iw/zoom/2)+0.10*iw*on/{max(frames-1,1)}'"
                y_expr = f"'ih/2-(ih/zoom/2)+0.02*ih*sin(2*PI*on/{max(frames,1)})'"
            else:  # push_in / default
                z_expr = f"'1.04+0.14*on/{max(frames-1,1)}'"
                x_expr = f"'iw/2-(iw/zoom/2)+0.03*iw*on/{max(frames-1,1)}'"
                y_expr = f"'ih/2-(ih/zoom/2)-0.05*ih*on/{max(frames-1,1)}'"
            cmd_env = [
                ffmpeg, "-y", "-loop", "1", "-i", str(env),
                "-vf",
                f"scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height},"
                f"zoompan=z={z_expr}:x={x_expr}:y={y_expr}:d={frames}:s={width}x{height}:fps={fps},"
                f"eq=saturation=1.15,"
                f"noise=alls=8:allf=t+u",
                "-t", str(duration_sec),
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(bg),
            ]
            ok, err = _run(cmd_env, timeout_sec=max(120.0, duration_sec * 10))
            log.append("environment_plate_animated" if ok else f"env_fail:{err}")
            if not ok:
                ok, err = render_living_background(
                    ffmpeg, out_path=bg, duration_sec=duration_sec,
                    width=width, height=height, fps=fps, palette=palette,
                    lighting_mood=lighting_mood,
                )
                log.append("living_background_fallback" if ok else err)
        else:
            if env and env.exists():
                log.append("static_fallback_plate_skipped")
            ok, err = render_living_background(
                ffmpeg, out_path=bg, duration_sec=duration_sec,
                width=width, height=height, fps=fps, palette=palette,
                lighting_mood=lighting_mood,
            )
            log.append(err if ok else f"bg_fail:{err}")

        if not bg.exists():
            return {"ok": False, "error": "background render failed", "log": log}

        # Direct PNG overlay preserves alpha (unlike intermediate yuva/yuv char MP4s).
        actor_path = performance_path if isinstance(performance_path, dict) else None
        x_expr, y_expr, scale_num = _character_motion_exprs(
            performance,
            duration_sec=duration_sec,
            shot_size=shot_size,
            emotion=emotion,
            performance_path=actor_path,
        )
        path_driven = bool(actor_path and len(actor_path.get("keyframes") or []) >= 2)
        log.append(
            f"character_performance={performance}:{shot_size}:{emotion}"
            + (":actor_path" if path_driven else "")
        )

        # Motivated camera — amplitude scales with emotion (V2: no purposeless shake)
        # Actor-driven performances: camera follows; reduce zoom-as-action amplitude.
        cam = str(camera or "push_in").lower()
        if path_driven or actor_driven:
            if cam in {"push_in", "pull_out", "reveal"}:
                cam = "tracking"
            log.append(f"camera_follows_actor={cam}")
        amp = {
            "curiosity": 1.0,
            "tension": 1.15,
            "awe": 0.55,
            "warmth": 0.65,
            "melancholy": 0.5,
            "clarity": 0.75,
            "focus": 0.85,
        }.get(str(emotion or "focus"), 0.85)
        if path_driven or actor_driven:
            amp *= 0.55
        if cinematic_v2 and cam in {"handheld"}:
            cam_tail = (
                f",crop=w=iw*{0.90 - 0.02 * amp:.2f}:h=ih*{0.90 - 0.02 * amp:.2f}:"
                f"x='(iw-ow)/2+{int(22 * amp)}*sin(2*PI*t/0.9)':"
                f"y='(ih-oh)/2+{int(14 * amp)}*cos(2*PI*t/1.1)',scale={width}:{height}"
            )
        elif cam in {"orbit", "parallax"}:
            cam_tail = (
                f",crop=w=iw*{0.88 - 0.02 * amp:.2f}:h=ih*{0.88 - 0.02 * amp:.2f}:"
                f"x='(iw-ow)/2+{int(48 * amp)}*sin(2*PI*t/3.2)':"
                f"y='(ih-oh)/2+{int(32 * amp)}*cos(2*PI*t/3.2)',scale={width}:{height}"
            )
        elif cam in {"tracking"}:
            cam_tail = (
                f",crop=w=iw*0.90:h=ih*0.90:"
                f"x='(iw-ow)/2+{int(90 * amp)}*(t/{max(duration_sec,0.1)}-0.5)':"
                f"y='(ih-oh)/2+{int(14 * amp)}*sin(2*PI*t/1.8)',scale={width}:{height}"
            )
        elif cam in {"pull_out", "reveal"}:
            zoom = 0.10 * amp + 0.06
            cam_tail = (
                f",scale=iw*(1.16-{zoom:.2f}*t/{max(duration_sec,0.1)}):-1,"
                f"crop={width}:{height}"
            )
        else:  # push_in
            zoom = 0.12 * amp + 0.06
            cam_tail = (
                f",scale=iw*(1.02+{zoom:.2f}*t/{max(duration_sec,0.1)}):-1,"
                f"crop={width}:{height}"
            )

        title_path = render_title_overlay(title_card, out_path=title_png, width=width, height=height)

        # Story props only when titles/emotion call for them — avoid floating abstract shapes
        coin_png = tmp_path / "coin.png"
        mist_png = tmp_path / "mist.png"
        prop_ok = False
        title_l = str(title_card or "").lower()
        want_gold = cinematic_v2 and ("gold" in title_l or "treasure" in title_l or emotion == "awe")
        try:
            from PIL import Image, ImageDraw

            if want_gold:
                coin = Image.new("RGBA", (90, 90), (0, 0, 0, 0))
                ImageDraw.Draw(coin).ellipse((5, 5,
                                             85, 85), fill=(255, 215, 0, 235))
                coin.save(coin_png)
                mist = Image.new("RGBA", (220, 40), (0, 0, 0, 0))
                ImageDraw.Draw(mist).ellipse((0, 0, 220, 40), fill=(255, 240, 180, 90))
                mist.save(mist_png)
                prop_ok = True
                log.append("story_prop_gold")
            else:
                log.append("no_floating_abstract_props")
        except Exception as exc:  # noqa: BLE001
            log.append(f"prop_fail:{exc}")

        inputs: list[str] = [
            "-i", str(bg),
            "-loop", "1", "-t", str(duration_sec), "-i", str(character_path),
        ]
        idx = 2
        coin_idx = mist_idx = title_idx = None
        if prop_ok:
            inputs += ["-loop", "1", "-t", str(duration_sec), "-i", str(coin_png)]
            coin_idx = idx
            idx += 1
            inputs += ["-loop", "1", "-t", str(duration_sec), "-i", str(mist_png)]
            mist_idx = idx
            idx += 1
        if title_path:
            inputs += ["-loop", "1", "-t", str(min(3.2, duration_sec)), "-i", str(title_path)]
            title_idx = idx
            idx += 1
            log.append("title_overlay_pil")

        steps = [
            f"[1:v]scale=iw*{scale_num}:-1,format=rgba,"
            f"rotate='0.05*sin(2*PI*t/1.7)':c=none:ow=rotw(iw):oh=roth(ih)[char]",
            f"[0:v][char]overlay=x='{x_expr}':y='{y_expr}':format=auto[base]",
        ]
        tag = "base"
        if coin_idx is not None and mist_idx is not None:
            steps.append(
                f"[{tag}][{coin_idx}:v]overlay=x='40+({width}-200)*t/{max(duration_sec,0.1)}':"
                f"y='{int(height * 0.30)}+55*sin(2*PI*t/1.3)':format=auto[withcoin]"
            )
            tag = "withcoin"
            steps.append(
                f"[{tag}][{mist_idx}:v]overlay=x='-160+({width}+280)*t/{max(duration_sec,0.1)}':"
                f"y='{int(height * 0.16)}+30*sin(2*PI*t/2.0)':format=auto[withmist]"
            )
            tag = "withmist"
        if title_idx is not None:
            steps.append(
                f"[{tag}][{title_idx}:v]overlay=0:0:format=auto:enable='lt(t,3)'[withtitle]"
            )
            tag = "withtitle"
        filter_complex = (
            ";".join(steps)
            + f";[{tag}]eq=brightness='0.015+0.03*sin(2*PI*t/1.8)':saturation='1.15+0.2*sin(2*PI*t/3)',"
            f"unsharp=5:5:0.8:5:5:0.0,"
            f"noise=alls=10:allf=t+u,"
            f"vignette=PI/5{cam_tail}[v]"
        )

        cmd = [
            ffmpeg, "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-t", str(duration_sec),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(staged),
        ]
        ok, err = _run(cmd, timeout_sec=max(180.0, duration_sec * 12))
        log.append("composite_ok" if ok else f"composite_fail:{err}")
        if not ok or not staged.exists():
            # Minimal retry: bg + character PNG only
            filter_simple = (
                f"[1:v]scale=iw*0.7:-1,format=rgba[char];"
                f"[0:v][char]overlay=x='{x_expr}':y='{y_expr}':format=auto,"
                f"eq=brightness='0.02+0.03*sin(2*PI*t/1.6)':saturation=1.25,"
                f"noise=alls=12:allf=t+u,vignette=PI/5[v]"
            )
            cmd_r = [
                ffmpeg, "-y",
                "-i", str(bg),
                "-loop", "1", "-t", str(duration_sec), "-i", str(character_path),
                "-filter_complex", filter_simple,
                "-map", "[v]", "-t", str(duration_sec),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(staged),
            ]
            ok, err = _run(cmd_r, timeout_sec=max(180.0, duration_sec * 12))
            log.append("composite_retry_ok" if ok else f"composite_retry_fail:{err}")
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

        layers = ["environment", "character_performance", "camera_path", "particles_noise", "lighting_vignette"]
        if prop_ok:
            layers.append("animated_props")
        if title_path or (title_card and str(title_card).strip()):
            layers.append("motion_graphics_title")
        if cinematic_v2:
            layers.append("cinematic_v2_grade")

        manifest = {
            "ok": True,
            "mock": False,
            "motion_class": "actor_performance" if path_driven else "true_layered_animation",
            "not_ken_burns_only": True,
            "actor_driven": bool(path_driven or actor_driven),
            "performance_path_keyframes": len((actor_path or {}).get("keyframes") or []),
            "layers": layers,
            "performance": performance,
            "camera": cam if (path_driven or actor_driven) else camera,
            "palette": palette,
            "lighting_mood": lighting_mood,
            "shot_size": shot_size,
            "emotion": emotion,
            "cinematic_v2": cinematic_v2,
            "duration_sec": duration_sec,
            "output_path": str(output_path),
            "bytes": output_path.stat().st_size,
            "log": log,
            "used_environment_plate": use_plate,
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
