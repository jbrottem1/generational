"""Character performer — idle life + lip-synced mouth on a timeline."""

from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image

from services.animation.lip_sync import MouthDriver, build_mouth_timeline, load_mono_wav
from services.animation.stick_figure import StickFigureSpec, draw_stick_figure
from services.media_production.ffmpeg_assembler import find_ffmpeg


def _blink_at(t: float) -> float:
    # Blink ~ every 2.8s, duration ~0.12s
    cycle = 2.8
    phase = t % cycle
    if 0.05 < phase < 0.17:
        x = (phase - 0.05) / 0.12
        return float(1.0 - abs(2 * x - 1.0))
    return 0.0


def _educator_stage_x(width: int, t: float, duration: float, plan_id: str | None) -> int:
    """Planted stance; advance only during purposeful walk beats (eased)."""
    from services.animation.fluid_motion import smootherstep
    from services.animation.teaching_choreography import PLANS

    plan = PLANS.get(plan_id or "default") or PLANS["default"]
    p = t / max(duration, 0.1)
    total = 0.0
    done = 0.0
    for beat in plan:
        w = float(beat.get("walk") or 0.0)
        s, e = float(beat["start"]), float(beat["end"])
        span = max(1e-6, e - s)
        total += w * span
        if p >= e:
            done += w * span
        elif p > s:
            # Ease within the walk beat
            local = (p - s) / span
            done += w * span * smootherstep(local)
    progress = (done / total) if total > 1e-6 else 0.0
    return int(width * (0.03 + 0.14 * min(1.0, progress)))


def _performance_params(
    t: float,
    duration: float,
    *,
    teach: bool = False,
    educator: bool = False,
    plan_id: str | None = None,
) -> dict[str, float | str]:
    from services.animation.fluid_motion import blink_envelope, eased_walk_stride, fluid_life

    if educator:
        from services.animation.teaching_choreography import choreography_at

        choreo = choreography_at(t, duration, plan_id=plan_id)
        gesture = str(choreo["gesture"])
        walk_amt = float(choreo["walk"])
        life = fluid_life(t, professor=True)
        walk_stride = eased_walk_stride(t, walk_amt)
        return {
            "head_bob_y": life["head_bob_y"],
            "head_tilt": life["head_tilt"],
            "arm_phase": 0.0,
            "weight_shift": life["weight_shift"],
            "walk_stride": walk_stride,
            "gesture": gesture,
            "blink": blink_envelope(t),
            "walk_amt": walk_amt,
            "beat": str(choreo.get("label") or ""),
            "eye_drift": life["eye_drift"],
        }

    life = fluid_life(t, professor=False)
    if t < 1.4:
        gesture = "wave"
    elif teach and (duration * 0.2) < t < (duration * 0.75):
        gesture = "point" if int(t * 2) % 4 == 0 else "idle"
    else:
        gesture = "idle"

    return {
        "head_bob_y": life["head_bob_y"],
        "head_tilt": life["head_tilt"],
        "arm_phase": math.sin(2 * math.pi * t / 2.3),
        "weight_shift": life["weight_shift"],
        "walk_stride": 0.0,
        "gesture": gesture,
        "blink": blink_envelope(t),
        "eye_drift": life["eye_drift"],
    }


