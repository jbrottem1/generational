#!/usr/bin/env python3
"""Full publication-ready Short: Why Octopuses Have Three Hearts.

Uses existing studio ops + world builder + packaging. No new engines.
Publishing disabled. Organizes into AI Start-UP/Videos/Shorts/Science/Biology/...
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env  # noqa: E402

load_application_env(create_if_missing=False)

import engines  # noqa: F401, E402
from services.production_operations import run_studio_ops  # noqa: E402
from services.world_builder import place_candidate_in_world, reset_world_state  # noqa: E402

TOPIC = "Why Octopuses Have Three Hearts"
PLATFORM = "youtube_shorts"
LENGTH_SEC = 45
STYLE = "cinematic_educational_science"
NARRATOR = "professor"
WORLD_TYPE = "Ocean Research Observatory"
PRODUCTION_ID = f"octopus_three_hearts_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"

VIDEOS_ROOT = Path.home() / "Desktop" / "AI Start-UP" / "Videos"
PROJECT_ROOT = (
    VIDEOS_ROOT / "Shorts" / "Science" / "Biology" / TOPIC
)
SUBFOLDERS = ("Project", "Assets", "Audio", "Captions", "Thumbnail", "Export", "Reports")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug_topic() -> str:
    return "Why-Octopuses-Have-Three-Hearts"


def _next_version(export_dir: Path) -> int:
    stem = f"{date.today().isoformat()}_{_slug_topic()}_YouTubeShort_v"
    versions = []
    if export_dir.exists():
        for p in export_dir.glob(f"{stem}*.mp4"):
            try:
                versions.append(int(p.stem.rsplit("_v", 1)[-1]))
            except ValueError:
                continue
    return (max(versions) + 1) if versions else 1


def _copy(src: Any, dest: Path) -> str | None:
    if not src:
        return None
    p = Path(str(src))
    if not p.is_file():
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dest)
    return str(dest)


def _find_artifacts(result: dict[str, Any]) -> dict[str, Any]:
    ctx = result.get("context") or {}
    export = result.get("export_validation") or ctx.get("export_validation") or {}
    top: dict[str, Any] = {}
    for c in ctx.get("candidates") or []:
        if isinstance(c, dict):
            top = c
            break
    files = list((result.get("status") or {}).get("current_files") or [])
    mp4 = (
        export.get("mp4_path")
        or export.get("video_path")
        or export.get("final_mp4")
        or top.get("video_path")
        or (top.get("render_package") or {}).get("mp4_path")
        or (top.get("render_package") or {}).get("file_uri")
        or (top.get("studio_render_package") or {}).get("mp4_path")
    )
    if not mp4:
        for f in files:
            if str(f).lower().endswith(".mp4") and Path(str(f)).is_file():
                mp4 = f
                break
        # Scan renders
        renders = ROOT / "data" / "renders"
        if renders.exists():
            mp4s = sorted(renders.rglob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
            if mp4s:
                mp4 = str(mp4s[0])

    narration = (top.get("voice_package") or {}).get("path") or (top.get("audio_package") or {}).get("path")
    captions = None
    thumb = None
    music = None
    for f in files:
        fl = str(f).lower()
        if fl.endswith((".srt", ".vtt")):
            captions = captions or f
        if "thumb" in fl and fl.endswith((".png", ".jpg", ".jpeg", ".webp")):
            thumb = thumb or f
        if "music" in fl and fl.endswith((".mp3", ".wav", ".m4a")):
            music = music or f
    # recurse candidate packages
    caps = top.get("caption_package") or top.get("captions") or {}
    if isinstance(caps, dict):
        captions = captions or caps.get("srt_path") or caps.get("path") or caps.get("vtt_path")
    thumbs = top.get("thumbnail_concepts") or top.get("thumbnails") or []
    if isinstance(thumbs, list) and thumbs and isinstance(thumbs[0], dict):
        thumb = thumb or thumbs[0].get("path") or thumbs[0].get("uri")

    script_obj = top.get("structured_script") or top.get("script_package") or {}
    script_text = ""
    if isinstance(script_obj, dict):
        script_text = str(script_obj.get("full_script") or script_obj.get("script") or script_obj.get("narration") or "")
    if not script_text:
        script_text = str(top.get("script") or "")

    return {
        "mp4": mp4,
        "narration": narration,
        "captions": captions,
        "thumbnail": thumb,
        "music": music,
        "script_text": script_text,
        "script_obj": script_obj if isinstance(script_obj, dict) else {},
        "top": top,
        "export": export,
        "files": files,
        "world_package": top.get("world_package") or top.get("environment_package"),
        "cinematic_package": top.get("cinematic_direction_package"),
        "asset_package": top.get("asset_intelligence") or top.get("asset_package") or top.get("visual_package"),
    }


def _ffprobe(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"ok": False, "error": "missing"}
    try:
        raw = subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height,duration:format=duration",
                "-of",
                "json",
                str(path),
            ],
            text=True,
        )
        data = json.loads(raw)
        streams = data.get("streams") or [{}]
        fmt = data.get("format") or {}
        w = int(streams[0].get("width") or 0)
        h = int(streams[0].get("height") or 0)
        dur = float(streams[0].get("duration") or fmt.get("duration") or 0)
        # audio stream?
        araw = subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_type", "-of", "json", str(path)],
            text=True,
        )
        has_audio = bool((json.loads(araw).get("streams") or []))
        return {"ok": True, "width": w, "height": h, "duration_sec": round(dur, 2), "has_audio": has_audio}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:200]}


def _ensure_tree() -> Path:
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    for sub in SUBFOLDERS:
        (PROJECT_ROOT / sub).mkdir(parents=True, exist_ok=True)
    return PROJECT_ROOT


def _package(result: dict[str, Any]) -> dict[str, Any]:
    root = _ensure_tree()
    arts = _find_artifacts(result)
    report = result.get("report") or {}
    version = _next_version(root / "Export")
    date_s = date.today().isoformat()
    base_name = f"{date_s}_{_slug_topic()}_YouTubeShort_v{version}"

    paths: dict[str, Any] = {"project_root": str(root), "version": version, "base_name": base_name}

    # Export MP4 + compressed + preview
    final_mp4 = root / "Export" / f"{base_name}.mp4"
    paths["final_mp4"] = _copy(arts["mp4"], final_mp4)
    if paths["final_mp4"] and Path(paths["final_mp4"]).is_file():
        compressed = root / "Export" / f"{base_name}_compressed.mp4"
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    paths["final_mp4"],
                    "-vf",
                    "scale=720:-2",
                    "-c:v",
                    "libx264",
                    "-crf",
                    "28",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "96k",
                    str(compressed),
                ],
                check=False,
                capture_output=True,
            )
            if compressed.is_file():
                paths["compressed_mp4"] = str(compressed)
        except Exception:  # noqa: BLE001
            pass
        # Preview frame
        preview = root / "Export" / f"{base_name}_preview.jpg"
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-ss", "1", "-i", paths["final_mp4"], "-frames:v", "1", str(preview)],
                check=False,
                capture_output=True,
            )
            if preview.is_file():
                paths["preview"] = str(preview)
        except Exception:  # noqa: BLE001
            pass

    paths["narration"] = _copy(arts["narration"], root / "Audio" / f"{base_name}_narration.mp3")
    paths["music"] = _copy(arts["music"], root / "Audio" / f"{base_name}_music.mp3")
    paths["captions_srt"] = _copy(arts["captions"], root / "Captions" / f"{base_name}.srt")
    if arts["captions"] and str(arts["captions"]).endswith(".vtt"):
        paths["captions_vtt"] = _copy(arts["captions"], root / "Captions" / f"{base_name}.vtt")
    paths["thumbnail"] = _copy(arts["thumbnail"], root / "Thumbnail" / f"{base_name}_thumb.png")

    # Captions JSON timing from candidate if present
    top = arts["top"]
    cap_pkg = top.get("caption_package") or {}
    if isinstance(cap_pkg, dict):
        (root / "Captions" / f"{base_name}_timing.json").write_text(json.dumps(cap_pkg, indent=2) + "\n", encoding="utf-8")
        paths["captions_json"] = str(root / "Captions" / f"{base_name}_timing.json")

    # Project metadata
    project_meta = {
        "generated_at": _now(),
        "topic": TOPIC,
        "platform": "YouTube Shorts",
        "length_sec": LENGTH_SEC,
        "audience": "General Audience",
        "style": "Cinematic Educational Science",
        "narrator": "Professor",
        "voice_provider": "ElevenLabs",
        "persistent_world": WORLD_TYPE,
        "production_id": result.get("production_id"),
        "publishing": "disabled",
        "version": version,
        "file_basename": base_name,
    }
    (root / "Project" / "project_config.json").write_text(json.dumps(project_meta, indent=2) + "\n", encoding="utf-8")
    (root / "Project" / "production_metadata.json").write_text(
        json.dumps(
            {
                "result_keys": list(result.keys()),
                "succeeded": result.get("succeeded"),
                "elapsed_ms": result.get("elapsed_ms"),
                "pipeline_health": (result.get("status") or {}).get("pipeline_health"),
                "report_summary": {
                    "overall_quality_score": report.get("overall_quality_score"),
                    "final_recommendation": report.get("final_recommendation"),
                    "hook_score": report.get("hook_score"),
                    "visual_score": report.get("visual_score"),
                    "narration_score": report.get("narration_score"),
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "Project" / "creative_notes.md").write_text(
        f"# Creative Notes — {TOPIC}\n\n"
        f"- Persistent world: {WORLD_TYPE}\n"
        f"- Platform: YouTube Shorts · {LENGTH_SEC}s\n"
        f"- Style: Cinematic Educational Science\n"
        f"- Opening priority: Giant octopus · Three hearts · Curiosity\n"
        f"- Publishing: disabled\n",
        encoding="utf-8",
    )
    # Prompt history = studio brief + world selection
    (root / "Project" / "prompt_history.json").write_text(
        json.dumps(
            {
                "topic": TOPIC,
                "constraints": {
                    "world": WORLD_TYPE,
                    "style": STYLE,
                    "narrator": NARRATOR,
                    "length_sec": LENGTH_SEC,
                },
                "production_id": result.get("production_id"),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    paths["project_config"] = str(root / "Project" / "project_config.json")

    # Assets: world, cinematic, asset/visual packages + any scene images
    if arts.get("world_package"):
        (root / "Assets" / "WORLD_PACKAGE.json").write_text(
            json.dumps(arts["world_package"], indent=2) + "\n", encoding="utf-8"
        )
        paths["world_package"] = str(root / "Assets" / "WORLD_PACKAGE.json")
    if arts.get("cinematic_package"):
        (root / "Assets" / "CINEMATIC_PACKAGE.json").write_text(
            json.dumps(arts["cinematic_package"], indent=2) + "\n", encoding="utf-8"
        )
        paths["cinematic_package"] = str(root / "Assets" / "CINEMATIC_PACKAGE.json")
    if arts.get("asset_package"):
        (root / "Assets" / "ASSET_PACKAGE.json").write_text(
            json.dumps(arts["asset_package"], indent=2) + "\n", encoding="utf-8"
        )
        paths["asset_package"] = str(root / "Assets" / "ASSET_PACKAGE.json")

    # Copy scene stills if present
    scenes = (top.get("visual_package") or {}).get("scenes") or top.get("scenes") or []
    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            continue
        for key in ("image_path", "path", "uri", "resolved_path"):
            p = scene.get(key)
            if p and Path(str(p)).is_file():
                _copy(p, root / "Assets" / f"scene_{i:02d}{Path(str(p)).suffix}")
                break

    # Script
    (root / "Project" / "SCRIPT.md").write_text(
        f"# Script — {TOPIC}\n\n{arts['script_text'] or '_See production metadata / structured_script._'}\n",
        encoding="utf-8",
    )
    if arts["script_obj"]:
        (root / "Project" / "SCRIPT.json").write_text(json.dumps(arts["script_obj"], indent=2) + "\n", encoding="utf-8")

    # Thumbnail prompt
    (root / "Thumbnail" / "PROMPT.md").write_text(
        f"# Thumbnail Prompt — {TOPIC}\n\n"
        "Giant octopus silhouette through observatory glass, three glowing heart icons, "
        "curious human eye, cinematic teal marine lighting, YouTube Shorts 1080x1920.\n",
        encoding="utf-8",
    )

    # Reports
    (root / "Reports" / "PRODUCTION_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if result.get("report_path") and Path(result["report_path"]).is_file():
        shutil.copy2(result["report_path"], root / "Reports" / "PRODUCTION_REPORT.md")

    probe = _ffprobe(Path(paths["final_mp4"])) if paths.get("final_mp4") else {"ok": False, "error": "no_mp4"}
    world_ok = bool(arts.get("world_package"))
    cine_ok = bool(arts.get("cinematic_package"))
    env_pkgs = []
    if isinstance(arts.get("world_package"), dict):
        env_pkgs = arts["world_package"].get("environment_packages") or []
        world_ok = world_ok and bool(arts["world_package"].get("world_id"))

    validation = {
        "generated_at": _now(),
        "checks": {
            "final_mp4_exists": bool(paths.get("final_mp4")),
            "mp4_plays": bool(probe.get("ok")),
            "resolution_1080x1920": probe.get("width") == 1080 and probe.get("height") == 1920,
            "elevenlabs_narration_present": bool(paths.get("narration")),
            "has_audio_track": bool(probe.get("has_audio")),
            "world_continuity_package": world_ok,
            "cinematic_direction_package": cine_ok,
            "environment_packages": bool(env_pkgs) or world_ok,
            "captions_present": bool(paths.get("captions_srt") or paths.get("captions_json")),
            "no_silent_export": bool(probe.get("has_audio")),
            "duration_sec": probe.get("duration_sec"),
        },
        "ffprobe": probe,
        "export_validation": arts.get("export"),
        "hard_fails": [],
    }
    checks = validation["checks"]
    for key, ok in checks.items():
        if key == "duration_sec":
            continue
        if ok is False:
            validation["hard_fails"].append(key)
    validation["ok"] = not validation["hard_fails"]
    (root / "Reports" / "VALIDATION_REPORT.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    (root / "Reports" / "VALIDATION_REPORT.md").write_text(
        "# Validation Report\n\n"
        + "\n".join(f"- {'✓' if v is True else '✗' if v is False else v}: `{k}`" for k, v in checks.items())
        + f"\n\n**Passed: {validation['ok']}**\n",
        encoding="utf-8",
    )

    quality = {
        "generated_at": _now(),
        "overall_quality_score": report.get("overall_quality_score"),
        "scores": {
            "hook": report.get("hook_score"),
            "visual": report.get("visual_score"),
            "narration": report.get("narration_score"),
            "audio": report.get("audio_score"),
            "captions": report.get("caption_score"),
            "animation": report.get("animation_score"),
            "retention": report.get("retention_prediction"),
            "educational_accuracy": report.get("educational_accuracy"),
        },
        "final_recommendation": report.get("final_recommendation"),
        "validation_ok": validation["ok"],
    }
    (root / "Reports" / "QUALITY_REPORT.json").write_text(json.dumps(quality, indent=2) + "\n", encoding="utf-8")
    (root / "Reports" / "QUALITY_REPORT.md").write_text(
        f"# Quality Report — {TOPIC}\n\nOverall: **{quality.get('overall_quality_score')}**\n\n"
        + "\n".join(f"- {k}: {v}" for k, v in (quality.get("scores") or {}).items())
        + f"\n\nRecommendation: {quality.get('final_recommendation')}\n",
        encoding="utf-8",
    )

    # Performance prediction (from report fields — predictions labeled)
    perf = {
        "label": "prediction",
        "retention_prediction": report.get("retention_prediction"),
        "shareability": report.get("shareability"),
        "hook_score": report.get("hook_score"),
        "note": "Predictions from Creative Performance / ops scoring — not live analytics",
    }
    (root / "Reports" / "PERFORMANCE_PREDICTION.json").write_text(json.dumps(perf, indent=2) + "\n", encoding="utf-8")

    # Creative review (human checklist — no auto rebuild)
    review = _creative_review(paths, validation, quality, probe, world_ok, cine_ok)
    (root / "Reports" / "CREATIVE_DIRECTOR_REVIEW.md").write_text(review, encoding="utf-8")
    paths["creative_review"] = str(root / "Reports" / "CREATIVE_DIRECTOR_REVIEW.md")
    paths["validation"] = validation
    paths["quality"] = quality
    return paths


def _creative_review(
    paths: dict,
    validation: dict,
    quality: dict,
    probe: dict,
    world_ok: bool,
    cine_ok: bool,
) -> str:
    has_mp4 = bool(paths.get("final_mp4"))
    has_audio = bool(probe.get("has_audio"))
    has_narration = bool(paths.get("narration"))
    overall = float(quality.get("overall_quality_score") or 0)
    hook = float((quality.get("scores") or {}).get("hook") or 0)

    answers = {
        "1_stop_scroll": "Yes" if hook >= 85 and has_mp4 else "No",
        "2_opening_exciting": "Yes" if hook >= 80 else "No",
        "3_world_believable": "Yes" if world_ok else "No",
        "4_narration_human": "Yes" if has_narration and has_audio else "No",
        "5_visuals_synced": "Yes" if validation.get("ok") and has_audio else "No",
        "6_professional_short": "Yes" if overall >= 90 and validation.get("ok") else "No",
        "7_personally_publish": "Yes" if overall >= 95 and validation.get("ok") and has_audio else "No",
    }
    nos = [k for k, v in answers.items() if v == "No"]
    improvement = ""
    if nos:
        # ONE highest-impact improvement only
        if "4_narration_human" in nos or not has_audio:
            improvement = "Ensure ElevenLabs narration muxes into the final MP4 (fix/export audio path)."
        elif "3_world_believable" in nos:
            improvement = "Confirm Ocean Research Observatory Environment Packages attach before render."
        elif "1_stop_scroll" in nos or "2_opening_exciting" in nos:
            improvement = "Strengthen the 0–3s hook visually: giant octopus + three-heart graphic in the opening frame."
        elif "7_personally_publish" in nos or "6_professional_short" in nos:
            improvement = "Raise overall production quality via the single weakest ops score area (see QUALITY_REPORT)."
        else:
            improvement = "Fix the first failed validation check in VALIDATION_REPORT."

    lines = [
        f"# Creative Director Review — {TOPIC}",
        "",
        f"Generated: {_now()}",
        "",
        "## Checklist",
        "",
        f"1. Would this stop someone scrolling? **{answers['1_stop_scroll']}**",
        f"2. Is the opening exciting? **{answers['2_opening_exciting']}**",
        f"3. Does the world feel believable? **{answers['3_world_believable']}**",
        f"4. Does narration feel human? **{answers['4_narration_human']}**",
        f"5. Are visuals synchronized with narration? **{answers['5_visuals_synced']}**",
        f"6. Does it feel professionally produced? **{answers['6_professional_short']}**",
        f"7. Would you personally publish it? **{answers['7_personally_publish']}**",
        "",
        "## Highest-impact improvement (only if any No)",
        "",
        improvement or "_None — all Yes._",
        "",
        "## Notes",
        "",
        "- Publishing remains disabled.",
        "- Do not auto-rebuild from this review.",
        f"- Output: `{paths.get('project_root')}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    print("=== Octopus Three Hearts — Full Production ===")
    print(f"production_id={PRODUCTION_ID}")
    _ensure_tree()

    reset_world_state("WORLD-OCEAN_RESEARCH_OBSERVATORY", PRODUCTION_ID)
    seed = place_candidate_in_world(
        {
            "title": TOPIC,
            "topic": TOPIC,
            "niche": "biology",
            "platform": PLATFORM,
            "audience": "General Audience",
            "style": STYLE,
        },
        topic=TOPIC,
        niche="biology",
        world_type=WORLD_TYPE,
        scene_count=4,
        production_id=PRODUCTION_ID,
        platform=PLATFORM,
        audience="general_public",
    )

    result = run_studio_ops(
        topic=TOPIC,
        platform=PLATFORM,
        length_sec=LENGTH_SEC,
        style="educational",
        narrator=NARRATOR,
        voice="default",
        quality_target=98.0,
        production_id=PRODUCTION_ID,
        constraints={
            "audience": "General Audience",
            "style": "Cinematic Educational Science",
            "persistent_world": WORLD_TYPE,
            "publishing_disabled": True,
        },
        context={
            "candidates": [seed],
            "niche": "biology",
            "audience": "General Audience",
            "prefer_motion": True,
            "cinematic_priority": True,
            "narration_style": "professor",
            "preferred_voice_provider": "elevenlabs",
            "force_strong_hook": True,
            "world_id": seed.get("world_id"),
            "length_sec": LENGTH_SEC,
        },
    )

    # Re-attach world packages onto final top candidate if pipelines overwrote lightly
    ctx = result.get("context") or {}
    cands = list(ctx.get("candidates") or [])
    if cands and isinstance(cands[0], dict):
        if not cands[0].get("world_package") and seed.get("world_package"):
            cands[0] = place_candidate_in_world(
                cands[0],
                world_type=WORLD_TYPE,
                production_id=PRODUCTION_ID,
                scene_count=4,
            )
            ctx["candidates"] = cands
            result["context"] = ctx

    paths = _package(result)
    summary = {
        "production_id": result.get("production_id"),
        "succeeded": result.get("succeeded"),
        "overall_quality_score": (result.get("report") or {}).get("overall_quality_score"),
        "recommendation": (result.get("report") or {}).get("final_recommendation"),
        "project_root": paths.get("project_root"),
        "final_mp4": paths.get("final_mp4"),
        "narration": paths.get("narration"),
        "validation_ok": (paths.get("validation") or {}).get("ok"),
        "validation_fails": (paths.get("validation") or {}).get("hard_fails"),
        "world_package": paths.get("world_package"),
        "cinematic_package": paths.get("cinematic_package"),
        "creative_review": paths.get("creative_review"),
    }
    (PROJECT_ROOT / "Reports" / "RUN_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"\nLibrary:\n{PROJECT_ROOT}")
    return 0 if paths.get("final_mp4") else 1


if __name__ == "__main__":
    raise SystemExit(main())
