#!/usr/bin/env python3
"""Animation Engine Validation — re-render Leprechaun Short visuals only.

Preserves research/script/narration/captions/thumbnail/project tree.
Replaces visual execution with Animation Engine V1 + true_motion.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TOPIC = "Are Leprechauns Real? The Truth Behind Ireland's Tiny Tricksters"
PROJ = (
    Path.home()
    / "Desktop"
    / "AI Start-UP"
    / "Videos"
    / "History"
    / "Folklore"
    / TOPIC
)
BEFORE_NAME = "Are_Leprechauns_Real_The_Truth_Behind_Irelands_Tiny_Tricksters.mp4"
AFTER_NAME = "Are_Leprechauns_Real_ANIMATION_V1.mp4"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ffprobe(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        raw = subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration,size",
                "-show_entries",
                "stream=codec_type,codec_name,width,height",
                "-of",
                "json",
                str(path),
            ],
            text=True,
        )
        return json.loads(raw)
    except Exception:  # noqa: BLE001
        return {}


def _duration(path: Path) -> float:
    return float((_ffprobe(path).get("format") or {}).get("duration") or 0)


def draw_leprechaun_plate(path: Path, *, size: int = 1024) -> Path:
    """Animated character plate — green-coated folkloric figure (not a static stock icon)."""
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = size // 2, int(size * 0.36)
    # Hat
    d.polygon(
        [(cx - 140, cy - 40), (cx + 140, cy - 40), (cx + 90, cy - 180), (cx - 90, cy - 180)],
        fill=(20, 120, 55, 255),
        outline=(10, 60, 30, 255),
    )
    d.ellipse((cx - 160, cy - 55, cx + 160, cy - 5), fill=(18, 100, 45, 255), outline=(8, 50, 25, 255), width=4)
    d.rectangle((cx - 50, cy - 95, cx + 50, cy - 70), fill=(212, 175, 55, 255))  # buckle
    # Head
    d.ellipse((cx - 110, cy - 30, cx + 110, cy + 160), fill=(255, 220, 180, 255), outline=(40, 30, 20, 255), width=5)
    # Eyes (will blink via character layer bob — drawn open)
    for ex in (cx - 55, cx + 15):
        d.ellipse((ex, cy + 30, ex + 40, cy + 70), fill=(255, 255, 255, 255), outline=(20, 20, 20, 255), width=3)
        d.ellipse((ex + 12, cy + 42, ex + 28, cy + 60), fill=(30, 80, 40, 255))
    # Smile + beard
    d.arc((cx - 45, cy + 70, cx + 45, cy + 120), 20, 160, fill=(20, 20, 20, 255), width=4)
    d.ellipse((cx - 95, cy + 100, cx + 95, cy + 210), fill=(240, 230, 200, 255), outline=(180, 160, 120, 255), width=3)
    # Body coat
    d.polygon(
        [(cx - 120, cy + 170), (cx + 120, cy + 170), (cx + 150, int(size * 0.78)), (cx - 150, int(size * 0.78))],
        fill=(25, 130, 60, 255),
        outline=(10, 60, 30, 255),
    )
    # Arms
    d.line((cx - 90, cy + 220, cx - 200, cy + 320), fill=(10, 60, 30, 255), width=14)
    d.line((cx + 90, cy + 220, cx + 210, cy + 280), fill=(10, 60, 30, 255), width=14)
    d.ellipse((cx + 190, cy + 260, cx + 230, cy + 300), fill=(255, 220, 180, 255), outline=(40, 30, 20, 255), width=3)
    # Legs + shoes
    d.line((cx - 40, int(size * 0.78), cx - 80, int(size * 0.92)), fill=(10, 60, 30, 255), width=14)
    d.line((cx + 40, int(size * 0.78), cx + 90, int(size * 0.92)), fill=(10, 60, 30, 255), width=14)
    d.ellipse((cx - 120, int(size * 0.90), cx - 40, int(size * 0.96)), fill=(120, 40, 30, 255))
    d.ellipse((cx + 50, int(size * 0.90), cx + 130, int(size * 0.96)), fill=(120, 40, 30, 255))
    # Pot of gold prop (right)
    d.ellipse((cx + 160, cy + 340, cx + 280, cy + 420), fill=(40, 40, 40, 255))
    d.ellipse((cx + 175, cy + 330, cx + 265, cy + 370), fill=(255, 200, 40, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path


def load_source_candidate() -> dict:
    script = json.loads((PROJ / "Project" / "SCRIPT.json").read_text(encoding="utf-8"))
    scenes = []
    breakdown = list(script.get("scene_breakdown") or [])
    # Prefer latest per scene index assets
    by_idx: dict[int, Path] = {}
    for p in sorted((PROJ / "Assets").glob("scene_*.png")):
        try:
            idx = int(p.name.split("_")[1])
        except Exception:  # noqa: BLE001
            continue
        by_idx[idx] = p  # later overwrite = newer mtime order from sorted name; refine by mtime
    for p in sorted((PROJ / "Assets").glob("scene_*.png"), key=lambda x: x.stat().st_mtime):
        try:
            idx = int(p.name.split("_")[1])
        except Exception:  # noqa: BLE001
            continue
        by_idx[idx] = p

    for i, beat in enumerate(breakdown):
        idx = int(beat.get("scene") or i + 1)
        still = by_idx.get(idx) or by_idx.get(i + 1)
        scenes.append(
            {
                "scene_number": idx,
                "purpose": beat.get("purpose") or "story_beat",
                "length_sec": float(beat.get("length_sec") or 5),
                "narration": beat.get("narration") or "",
                "subject": "leprechaun" if i < 5 else "folklore",
                "image": str(still) if still else "",
                "approved_asset_path": str(still) if still else "",
            }
        )
    world = {}
    wp = PROJ / "Project" / "WORLD_PACKAGE.json"
    if wp.is_file():
        try:
            world = json.loads(wp.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            world = {}
    return {
        "topic": TOPIC,
        "title": TOPIC,
        "hook": script.get("hook"),
        "narration": script.get("narration"),
        "structured_script": script,
        "world_package": world or {"world_type": "Irish misty countryside"},
        "visual_package": {"scenes": scenes},
        "scenes": scenes,
    }


def analyze_mp4_motion(path: Path, *, sample_fps: float = 2.0) -> dict:
    """Measure motion from the exported MP4 (frame diffs) — not scene plans."""
    from PIL import Image
    import numpy as np

    dur = _duration(path)
    if dur <= 0 or not path.is_file():
        return {"ok": False, "error": "missing_mp4"}

    with tempfile.TemporaryDirectory(prefix="motion_probe_") as tmp:
        tmp_p = Path(tmp)
        pattern = tmp_p / "f_%04d.png"
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(path),
            "-vf",
            f"fps={sample_fps},scale=320:-1",
            str(pattern),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        frames = sorted(tmp_p.glob("f_*.png"))
        if len(frames) < 3:
            return {
                "ok": False,
                "error": "too_few_frames",
                "stderr": (proc.stderr or "")[-400:],
            }

        diffs: list[float] = []
        prev = None
        for fp in frames:
            arr = np.asarray(Image.open(fp).convert("L"), dtype=np.float32)
            if prev is not None:
                mad = float(np.mean(np.abs(arr - prev)))
                diffs.append(mad)
            prev = arr

        # Threshold: near-static frames (slideshows cluster very low)
        static_thr = 2.5
        static_n = sum(1 for d in diffs if d < static_thr)
        static_pct = 100.0 * static_n / max(1, len(diffs))
        mean_diff = float(sum(diffs) / max(1, len(diffs)))
        p90 = float(sorted(diffs)[int(0.9 * (len(diffs) - 1))])

        return {
            "ok": True,
            "duration_sec": round(dur, 2),
            "sampled_frames": len(frames),
            "diff_samples": len(diffs),
            "mean_frame_diff": round(mean_diff, 3),
            "p90_frame_diff": round(p90, 3),
            "static_frame_pct": round(static_pct, 2),
            "static_threshold_mad": static_thr,
            "motion_density": round(min(100.0, mean_diff * 8.0), 1),
        }


def grab_screenshot(mp4: Path, t_sec: float, out: Path) -> Path | None:
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(max(0.0, t_sec)),
        "-i",
        str(mp4),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(out),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return out if out.is_file() and proc.returncode == 0 else None


def render_animated_scenes(candidate: dict, anim_pkg: dict, char_plate: Path, work: Path) -> list[dict]:
    from services.media_production.true_motion import composite_true_motion_scene

    audio_dur = _duration(next((PROJ / "Audio").glob("*.mp3")))
    decisions = list(anim_pkg.get("scene_decisions") or [])
    scenes = list((candidate.get("visual_package") or {}).get("scenes") or [])
    plan_total = sum(float(s.get("length_sec") or 3) for s in scenes) or 1.0

    # Guarantee camera variety across the Short (not locked push-ins).
    camera_cycle = ["push_in", "orbit", "tracking", "pull_out", "parallax", "handheld", "reveal"]
    palette_cycle = ["ireland", "fog", "castle", "gold", "ireland", "medieval", "ireland"]

    clips: list[dict] = []
    for i, scene in enumerate(scenes):
        dec = decisions[i] if i < len(decisions) else {}
        layers = dec.get("layers") or {}
        cam = (layers.get("camera") or {}).get("true_motion_camera") or dec.get("true_motion_camera")
        cam_map = {
            "pull_out": "pull_out",
            "orbit": "orbit",
            "tracking": "tracking",
            "handheld": "handheld",
            "reveal": "reveal",
            "parallax": "parallax",
            "rack_focus": "push_in",
            "punch_in": "push_in",
            "push_in": "push_in",
        }
        camera = cam_map.get(str(cam), camera_cycle[i % len(camera_cycle)])
        perf = (layers.get("character") or {}).get("performance") or "walk_explain"
        narr = str(scene.get("narration") or "").lower()
        if any(w in narr for w in ("gold", "green", "evidence", "word", "luchorp")):
            perf = "point_teach"
        elif scene.get("purpose") == "hook":
            perf = "walk_explain"
        elif scene.get("purpose") == "payoff":
            perf = "celebrate"

        dur = max(2.0, audio_dur * (float(scene.get("length_sec") or 3) / plan_total))
        env = scene.get("approved_asset_path") or scene.get("image") or None
        out = work / f"anim_scene_{int(scene.get('scene_number') or i+1):02d}.mp4"
        # ASCII titles — PIL fonts handle them; avoid exotic glyphs for portability.
        title = ""
        if "gold" in narr:
            title = "FAIRY GOLD"
        elif "green" in narr or "red coat" in narr:
            title = "GREEN IS MODERN"
        elif "evidence" in narr or "archaeological" in narr:
            title = "FOLKLORE != HISTORY"
        elif "luchorp" in narr or "little body" in narr:
            title = "luchorpan = little body"
        elif scene.get("purpose") == "hook":
            title = "WHERE DID THE LEGEND BEGIN?"

        palette = palette_cycle[i % len(palette_cycle)]
        hint = (layers.get("world") or {}).get("palette_hint")
        if hint in {"ireland", "fog", "castle", "gold", "medieval", "mist"}:
            palette = hint
        if "gold" in narr:
            palette = "gold"
        elif "evidence" in narr or "castle" in narr or "medieval" in narr:
            palette = "castle"

        manifest = composite_true_motion_scene(
            character_path=char_plate,
            output_path=out,
            duration_sec=dur,
            width=1080,
            height=1920,
            fps=30,
            performance=perf,
            palette=palette,
            camera=camera,
            environment_path=env if env and Path(str(env)).is_file() else None,
            title_card=title,
        )
        clips.append(
            {
                "scene_number": scene.get("scene_number") or i + 1,
                "path": str(out) if out.is_file() and manifest.get("ok") else None,
                "ok": bool(manifest.get("ok")),
                "manifest": manifest,
                "duration_sec": dur,
                "camera": camera,
                "performance": perf,
                "title": title,
                "palette": palette,
                "error": manifest.get("error"),
                "log": (manifest.get("log") or [])[-4:],
                "active_motion_classes": (layers.get("active_motion_classes") or []),
            }
        )
    return clips


def concat_with_audio(clips: list[dict], audio: Path, dest: Path) -> dict:
    from services.media_production.ffmpeg_assembler import find_ffmpeg

    ffmpeg = find_ffmpeg()
    paths = [Path(c["path"]) for c in clips if c.get("path") and Path(str(c["path"])).is_file()]
    if not paths:
        return {"ok": False, "error": "no_clips"}
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="lep_concat_") as tmp:
        tmp_p = Path(tmp)
        # Re-encode each clip to identical params for concat safety
        norm: list[Path] = []
        for i, p in enumerate(paths):
            np = tmp_p / f"n_{i:02d}.mp4"
            cmd = [
                ffmpeg,
                "-y",
                "-i",
                str(p),
                "-vf",
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-an",
                str(np),
            ]
            subprocess.run(cmd, capture_output=True, text=True, check=False)
            if np.is_file():
                norm.append(np)
        lst = tmp_p / "list.txt"
        lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in norm), encoding="utf-8")
        silent = tmp_p / "silent.mp4"
        concat_cmd = [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(lst),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(silent),
        ]
        proc = subprocess.run(concat_cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0 or not silent.is_file():
            return {"ok": False, "error": (proc.stderr or "")[-600:]}
        mux = [
            ffmpeg,
            "-y",
            "-i",
            str(silent),
            "-i",
            str(audio),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            str(dest),
        ]
        proc2 = subprocess.run(mux, capture_output=True, text=True, check=False)
        return {
            "ok": proc2.returncode == 0 and dest.is_file(),
            "error": (proc2.stderr or "")[-400:] if proc2.returncode else None,
            "path": str(dest),
            "bytes": dest.stat().st_size if dest.is_file() else 0,
        }


def judge(before: dict, after: dict, anim_pkg: dict, clips: list[dict]) -> dict:
    excellence = (anim_pkg.get("animation_excellence") or {}).get("animation_excellence_score")
    gate = anim_pkg.get("quality_gate") or {}

    def _metric(d: dict, key: str, default: float) -> float:
        if not d or key not in d or d.get(key) is None:
            return float(default)
        return float(d.get(key))

    after_static = _metric(after, "static_frame_pct", 100.0)
    before_static = _metric(before, "static_frame_pct", 100.0)
    after_motion = _metric(after, "mean_frame_diff", 0.0)
    before_motion = _metric(before, "mean_frame_diff", 0.0)
    char_ok = all(c.get("ok") for c in clips) and any(
        "character" in str((c.get("manifest") or {}).get("layers") or []) for c in clips
    )
    cam_variety = len({c.get("camera") for c in clips})
    env_ok = all("environment" in str((c.get("manifest") or {}).get("layers") or []) for c in clips if c.get("ok"))
    mg_ok = any(c.get("title") for c in clips)

    checks = {
        "every_scene_renders": all(c.get("ok") and c.get("path") for c in clips),
        "character_layer_present": char_ok,
        "camera_moves_variety": cam_variety >= 3,
        "environment_alive": env_ok,
        "motion_graphics_titles": mg_ok,
        "static_under_10pct": after_static < 10.0,
        "mean_motion_improved": after_motion > before_motion * 1.15,
        "static_reduced": after_static < before_static - 5,
        "animation_excellence_ge_75": float(excellence or 0) >= 75,
        "plan_gate_approve": gate.get("decision") == "APPROVE",
        "true_layered_motion_class": all(
            (c.get("manifest") or {}).get("motion_class") == "true_layered_animation" for c in clips if c.get("ok")
        ),
    }
    passed = all(
        checks[k]
        for k in (
            "every_scene_renders",
            "character_layer_present",
            "camera_moves_variety",
            "environment_alive",
            "static_under_10pct",
            "true_layered_motion_class",
        )
    ) and (checks["mean_motion_improved"] or checks["static_reduced"])

    # Honest viewer question — Generational true-motion is layered 2D, not studio 3D.
    reasons = []
    if after_static >= 10:
        reasons.append(f"Static frame share still {after_static}% (≥10%).")
    if after_motion < 4:
        reasons.append(f"Mean frame delta {after_motion:.2f} is still low for pro animation.")
    if not checks["character_layer_present"]:
        reasons.append("Character performance layer missing/failed on some scenes.")
    if not checks["mean_motion_improved"] and not checks["static_reduced"]:
        reasons.append("Exported MP4 is not clearly more active than the prior slideshow render.")
    if passed and after_motion >= 8 and after_static < 10:
        believe = (
            "MOSTLY — every scene has measurable motion (camera, living Ireland env, character performance, "
            "props, titles). A viewer would not mistake it for the prior slideshow. They would correctly see "
            "it as Generational Animation Engine / true-motion documentary layers (procedural landscape + "
            "puppet character), not a high-end studio 3D short."
        )
    elif passed:
        believe = (
            "MOSTLY — layered character + living env + camera clearly beat the prior slideshow, but craft "
            "still reads as procedural true-motion rather than premium studio animation."
        )
    else:
        believe = "NO — " + (" ".join(reasons) if reasons else "motion metrics failed validation thresholds.")

    weaknesses = []
    if after_motion < 8:
        weaknesses.append("Increase character pose variety / walk cycles beyond single-plate bob.")
    if cam_variety < 5:
        weaknesses.append("Push more distinct camera tokens through true_motion (orbit/parallax need stronger pixel evidence).")
    weaknesses.append("Character is a single-plate puppet (bob/drift/rotate), not multi-joint skeletal animation.")
    weaknesses.append("Replace procedural living backgrounds with Irish landscape video plates when stock is available.")
    weaknesses.append("Lip-sync is approximate (performance layer), not phoneme-accurate.")
    weaknesses.append("Scene assets from the original production were solid-color fallbacks — animation rebuilt environments procedurally.")

    return {
        "passed": passed,
        "checks": checks,
        "viewer_belief": believe,
        "remaining_weaknesses": weaknesses,
        "before_static_pct": before_static,
        "after_static_pct": after_static,
        "before_mean_diff": before_motion,
        "after_mean_diff": after_motion,
        "animation_excellence_score": excellence,
        "camera_variety": cam_variety,
    }


def run() -> dict:
    if not PROJ.is_dir():
        raise SystemExit(f"Missing project: {PROJ}")

    reports = PROJ / "Reports"
    comparison = PROJ / "Comparison"
    anim_dir = PROJ / "Animation"
    for d in (reports, comparison, anim_dir):
        d.mkdir(parents=True, exist_ok=True)

    before = PROJ / "Export" / BEFORE_NAME
    dated = next((PROJ / "Export").glob("2026-*.mp4"), None)
    before_copy = comparison / "BEFORE_slideshow.mp4"
    # Prefer an existing comparison before, else restore from dated original, else Export name.
    if before_copy.is_file() and _duration(before_copy) > 40:
        pass  # keep sticky before
    elif dated and dated.is_file() and _duration(dated) > 40:
        shutil.copy2(dated, before_copy)
        if not before.is_file() or _duration(before) < 40:
            shutil.copy2(dated, before)
    elif before.is_file():
        shutil.copy2(before, before_copy)

    candidate = load_source_candidate()
    from services.animation_engine import attach_animation_package, build_animation_package

    anim_pkg = build_animation_package(
        candidate,
        topic=TOPIC,
        production_id="animation_validation_leprechaun",
        write=True,
        out_path=anim_dir / "ANIMATION_PACKAGE.json",
    )
    candidate = attach_animation_package(candidate, anim_pkg)
    (PROJ / "Project" / "ANIMATION_PACKAGE.json").write_text(
        json.dumps(anim_pkg, indent=2, default=str) + "\n", encoding="utf-8"
    )

    char_plate = draw_leprechaun_plate(anim_dir / "leprechaun_character_plate.png")
    work = anim_dir / "scene_clips"
    work.mkdir(parents=True, exist_ok=True)
    clips = render_animated_scenes(candidate, anim_pkg, char_plate, work)

    audio = next((PROJ / "Audio").glob("*.mp3"))
    after = PROJ / "Export" / AFTER_NAME
    mux = concat_with_audio(clips, audio, after)
    # Refresh animation export + comparison AFTER only — never clobber sticky BEFORE.
    if mux.get("ok") and after.is_file():
        shutil.copy2(after, comparison / "AFTER_animation_v1.mp4")
        # Canonical export points at the latest animation validation render.
        shutil.copy2(after, PROJ / "Export" / BEFORE_NAME)

    before_motion = analyze_mp4_motion(before_copy if before_copy.is_file() else before)
    after_motion = analyze_mp4_motion(after)

    # Screenshots
    shots = []
    for label, src, times in (
        ("before", before_copy if before_copy.is_file() else before, (1.0, 12.0, 28.0)),
        ("after", after, (1.0, 12.0, 28.0)),
    ):
        for t in times:
            out = comparison / f"{label}_t{int(t):02d}s.jpg"
            if grab_screenshot(src, t, out):
                shots.append(str(out))

    verdict = judge(before_motion, after_motion, anim_pkg, clips)

    report = {
        "mission": "Animation Engine Validation Production",
        "topic": TOPIC,
        "generated_at": _now(),
        "publishing_enabled": False,
        "source_preserved": {
            "script": str(PROJ / "Project" / "SCRIPT.json"),
            "audio": str(audio),
            "captions": str(next((PROJ / "Captions").glob("*"), "")),
            "thumbnail": str(next((PROJ / "Thumbnail").glob("*"), "")),
        },
        "outputs": {
            "after_mp4": str(after),
            "before_mp4": str(before_copy),
            "animation_package": anim_pkg.get("path"),
            "screenshots": shots,
        },
        "clips": [
            {
                "scene": c.get("scene_number"),
                "ok": c.get("ok"),
                "camera": c.get("camera"),
                "performance": c.get("performance"),
                "title": c.get("title"),
                "motion_class": (c.get("manifest") or {}).get("motion_class"),
                "layers": (c.get("manifest") or {}).get("layers"),
                "active_motion_classes": c.get("active_motion_classes"),
            }
            for c in clips
        ],
        "before_video_analysis": before_motion,
        "after_video_analysis": after_motion,
        "animation_excellence": anim_pkg.get("animation_excellence"),
        "plan_quality_gate": anim_pkg.get("quality_gate"),
        "verdict": verdict,
        "mux": mux,
    }

    (reports / "ANIMATION_VALIDATION_REPORT.json").write_text(
        json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8"
    )
    md = _markdown(report)
    (reports / "ANIMATION_VALIDATION_REPORT.md").write_text(md, encoding="utf-8")
    (reports / "SIDE_BY_SIDE_COMPARISON.md").write_text(_comparison_md(report), encoding="utf-8")
    (ROOT / "ANIMATION_VALIDATION_LEPRECHAUN.md").write_text(md, encoding="utf-8")
    return report


def _markdown(report: dict) -> str:
    v = report.get("verdict") or {}
    before = report.get("before_video_analysis") or {}
    after = report.get("after_video_analysis") or {}
    ex = report.get("animation_excellence") or {}
    lines = [
        "# Animation Engine Validation — Leprechaun Short",
        "",
        f"**Topic:** {report.get('topic')}",
        f"**Generated:** {report.get('generated_at')}",
        f"**Result:** {'PASS' if v.get('passed') else 'FAIL'}",
        "",
        "## Would a viewer believe this was professionally animated?",
        "",
        v.get("viewer_belief") or "Unknown",
        "",
        "## Animation Excellence",
        "",
        f"- Score: **{ex.get('animation_excellence_score')}**",
        f"- Plan gate: `{(report.get('plan_quality_gate') or {}).get('decision')}`",
        "",
        "## Exported video motion analysis (MP4 evidence)",
        "",
        "| Metric | Before | After |",
        "|---|---:|---:|",
        f"| Duration | {before.get('duration_sec')} | {after.get('duration_sec')} |",
        f"| Mean frame diff | {before.get('mean_frame_diff')} | {after.get('mean_frame_diff')} |",
        f"| P90 frame diff | {before.get('p90_frame_diff')} | {after.get('p90_frame_diff')} |",
        f"| Static frame % | {before.get('static_frame_pct')} | {after.get('static_frame_pct')} |",
        f"| Motion density | {before.get('motion_density')} | {after.get('motion_density')} |",
        "",
        "## Pass checks",
        "",
    ]
    for k, val in (v.get("checks") or {}).items():
        lines.append(f"- {k}: {'✓' if val else '✗'}")
    lines += ["", "## Remaining creative weaknesses", ""]
    for w in v.get("remaining_weaknesses") or []:
        lines.append(f"- {w}")
    lines += [
        "",
        "## Outputs",
        "",
        f"- After MP4: `{(report.get('outputs') or {}).get('after_mp4')}`",
        f"- Before MP4: `{(report.get('outputs') or {}).get('before_mp4')}`",
        f"- Screenshots: {len((report.get('outputs') or {}).get('screenshots') or [])}",
        "",
        "_Visual execution only — script/narration/captions/thumbnail preserved. Publishing disabled._",
        "",
    ]
    return "\n".join(lines)


def _comparison_md(report: dict) -> str:
    before = report.get("before_video_analysis") or {}
    after = report.get("after_video_analysis") or {}
    return "\n".join(
        [
            "# Side-by-side comparison — Leprechaun Short",
            "",
            "## Files",
            "",
            f"- Before: `{(report.get('outputs') or {}).get('before_mp4')}`",
            f"- After: `{(report.get('outputs') or {}).get('after_mp4')}`",
            "",
            "## Screenshots",
            "",
            *[f"- `{s}`" for s in (report.get("outputs") or {}).get("screenshots") or []],
            "",
            "## Motion delta",
            "",
            f"- Mean frame diff: {before.get('mean_frame_diff')} → {after.get('mean_frame_diff')}",
            f"- Static %: {before.get('static_frame_pct')} → {after.get('static_frame_pct')}",
            "",
            "## Scene motion classes (after)",
            "",
            *[
                f"- Scene {c.get('scene')}: camera=`{c.get('camera')}` perf=`{c.get('performance')}` "
                f"class=`{c.get('motion_class')}` title=`{c.get('title')}`"
                for c in report.get("clips") or []
            ],
            "",
        ]
    )


if __name__ == "__main__":
    out = run()
    print(
        json.dumps(
            {
                "passed": (out.get("verdict") or {}).get("passed"),
                "viewer_belief": (out.get("verdict") or {}).get("viewer_belief"),
                "excellence": (out.get("animation_excellence") or {}).get("animation_excellence_score"),
                "before_static": (out.get("before_video_analysis") or {}).get("static_frame_pct"),
                "after_static": (out.get("after_video_analysis") or {}).get("static_frame_pct"),
                "before_diff": (out.get("before_video_analysis") or {}).get("mean_frame_diff"),
                "after_diff": (out.get("after_video_analysis") or {}).get("mean_frame_diff"),
                "after_mp4": (out.get("outputs") or {}).get("after_mp4"),
            },
            indent=2,
        )
    )
    raise SystemExit(0 if (out.get("verdict") or {}).get("passed") else 2)
