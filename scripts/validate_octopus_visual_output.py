#!/usr/bin/env python3
"""Prove the visual pipeline repair with a brand-new octopus production.

Clears visual caches, renders a new Final.mp4, then audits actual pixels —
not logs. Writes VISUAL_OUTPUT_VALIDATION.md with per-scene screenshots.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
OUT_DIR = ROOT / "data" / "outputs" / f"octopus_visual_validation_{RUN_ID}"
SCREEN_DIR = OUT_DIR / "screenshots"
FINAL_MP4 = OUT_DIR / "Final.mp4"
REPORT_MD = ROOT / "VISUAL_OUTPUT_VALIDATION.md"
BLANK_NAVY = np.array([0x10, 0x18, 0x20], dtype=np.float32)  # lavfi color=c=0x101820


def _clear_caches() -> list[str]:
    cleared: list[str] = []
    targets = [
        ROOT / "data" / "media" / "images",
        ROOT / "data" / "provider_runtime" / "cache",
        ROOT / "data" / "temp",
    ]
    for path in targets:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
            cleared.append(str(path))
        path.mkdir(parents=True, exist_ok=True)
    # Remove prior octopus validation / render folders (not the whole renders tree)
    renders = ROOT / "data" / "renders"
    if renders.exists():
        for child in renders.iterdir():
            if child.is_dir():
                # only wipe dirs that look like prior octopus jobs or QA leftovers
                marker = child / "VISUAL_PIPELINE_REPORT.md"
                mp4s = list(child.glob("*octopus*.mp4"))
                if marker.exists() or mp4s:
                    shutil.rmtree(child, ignore_errors=True)
                    cleared.append(str(child))
    for old in (ROOT / "data" / "outputs").glob("octopus_*"):
        if old.is_dir() and old.name != OUT_DIR.name:
            shutil.rmtree(old, ignore_errors=True)
            cleared.append(str(old))
    return cleared


def _build_idea() -> dict:
    scenes = [
        {
            "scene_number": 1,
            "purpose": "hook",
            "emotion": "curiosity",
            "length_sec": 3.5,
            "narration": "This animal has three hearts.",
            "visual_description": "Photorealistic common octopus underwater close-up, cinematic lighting",
            "ai_image_prompt": (
                "Photorealistic octopus underwater close-up, documentary nature photography, "
                "three hearts concept, no illustration, no cartoon"
            ),
            "camera_motion": "slow push-in",
            "asset_type": "ai_image",
            "text_overlay": "3 hearts",
            "caption_timing": {"start_sec": 0.0, "end_sec": 3.5},
        },
        {
            "scene_number": 2,
            "purpose": "explanation",
            "emotion": "revelatory",
            "length_sec": 5.0,
            "narration": "Two pump blood through the gills. The third pushes blood through the body.",
            "visual_description": "Educational octopus circulatory / gills documentary still",
            "ai_image_prompt": (
                "Realistic octopus anatomy gills and systemic heart educational documentary photo, "
                "photorealistic underwater biology"
            ),
            "camera_motion": "rack focus",
            "asset_type": "ai_image",
            "text_overlay": "Gill hearts + systemic heart",
            "caption_timing": {"start_sec": 3.5, "end_sec": 8.5},
        },
        {
            "scene_number": 3,
            "purpose": "payoff",
            "emotion": "dramatic",
            "length_sec": 4.5,
            "narration": (
                "When an octopus swims, those gill hearts pause — which is why it usually crawls instead."
            ),
            "visual_description": "Octopus crawling across reef then brief jet swim",
            "ai_image_prompt": (
                "Photorealistic octopus crawling on reef then swimming, nature documentary still, "
                "no cartoon, no blank background"
            ),
            "camera_motion": "handheld drift",
            "asset_type": "ai_image",
            "text_overlay": "Swim = hearts pause",
            "caption_timing": {"start_sec": 8.5, "end_sec": 13.0},
        },
    ]
    idea = {
        "title": "Why Octopuses Have Three Hearts",
        "hook": "This animal has three hearts — and two of them stop when it hunts.",
        "script": " ".join(s["narration"] for s in scenes),
        "visual_package": {
            "scenes": scenes,
            "asset_requests": [
                {
                    "source": "ai_image",
                    "asset_kind": "image",
                    "scene_number": s["scene_number"],
                    "duration_sec": s["length_sec"],
                    "prompt": s["ai_image_prompt"],
                    "query": "octopus",
                }
                for s in scenes
            ],
            "image_prompts": [
                {"scene_number": s["scene_number"], "prompt": s["ai_image_prompt"]} for s in scenes
            ],
        },
        "audio_package": {"scene_cues": [], "narration_tracks": []},
    }
    return idea


def _run_production(idea: dict) -> dict:
    from engines.image import ImageEngine
    from engines.render.engine import build_render_output
    from engines.render.renderer import MockRenderer

    image_out = ImageEngine().run({"ideas": [idea]})
    idea = (image_out.get("ideas") or [idea])[0]
    package = build_render_output(idea, {"run_id": RUN_ID, "force_new": True})

    # Force a dedicated Final.mp4 path (do not reuse prior render path).
    timeline = package.get("timeline") or {}
    scene_plan = package.get("scene_render_plan") or []
    captions = package.get("caption_render_plan") or {"segments": []}
    audio = package.get("audio_mix_plan") or {"tracks": {}}
    missing = package.get("missing_assets") or []

    render = MockRenderer().render(
        title=f"{idea['title']} Validation {RUN_ID}",
        timeline=timeline,
        scene_render_plan=scene_plan,
        caption_render_plan=captions,
        audio_mix_plan=audio,
        missing_assets=missing,
        warnings=[],
        output_format=package.get("output_format"),
    )

    # Copy successful mp4 to Final.mp4 (canonical proof artifact)
    src = Path(str(render.get("mp4_path") or render.get("output_path") or ""))
    if not src.is_absolute() and str(src):
        src = ROOT / src
    if src.exists() and src.stat().st_size > 0:
        shutil.copy2(src, FINAL_MP4)

    return {
        "idea": idea,
        "image_summary": image_out.get("render_assets_summary") or {},
        "package": package,
        "render": render,
        "scene_render_plan": scene_plan,
        "timeline": timeline,
        "final_mp4": str(FINAL_MP4) if FINAL_MP4.exists() else "",
        "source_mp4": str(src) if src.exists() else "",
    }


def _probe(path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration,nb_frames,avg_frame_rate",
        "-show_entries", "format=duration,size",
        "-of", "json",
        str(path),
    ]
    # ffprobe may not be in venv; use system
    for bin_name in ("ffprobe", "/usr/bin/ffprobe"):
        try:
            proc = subprocess.run([bin_name, *cmd[1:]], capture_output=True, text=True, check=False)
            if proc.returncode == 0 and proc.stdout.strip():
                return json.loads(proc.stdout)
        except FileNotFoundError:
            continue
    # fallback via ffmpeg
    return {}


def _extract_frame(mp4: Path, t_sec: float, out: Path) -> Path | None:
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-ss", f"{max(0.0, t_sec):.3f}",
        "-i", str(mp4),
        "-frames:v", "1",
        "-q:v", "2",
        str(out),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not out.exists() or out.stat().st_size < 1000:
        return None
    return out


def _analyze_frame(path: Path) -> dict:
    img = Image.open(path).convert("RGB")
    arr = np.asarray(img, dtype=np.float32)
    h, w, _ = arr.shape
    pixels = arr.reshape(-1, 3)
    mean = pixels.mean(axis=0)
    std = pixels.std(axis=0)
    # Fraction of pixels near mean (solid / near-solid)
    near_mean = np.linalg.norm(pixels - mean, axis=1) < 12.0
    solid_frac = float(near_mean.mean())
    # Fraction near historic blank navy
    near_navy = np.linalg.norm(pixels - BLANK_NAVY, axis=1) < 18.0
    navy_frac = float(near_navy.mean())
    # Unique quantized colors (coarse)
    q = (pixels / 16).astype(np.int32)
    unique = len({(int(a), int(b), int(c)) for a, b, c in q[:: max(1, len(q)//20000)]})
    is_blank = solid_frac >= 0.985 or navy_frac >= 0.90 or (float(std.mean()) < 3.0 and solid_frac >= 0.95)
    # Gradient placeholder heuristic: low unique colors + vertical/horizontal smooth ramp
    is_placeholder_gradient = unique <= 40 and 0.70 <= solid_frac < 0.985 and float(std.mean()) < 25
    return {
        "width": w,
        "height": h,
        "mean_rgb": [round(float(x), 1) for x in mean],
        "std_rgb": [round(float(x), 1) for x in std],
        "solid_fraction": round(solid_frac, 4),
        "navy_blank_fraction": round(navy_frac, 4),
        "unique_quantized_colors": unique,
        "is_blank": bool(is_blank),
        "is_placeholder_gradient": bool(is_placeholder_gradient),
        "bytes": path.stat().st_size,
    }


def _sample_blank_frames(mp4: Path, duration: float, fps_samples: int = 8) -> dict:
    """Sample frames across the whole video; count blanks/placeholders."""
    times = [duration * (i + 0.5) / fps_samples for i in range(fps_samples)]
    blank = 0
    placeholder = 0
    details = []
    for i, t in enumerate(times):
        frame = SCREEN_DIR / f"sample_{i:02d}_t{t:.2f}.png"
        got = _extract_frame(mp4, t, frame)
        if not got:
            blank += 1
            details.append({"t": t, "status": "extract_failed", "is_blank": True})
            continue
        stats = _analyze_frame(got)
        if stats["is_blank"]:
            blank += 1
        if stats["is_placeholder_gradient"]:
            placeholder += 1
        details.append({"t": t, "path": str(got.relative_to(ROOT)), **stats})
    return {"blank_frames": blank, "placeholder_frames": placeholder, "samples": details}


def _resolve_asset_path(asset: dict) -> Path | None:
    from services.media_production.persistence import absolute_media_path

    if not isinstance(asset, dict):
        return None
    if asset.get("placeholder") and not asset.get("approved_fallback_visual"):
        return None
    for key in ("path", "uri", "local_path", "image_path"):
        raw = str(asset.get(key) or "")
        if not raw or raw.startswith(("mock://", "runtime://")):
            continue
        p = absolute_media_path(raw)
        if p is None:
            cand = Path(raw)
            if not cand.is_absolute():
                cand = ROOT / raw
            p = cand if cand.exists() else None
        if p and p.exists() and p.stat().st_size >= 1024:
            return p
    return None


def audit(bundle: dict) -> dict:
    SCREEN_DIR.mkdir(parents=True, exist_ok=True)
    plan = bundle["scene_render_plan"]
    timeline = bundle["timeline"]
    segments = timeline.get("segments") or []
    seg_by_scene = {}
    for seg in segments:
        sid = seg.get("scene_id") or seg.get("scene_number")
        seg_by_scene[sid] = seg

    mp4 = Path(bundle["final_mp4"]) if bundle.get("final_mp4") else None
    if not mp4 or not mp4.exists():
        return {
            "ok": False,
            "overall_score": 0,
            "error": "Final.mp4 was not produced",
            "scenes": [],
            "blank_frames_detected": 0,
            "placeholder_frames_detected": 0,
            "missing_assets": len(plan),
        }

    probe = _probe(mp4)
    streams = (probe.get("streams") or [{}])[0]
    duration = float(
        streams.get("duration")
        or (probe.get("format") or {}).get("duration")
        or timeline.get("total_duration_sec")
        or 0
    )
    global_samples = _sample_blank_frames(mp4, duration or 13.0, fps_samples=12)

    scene_rows = []
    missing_assets = 0
    scene_fails = 0
    for idx, scene in enumerate(plan):
        sid = scene.get("scene_id") or scene.get("scene_number") or idx + 1
        asset = scene.get("resolved_asset") or {}
        asset_path = _resolve_asset_path(asset)
        seg = seg_by_scene.get(sid) or {}
        start = float(seg.get("start_time") or scene.get("caption_timing", {}).get("start_sec") or 0)
        end = float(seg.get("end_time") or scene.get("caption_timing", {}).get("end_sec") or start + float(scene.get("duration_sec") or 3))
        dur = max(0.1, end - start)
        mid = start + dur / 2.0

        shot = SCREEN_DIR / f"scene_{int(sid):02d}_mid.png"
        start_shot = SCREEN_DIR / f"scene_{int(sid):02d}_start.png"
        end_shot = SCREEN_DIR / f"scene_{int(sid):02d}_end.png"
        mid_ok = _extract_frame(mp4, mid, shot)
        start_ok = _extract_frame(mp4, start + min(0.15, dur * 0.1), start_shot)
        end_ok = _extract_frame(mp4, max(start, end - min(0.15, dur * 0.1)), end_shot)

        frame_stats = _analyze_frame(mid_ok) if mid_ok else {"is_blank": True, "is_placeholder_gradient": False}
        start_stats = _analyze_frame(start_ok) if start_ok else {"is_blank": True}
        end_stats = _analyze_frame(end_ok) if end_ok else {"is_blank": True}

        reasons = []
        if asset_path is None:
            missing_assets += 1
            reasons.append("missing_or_invalid_asset_file")
        if asset.get("placeholder") and not asset.get("approved_fallback_visual"):
            reasons.append("placeholder_asset_flag")
        if not mid_ok:
            reasons.append("screenshot_extract_failed")
        if frame_stats.get("is_blank") or start_stats.get("is_blank") or end_stats.get("is_blank"):
            reasons.append("blank_colored_background_detected")
        if frame_stats.get("is_placeholder_gradient"):
            reasons.append("placeholder_gradient_frame_detected")
        if dur < 0.8:
            reasons.append("scene_duration_too_short")
        narration = (scene.get("narration") or "").strip()
        if not narration:
            reasons.append("missing_narration")

        # Timeline must reference this scene and renderer must have used a real file
        timeline_ok = sid in seg_by_scene or any(
            (s.get("scene_id") == sid or s.get("scene_number") == sid) for s in segments
        )
        if not timeline_ok and segments:
            # segment ids may be ints while scene_id is int — already handled; if empty segments, fail
            reasons.append("timeline_missing_scene")
        if not timeline_ok and not segments:
            reasons.append("timeline_empty")

        passed = not reasons
        if not passed:
            scene_fails += 1

        scene_rows.append(
            {
                "scene_number": sid,
                "narration": narration,
                "expected_visual": scene.get("image_prompt") or scene.get("visual_description") or "",
                "asset_path": str(asset_path) if asset_path else str(asset.get("path") or ""),
                "asset_provider": asset.get("provider") or asset.get("source") or "",
                "asset_bytes": asset_path.stat().st_size if asset_path else 0,
                "placeholder_flag": bool(asset.get("placeholder")),
                "approved_fallback": bool(asset.get("approved_fallback_visual")),
                "timeline_start_sec": start,
                "timeline_end_sec": end,
                "timeline_duration_sec": round(dur, 3),
                "screenshot_mid": str(shot.relative_to(ROOT)) if mid_ok else "",
                "screenshot_start": str(start_shot.relative_to(ROOT)) if start_ok else "",
                "screenshot_end": str(end_shot.relative_to(ROOT)) if end_ok else "",
                "frame_stats": frame_stats,
                "result": "PASS" if passed else "FAIL",
                "fail_reasons": reasons,
            }
        )

    # Score
    score = 100
    score -= scene_fails * 25
    score -= global_samples["blank_frames"] * 5
    score -= global_samples["placeholder_frames"] * 5
    score -= missing_assets * 15
    if not mp4.exists() or mp4.stat().st_size < 50_000:
        score = 0
    score = max(0, min(100, score))

    ok = (
        scene_fails == 0
        and missing_assets == 0
        and global_samples["blank_frames"] == 0
        and global_samples["placeholder_frames"] == 0
        and mp4.exists()
        and mp4.stat().st_size >= 50_000
        and duration >= 5.0
    )

    return {
        "ok": ok,
        "overall_score": score,
        "run_id": RUN_ID,
        "final_mp4": str(mp4.relative_to(ROOT)),
        "final_mp4_bytes": mp4.stat().st_size,
        "duration_sec": duration,
        "probe": {"width": streams.get("width"), "height": streams.get("height")},
        "scenes": scene_rows,
        "blank_frames_detected": global_samples["blank_frames"],
        "placeholder_frames_detected": global_samples["placeholder_frames"],
        "missing_assets": missing_assets,
        "global_samples": global_samples,
        "render_status": (bundle.get("render") or {}).get("render_status"),
        "assembly": (bundle.get("render") or {}).get("assembly") or {},
        "first_fail": next((r for r in scene_rows if r["result"] == "FAIL"), None),
    }


def write_report(audit_result: dict, cleared: list[str], bundle: dict) -> str:
    lines: list[str] = []
    lines.append("# VISUAL OUTPUT VALIDATION")
    lines.append("")
    lines.append(f"- Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"- Run ID: `{audit_result.get('run_id')}`")
    lines.append(f"- Topic: Why Octopuses Have Three Hearts")
    lines.append(f"- Final MP4: `{audit_result.get('final_mp4')}`")
    lines.append(f"- Final MP4 bytes: {audit_result.get('final_mp4_bytes')}")
    lines.append(f"- Duration: {audit_result.get('duration_sec')}s")
    lines.append(f"- Probe: {audit_result.get('probe')}")
    lines.append(f"- Overall production score: **{audit_result.get('overall_score')}/100**")
    lines.append(f"- Overall result: **{'PASS' if audit_result.get('ok') else 'FAIL'}**")
    lines.append("")
    lines.append("## Cache clearing")
    lines.append("")
    if cleared:
        for c in cleared:
            lines.append(f"- Cleared `{c}`")
    else:
        lines.append("- (nothing pre-existing to clear)")
    lines.append("")
    lines.append("## Aggregate counters")
    lines.append("")
    lines.append(f"- Blank frames detected: **{audit_result.get('blank_frames_detected')}**")
    lines.append(f"- Placeholder frames detected: **{audit_result.get('placeholder_frames_detected')}**")
    lines.append(f"- Missing assets: **{audit_result.get('missing_assets')}**")
    lines.append(f"- Render status: `{audit_result.get('render_status')}`")
    asm = audit_result.get("assembly") or {}
    lines.append(f"- Assembly visual_count: `{asm.get('visual_count')}`")
    lines.append(f"- Assembly log: `{asm.get('log')}`")
    lines.append("")

    if not audit_result.get("ok") and audit_result.get("first_fail"):
        ff = audit_result["first_fail"]
        lines.append("## STOP — first failing scene")
        lines.append("")
        lines.append(f"- Scene: **{ff.get('scene_number')}**")
        lines.append(f"- Reasons: `{', '.join(ff.get('fail_reasons') or [])}`")
        lines.append(f"- Asset path: `{ff.get('asset_path')}`")
        lines.append(f"- Narration: {ff.get('narration')}")
        lines.append("")

    lines.append("## Scene-by-scene audit")
    lines.append("")
    for row in audit_result.get("scenes") or []:
        lines.append(f"### Scene {row['scene_number']} — {row['result']}")
        lines.append("")
        lines.append(f"- Narration: {row.get('narration')}")
        lines.append(f"- Expected visual: {row.get('expected_visual')}")
        lines.append(f"- Asset path: `{row.get('asset_path')}`")
        lines.append(f"- Asset provider: `{row.get('asset_provider')}`")
        lines.append(f"- Asset bytes: {row.get('asset_bytes')}")
        lines.append(f"- Placeholder flag: {row.get('placeholder_flag')}")
        lines.append(f"- Approved fallback: {row.get('approved_fallback')}")
        lines.append(
            f"- Timeline: {row.get('timeline_start_sec')}s → {row.get('timeline_end_sec')}s "
            f"(duration {row.get('timeline_duration_sec')}s)"
        )
        lines.append(f"- Mid-frame stats: `{row.get('frame_stats')}`")
        if row.get("fail_reasons"):
            lines.append(f"- Fail reasons: `{', '.join(row['fail_reasons'])}`")
        lines.append("")
        if row.get("screenshot_mid"):
            lines.append(f"![Scene {row['scene_number']} mid]({row['screenshot_mid']})")
            lines.append("")
        if row.get("screenshot_start"):
            lines.append(f"![Scene {row['scene_number']} start]({row['screenshot_start']})")
            lines.append("")
        if row.get("screenshot_end"):
            lines.append(f"![Scene {row['scene_number']} end]({row['screenshot_end']})")
            lines.append("")

    lines.append("## Global frame samples")
    lines.append("")
    lines.append("| t (s) | blank | placeholder | solid_frac | navy_frac | screenshot |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for s in (audit_result.get("global_samples") or {}).get("samples") or []:
        lines.append(
            f"| {s.get('t'):.2f} | {s.get('is_blank')} | {s.get('is_placeholder_gradient')} | "
            f"{s.get('solid_fraction')} | {s.get('navy_blank_fraction')} | `{s.get('path','')}` |"
        )
    lines.append("")
    lines.append("## Definition of success")
    lines.append("")
    lines.append("Success requires the **rendered Final.mp4** to contain continuous photographic")
    lines.append("visual storytelling for every narrated scene. Pipeline completion alone is insufficient.")
    lines.append("")

    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # Also copy into run folder
    (OUT_DIR / "VISUAL_OUTPUT_VALIDATION.md").write_text(REPORT_MD.read_text(encoding="utf-8"), encoding="utf-8")
    (OUT_DIR / "audit.json").write_text(json.dumps(audit_result, indent=2, default=str), encoding="utf-8")
    (OUT_DIR / "bundle_meta.json").write_text(
        json.dumps(
            {
                "run_id": RUN_ID,
                "image_summary": bundle.get("image_summary"),
                "render_status": (bundle.get("render") or {}).get("render_status"),
                "final_mp4": bundle.get("final_mp4"),
                "source_mp4": bundle.get("source_mp4"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(REPORT_MD)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SCREEN_DIR.mkdir(parents=True, exist_ok=True)

    print("=== CLEAR CACHES ===")
    cleared = _clear_caches()
    for c in cleared:
        print("cleared", c)

    print("=== PRODUCE ===")
    idea = _build_idea()
    bundle = _run_production(idea)
    print("image_summary", bundle.get("image_summary"))
    print("render_status", (bundle.get("render") or {}).get("render_status"))
    print("final_mp4", bundle.get("final_mp4"))
    print("source_mp4", bundle.get("source_mp4"))

    print("=== AUDIT PIXELS ===")
    result = audit(bundle)
    report = write_report(result, cleared, bundle)
    print("report", report)
    print("overall_score", result.get("overall_score"))
    print("blank_frames", result.get("blank_frames_detected"))
    print("placeholder_frames", result.get("placeholder_frames_detected"))
    print("missing_assets", result.get("missing_assets"))
    print("SUCCESS=" + str(bool(result.get("ok"))).lower())

    if not result.get("ok"):
        ff = result.get("first_fail") or {}
        print("FIRST_FAIL_SCENE", ff.get("scene_number"))
        print("FIRST_FAIL_REASONS", ff.get("fail_reasons"))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