def render_lip_sync_performance(
    *,
    audio_path: str | Path,
    output_path: str | Path,
    width: int = 1080,
    height: int = 1920,
    fps: int = 24,
    bg_color: tuple[int, int, int] = (245, 247, 250),
    character_scale: float = 0.72,
    spec: StickFigureSpec | None = None,
    mouth_driver: MouthDriver | None = None,
    max_duration_sec: float = 60.0,
    demo_id: str | None = None,
    character_anchor: str = "center",
    educator_mode: bool = False,
) -> dict[str, Any]:
    """Render stick-figure performance synced to narration audio.

    Optional ``demo_id`` draws a concept overlay.
    ``educator_mode`` enables Generational Method choreography (purposeful gestures only).
    """
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        return {"ok": False, "error": "ffmpeg unavailable"}

    audio_path = Path(audio_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    samples, sr = load_mono_wav(audio_path)
    duration = len(samples) / float(sr)
    duration = max(3.0, min(float(max_duration_sec), duration))

    timeline = build_mouth_timeline(audio_path, duration_sec=duration, fps=float(fps), driver=mouth_driver)
    frames_meta = timeline["frames"]
    n_frames = len(frames_meta)
    spec = spec or StickFigureSpec()
    plan_id = demo_id if educator_mode else None

    demo_drawer = None
    if demo_id:
        from services.animation.educator_demos import get_educator_demo
        from services.animation.physics_demos import get_demo

        demo_drawer = get_educator_demo(demo_id) or get_demo(demo_id)

    gesture_counts: dict[str, int] = {}
    walk_frames = 0

    from services.animation.fluid_motion import GestureBlender, MouthSmoother, breath_scale

    blender = GestureBlender(blend_sec=0.38, anticipate_sec=0.08)
    mouth_smooth = MouthSmoother(alpha=0.55)

    with tempfile.TemporaryDirectory(prefix="perf_") as tmp:
        tmp_path = Path(tmp)
        frame_dir = tmp_path / "frames"
        frame_dir.mkdir()

        # Educator / MacroCenter: smaller grounded figure; leave room for holograms
        if educator_mode and (
            str(demo_id or "").startswith("macro_")
            or str(demo_id or "").startswith("excellence_")
            or str(demo_id or "").startswith("skydive_")
        ):
            scale = 0.38
        elif educator_mode:
            scale = 0.42
        else:
            scale = character_scale
        char_size = int(min(width, height) * scale)
        for i, row in enumerate(frames_meta):
            t = float(row["t"])
            openness = float(row["openness"])
            params = _performance_params(
                t,
                duration,
                teach=bool(demo_id),
                educator=educator_mode,
                plan_id=plan_id,
            )
            g = str(params["gesture"])
            gesture_counts[g] = gesture_counts.get(g, 0) + 1
            if float(params.get("walk_amt") or 0) > 0:
                walk_frames += 1

            blend = blender.update(t, g)
            pose = dict(blend["pose"])
            # Breath settles into the arms — life without fidget
            arm_breath = math.sin(2 * math.pi * t / 3.8) * 2.2
            pose["ly"] = float(pose.get("ly", 0)) + arm_breath
            pose["ry"] = float(pose.get("ry", 0)) + arm_breath * 0.85
            pose["lhy"] = float(pose.get("lhy", 0)) + arm_breath * 0.6
            pose["rhy"] = float(pose.get("rhy", 0)) + arm_breath * 0.5
            brow = float(pose.get("brow", 0.0))
            openness_s = mouth_smooth.update(openness)
            breath = breath_scale(t, professor=educator_mode)

            is_professor = bool(educator_mode)
            use_pose = educator_mode
            is_windy = bool(str(demo_id or "").startswith("skydive_") and educator_mode)
            arm_for_draw = float(params["arm_phase"])
            if is_windy:
                arm_for_draw = math.sin(2 * math.pi * t * 1.8) * 0.85

            char = draw_stick_figure(
                size=char_size,
                mouth_open=openness_s,
                blink=float(params["blink"]),
                head_tilt=float(params["head_tilt"]),
                head_bob_y=float(params["head_bob_y"]),
                arm_phase=arm_for_draw,
                weight_shift=float(params["weight_shift"]),
                walk_stride=float(params.get("walk_stride") or 0.0),
                gesture=g,
                confident=educator_mode,
                professor=is_professor,
                windy=is_windy,
                pose=pose if use_pose else None,
                eye_drift=float(params.get("eye_drift") or 0.0),
                brow_raise=brow,
                spec=spec,
            )
            canvas = Image.new("RGB", (width, height), bg_color)

            floor_y = int(height * 0.78)
            if demo_drawer is not None:
                demo_drawer(canvas, t, duration)
            elif educator_mode:
                # Minimal grounded classroom if no demo
                from services.animation.educator_demos import draw_classroom_floor

                floor_y = draw_classroom_floor(canvas)
            else:
                wash = Image.new(
                    "RGB",
                    (width, height),
                    (
                        max(0, bg_color[0] - 8),
                        max(0, bg_color[1] - 4),
                        min(255, bg_color[2] + int(6 * math.sin(t))),
                    ),
                )
                canvas = Image.blend(canvas, wash, 0.35)

            cw, ch = char.size
            cw2 = int(cw * breath)
            ch2 = int(ch * breath)
            char_r = char.resize((cw2, ch2), Image.Resampling.LANCZOS)

            if educator_mode:
                # Planted; only advance during walk beats — skydive: hold mid-left freefall
                if str(demo_id or "").startswith("skydive_"):
                    p = t / max(duration, 0.1)
                    if p < 0.10:
                        x = int(width * 0.12)
                    elif p >= 0.90:
                        x = (width - cw2) // 2
                    else:
                        x = int(width * 0.10)
                        # slight freefall drift
                        x += int(12 * math.sin(t * 1.5))
                    y = int(height * 0.28) + int(8 * math.sin(t * 2.2))
                    if p >= 0.90:
                        y = int(height * 0.52)
                else:
                    x = _educator_stage_x(width, t, duration, plan_id)
                    y = floor_y - ch2 + int(ch2 * 0.06)
            elif character_anchor == "left":
                x = int(width * 0.02)
                y = int(height * 0.38) + int(float(params["head_bob_y"]) * 6)
            else:
                x = (width - cw2) // 2
                y = int(height * 0.22) + int(float(params["head_bob_y"]) * 6)

            canvas.paste(char_r, (x, y), char_r)
            canvas.save(frame_dir / f"f_{i:05d}.png")

        silent = tmp_path / "silent.mp4"
        pattern = str(frame_dir / "f_%05d.png")
        cmd = [
            ffmpeg, "-y",
            "-framerate", str(fps),
            "-i", pattern,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-r", str(fps),
            str(silent),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=max(300, int(duration * 40)), check=False)
        if proc.returncode != 0 or not silent.exists():
            return {"ok": False, "error": (proc.stderr or "frame encode failed")[-500:], "timeline": timeline}

        cmd_a = [
            ffmpeg, "-y",
            "-i", str(silent),
            "-i", str(audio_path),
            "-c:v", "copy", "-c:a", "aac",
            "-shortest",
            str(output_path),
        ]
        proc = subprocess.run(cmd_a, capture_output=True, text=True, timeout=120, check=False)
        if proc.returncode != 0 or not output_path.exists():
            shutil.copy2(silent, output_path)
            return {
                "ok": False,
                "error": "audio mux failed — wrote silent video",
                "output_path": str(output_path),
                "timeline": timeline,
            }

    opens = [float(r["openness"]) for r in frames_meta]
    speaking = sum(1 for o in opens if o > 0.12)
    silent_f = sum(1 for o in opens if o <= 0.12)
    idle_ratio = gesture_counts.get("idle", 0) / max(1, n_frames)
    walk_ratio = walk_frames / max(1, n_frames)
    qc = {
        "mouth_varies": (max(opens) - min(opens)) > 0.2,
        "has_silence_closed": silent_f > 0,
        "has_speech_open": speaking > int(0.12 * n_frames),
        "speaking_ratio": round(speaking / max(1, n_frames), 3),
        "idle_motion": True,
        "blink_programmed": True,
        "educator_mode": educator_mode,
        "demo_id": demo_id or "",
        "duration_sec": duration,
        "frame_count": n_frames,
        "grounded": educator_mode,
        "interactive_teaching": bool(demo_id and educator_mode),
        "gesture_counts": gesture_counts,
        "idle_ratio": round(idle_ratio, 3),
        "walk_ratio": round(walk_ratio, 3),
        # Generational Method: mostly calm; walk is rare; no wave spam
        # Skydive format may use a brief end-wave (playful closer)
        "purposeful_gestures": (not educator_mode)
        or (
            idle_ratio >= 0.22
            and walk_ratio <= 0.20
            and (
                gesture_counts.get("wave", 0) == 0
                or (
                    str(demo_id or "").startswith("skydive_")
                    and gesture_counts.get("wave", 0) / max(1, n_frames) <= 0.08
                )
            )
        ),
    }
    qc["passed"] = bool(
        qc["mouth_varies"]
        and qc["has_silence_closed"]
        and qc["has_speech_open"]
        and qc["idle_motion"]
        and output_path.stat().st_size > 50_000
        and (not educator_mode or (qc["interactive_teaching"] and qc["purposeful_gestures"]))
    )

    return {
        "ok": True,
        "output_path": str(output_path),
        "bytes": output_path.stat().st_size,
        "character_id": spec.character_id,
        "duration_sec": duration,
        "fps": fps,
        "mouth_driver": timeline["driver"],
        "upgrade_path": timeline["upgrade_path"],
        "timeline": timeline,
        "qc": qc,
        "demo_id": demo_id,
        "educator_mode": educator_mode,
        "teaching_method": "generational_method" if educator_mode else None,
        "motion_class": "educator_lip_sync_performance" if educator_mode else "lip_sync_character_performance",
        "not_ken_burns_only": True,
    }
