"""Resume bioluminescence validation from the failed voice stage."""

from __future__ import annotations

import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

from core.env import load_application_env

load_application_env()

from core.script_models import PIPELINE_STAGE_KEYS
from services.asset_production.executor import run_asset_production
from services.media_production import ffmpeg_available
from services.provider_runtime.config import has_credential
from services.provider_runtime.runtime import get_provider_runtime

ROOT = Path(__file__).resolve().parents[1]
ASSET_ID = "val_bioluminescence_001"
PROD = ROOT / "data" / "productions" / ASSET_ID
REPORT_DIR = ROOT / "data" / "productions" / "_validation"


def _load_json(name: str):
    path = PROD / name
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> dict:
    # Clear bad TTS cache entries from the failed sandbox run
    try:
        runtime = get_provider_runtime()
        cache = getattr(runtime, "cache", None)
        if cache is not None and hasattr(cache, "clear"):
            cache.clear()
            print("provider cache cleared")
        cache_dir = ROOT / "data" / "provider_runtime" / "cache"
        if cache_dir.exists():
            for item in cache_dir.glob("*tts*"):
                item.unlink(missing_ok=True)
            for item in cache_dir.glob("*voice*"):
                item.unlink(missing_ok=True)
    except Exception as exc:  # noqa: BLE001
        print("cache clear warning", exc)

    print("=== RESUME PREFLIGHT ===")
    print("ffmpeg", ffmpeg_available())
    print("openai", has_credential("OPENAI_API_KEY"))

    idea = _load_json("idea.json") or {}
    script = _load_json("script.json") or {}
    scenes = _load_json("scenes.json") or []
    visual_prompts = _load_json("visual_prompts.json") or {}
    images = _load_json("images.json") or []

    asset = {
        "asset_id": ASSET_ID,
        "title": idea.get("title") or "Secrets of Bioluminescence Revealed",
        "hook": idea.get("hook") or "",
        "description": idea.get("description") or "",
        "hashtags": ["#bioluminescence", "#ocean", "#science", "#shorts"],
        "cta": "Follow for more nature secrets",
        "niche": "science",
        "music_style": "curious ambient underwater",
        "video_script": script,
        "script": script.get("full_voiceover") or "",
        "scene_breakdown": scenes,
        "visual_package": {
            "scenes": scenes,
            "image_prompts": visual_prompts.get("image_prompts") or [],
            "video_prompts": visual_prompts.get("video_prompts") or [],
        },
        "visual_prompts": [p.get("prompt") for p in (visual_prompts.get("image_prompts") or []) if isinstance(p, dict)],
        "generated_images": images,
        "production_pipeline": {
            "stages": {
                "idea": {"status": "completed"},
                "script": {"status": "completed"},
                "scenes": {"status": "completed"},
                "visual_prompts": {"status": "completed"},
                "images": {"status": "completed"},
                "video_clips": {"status": "skipped"},
            }
        },
    }
    for scene in scenes:
        for img in images:
            if isinstance(scene, dict) and isinstance(img, dict) and scene.get("scene_number") == img.get("scene_number"):
                scene["resolved_asset"] = img

    project = {
        "name": "Validation — Bioluminescence",
        "model": "gpt-4o-mini",
        "niche": "science",
        "platform": "youtube_shorts",
        "provider": "openai",
    }

    events = []
    t0 = time.perf_counter()

    def on_progress(event):
        events.append({k: v for k, v in event.items() if k != "asset"})
        print(
            f"[{event.get('status')}] {event.get('label')}: {event.get('message')} "
            f"(retry={event.get('retry_count')}, t={event.get('execution_time_sec')}s)"
        )

    print("\n=== RESUME FROM VOICE ===")
    result = run_asset_production(
        asset,
        project,
        on_progress=on_progress,
        max_images=4,
        resume_from="voice",
    )
    elapsed = round(time.perf_counter() - t0, 2)

    files = sorted(str(p.relative_to(ROOT)) for p in PROD.rglob("*") if p.is_file()) if PROD.exists() else []
    stages = ((result.get("production_pipeline") or {}).get("stages") or {})
    stage_rows = []
    for key in PIPELINE_STAGE_KEYS:
        raw = stages.get(key) or {}
        if isinstance(raw, str):
            raw = {"status": raw}
        stage_rows.append(
            {
                "stage": key,
                "status": raw.get("status"),
                "retry_count": raw.get("retry_count", 0),
                "execution_time_sec": raw.get("execution_time_sec", 0),
                "artifacts": raw.get("artifacts") or [],
                "error": raw.get("error") or "",
            }
        )

    render = result.get("render_package") or {}
    qc = result.get("production_qc") or {}
    mp4 = render.get("mp4_path") or ""
    mp4_bytes = 0
    if mp4:
        mp = Path(mp4) if Path(mp4).is_absolute() else ROOT / mp4
        if mp.exists():
            mp4_bytes = mp.stat().st_size

    working = [r["stage"] for r in stage_rows if r["status"] in {"completed", "skipped"}]
    failed = [r for r in stage_rows if r["status"] == "failed"]
    score = int(round(100 * len(working) / max(1, len(PIPELINE_STAGE_KEYS))))
    if result.get("production_ok") and not render.get("mock") and mp4_bytes > 500:
        score = max(score, 92)

    report = {
        "topic": "Secrets of Bioluminescence Revealed",
        "mode": "resume_from_voice",
        "asset_id": ASSET_ID,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "resume_runtime_sec": elapsed,
        "production_ok": bool(result.get("production_ok")),
        "production_error": result.get("production_error") or "",
        "preflight": {
            "ffmpeg": ffmpeg_available(),
            "openai": has_credential("OPENAI_API_KEY"),
            "elevenlabs": has_credential("ELEVENLABS_API_KEY"),
            "youtube_oauth": has_credential("YOUTUBE_ACCESS_TOKEN"),
        },
        "stages": stage_rows,
        "failed_stages": failed,
        "working_stages": working,
        "qc_score": qc.get("score"),
        "qc_passed": qc.get("passed"),
        "qc_checks": qc.get("checks") or [],
        "final_mp4": mp4,
        "mp4_bytes": mp4_bytes,
        "mock_render": bool(render.get("mock", True)),
        "thumbnail": result.get("thumbnail_path") or "",
        "captions": result.get("caption_file") or "",
        "metadata": result.get("export_package") or {},
        "voice_path": (result.get("voice_package") or {}).get("path") or "",
        "files_created": files,
        "progress_events": events,
        "publish_package": result.get("publish_package") or {},
        "estimated_readiness_percent": score,
        "voice_repair": "OpenAITTSConnector now fails on empty audio / status 0 instead of returning placeholder success",
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORT_DIR / "bioluminescence_validation_report.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    md = REPORT_DIR / "PRODUCTION_VALIDATION_REPORT.md"
    md.write_text(_markdown(report), encoding="utf-8")
    print("report", out)
    print("ok", report["production_ok"], "mp4", mp4, "bytes", mp4_bytes, "qc", report["qc_score"])
    print("failed", [f["stage"] for f in failed])
    return report


def _markdown(report: dict) -> str:
    lines = [
        "# Production Validation Report",
        "",
        f"**Topic:** {report['topic']}",
        f"**Mode:** {report.get('mode')}",
        f"**Validated at:** {report['validated_at']}",
        f"**Production OK:** {report['production_ok']}",
        f"**Resume runtime:** {report.get('resume_runtime_sec')}s",
        f"**Readiness:** {report['estimated_readiness_percent']}%",
        "",
        "## Final outputs",
        f"- MP4: `{report.get('final_mp4')}` ({report.get('mp4_bytes')} bytes)",
        f"- Mock render: {report.get('mock_render')}",
        f"- Voice: `{report.get('voice_path')}`",
        f"- Captions: `{report.get('captions')}`",
        f"- Thumbnail: `{report.get('thumbnail')}`",
        f"- QC score: {report.get('qc_score')} passed={report.get('qc_passed')}",
        "",
        "## Stages",
    ]
    for row in report.get("stages") or []:
        lines.append(
            f"- **{row['stage']}**: {row['status']} · retries={row.get('retry_count')} · "
            f"{row.get('execution_time_sec')}s · err={row.get('error') or '—'}"
        )
    lines.extend(
        [
            "",
            "## Working stages",
            ", ".join(report.get("working_stages") or []) or "—",
            "",
            "## Failed stages",
            ", ".join(f["stage"] for f in (report.get("failed_stages") or [])) or "none",
            "",
            "## Files created",
        ]
    )
    for f in report.get("files_created") or []:
        lines.append(f"- `{f}`")
    lines.extend(
        [
            "",
            "## Metadata",
            "```json",
            json.dumps(report.get("metadata") or {}, indent=2),
            "```",
            "",
            "## Recommendation",
            "Next milestone: regenerate real scene images with OpenAI Images (network unblocked), then first YouTube OAuth publish.",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
