"""Real production validation — Secrets of Bioluminescence Revealed."""

from __future__ import annotations

import json
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from core.env import load_application_env

load_application_env()

from core.script_models import PIPELINE_STAGE_KEYS
from services.asset_production.executor import run_asset_production
from services.media_production import ffmpeg_available
from services.provider_runtime.config import has_credential

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "data" / "productions" / "_validation"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> dict:
    print("=== PREFLIGHT ===")
    print("ffmpeg", ffmpeg_available())
    for env in [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "ELEVENLABS_API_KEY",
        "RUNWAY_API_KEY",
        "FAL_KEY",
        "BFL_API_KEY",
        "YOUTUBE_ACCESS_TOKEN",
    ]:
        print(f"  {env}: {'SET' if has_credential(env) else 'MISSING'}")

    asset = {
        "asset_id": "val_bioluminescence_001",
        "title": "Secrets of Bioluminescence Revealed",
        "hook": "The ocean is hiding living light — and science just explained why.",
        "description": "A short educational video revealing how and why animals glow in the dark.",
        "hashtags": ["#bioluminescence", "#ocean", "#science", "#shorts"],
        "cta": "Follow for more nature secrets",
        "niche": "science",
        "music_style": "curious ambient underwater",
    }
    project = {
        "name": "Validation — Bioluminescence",
        "model": "gpt-4o-mini",
        "niche": "science",
        "platform": "youtube_shorts",
        "provider": "openai",
    }

    events: list[dict] = []
    t0 = time.perf_counter()

    def on_progress(event: dict) -> None:
        events.append(
            {
                **{k: v for k, v in event.items() if k != "asset"},
                "at": datetime.now(timezone.utc).isoformat(),
            }
        )
        print(
            f"[{event.get('status')}] {event.get('label')}: {event.get('message')} "
            f"(retry={event.get('retry_count')}, t={event.get('execution_time_sec')}s)"
        )

    print("\n=== PRODUCTION START ===")
    try:
        result = run_asset_production(asset, project, on_progress=on_progress, max_images=4)
    except Exception as exc:  # noqa: BLE001
        result = {
            "production_ok": False,
            "production_error": str(exc),
            "traceback": traceback.format_exc(),
            **asset,
        }

    elapsed = round(time.perf_counter() - t0, 2)
    print("\n=== PRODUCTION END ===")
    print("ok", result.get("production_ok"))
    print("error", result.get("production_error"))
    print("elapsed_sec", elapsed)

    prod_dir = ROOT / "data" / "productions" / "val_bioluminescence_001"
    files = (
        sorted(str(p.relative_to(ROOT)) for p in prod_dir.rglob("*") if p.is_file())
        if prod_dir.exists()
        else []
    )
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
    voice = result.get("voice_package") or {}

    warnings: list[str] = []
    broken_refs: list[str] = []
    for rel in files:
        path = ROOT / rel
        if not path.exists():
            broken_refs.append(rel)
        elif path.stat().st_size == 0:
            warnings.append(f"empty file: {rel}")

    mp4 = render.get("mp4_path") or result.get("mp4_path") or ""
    mp4_bytes = 0
    if mp4:
        mp = Path(mp4) if Path(mp4).is_absolute() else ROOT / mp4
        if not mp.exists():
            broken_refs.append(mp4)
            warnings.append("MP4 path recorded but file missing")
        else:
            mp4_bytes = mp.stat().st_size
            if mp4_bytes < 500:
                warnings.append(f"MP4 suspiciously small: {mp4_bytes} bytes")

    if render.get("mock", True):
        warnings.append("Render still marked mock")
    if not result.get("production_ok"):
        warnings.append("production_ok=False")

    working = [r["stage"] for r in stage_rows if r["status"] in {"completed", "skipped"}]
    failed = [r for r in stage_rows if r["status"] == "failed"]
    score = int(round(100 * len(working) / max(1, len(PIPELINE_STAGE_KEYS))))
    if result.get("production_ok") and not render.get("mock") and mp4_bytes > 500:
        score = max(score, 92)

    report = {
        "topic": "Secrets of Bioluminescence Revealed",
        "asset_id": "val_bioluminescence_001",
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "total_runtime_sec": elapsed,
        "production_ok": bool(result.get("production_ok")),
        "production_error": result.get("production_error") or "",
        "preflight": {
            "ffmpeg": ffmpeg_available(),
            "openai": has_credential("OPENAI_API_KEY"),
            "elevenlabs": has_credential("ELEVENLABS_API_KEY"),
            "runway": has_credential("RUNWAY_API_KEY"),
            "fal": has_credential("FAL_KEY"),
            "youtube_oauth": has_credential("YOUTUBE_ACCESS_TOKEN"),
        },
        "stages": stage_rows,
        "failed_stages": failed,
        "working_stages": working,
        "warnings": warnings,
        "broken_references": broken_refs,
        "qc_score": qc.get("score"),
        "qc_passed": qc.get("passed"),
        "qc_checks": qc.get("checks") or [],
        "final_mp4": mp4,
        "mp4_bytes": mp4_bytes,
        "mock_render": bool(render.get("mock", True)),
        "thumbnail": result.get("thumbnail_path") or "",
        "captions": result.get("caption_file") or "",
        "metadata": result.get("export_package") or {},
        "voice_path": voice.get("path") or "",
        "files_created": files,
        "progress_events": events,
        "publish_package": result.get("publish_package") or {},
        "estimated_readiness_percent": score,
    }

    out = REPORT_DIR / "bioluminescence_validation_report.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("report", out)
    print("files", len(files))
    print("mp4", mp4, "bytes", mp4_bytes)
    print("qc", report["qc_score"], report["qc_passed"])
    print("failed", [f["stage"] for f in failed])
    print("readiness", score)
    return report


if __name__ == "__main__":
    main()
