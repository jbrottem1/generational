"""Validate cinematic visual storytelling on one educational Short."""

from __future__ import annotations

import json
import time
from pathlib import Path

from core.env import load_application_env

load_application_env()

from services.asset_production.executor import run_asset_production
from services.media_production import ffmpeg_available
from services.provider_runtime.config import has_credential

ROOT = Path(__file__).resolve().parents[1]


def main() -> dict:
    assert has_credential("OPENAI_API_KEY"), "OPENAI_API_KEY required"
    assert ffmpeg_available(), "ffmpeg required"

    asset = {
        "asset_id": "viz_crispr_cinematic_001",
        "title": "How CRISPR Edits DNA",
        "hook": "Scientists can cut DNA like text — this is how CRISPR works.",
        "description": "Accurate CRISPR-Cas9 explainer for a general audience.",
        "hashtags": ["#CRISPR", "#science", "#shorts"],
        "niche": "science",
        "music_style": "precise tech ambient",
    }
    project = {
        "name": "Cinematic Visual Validation",
        "model": "gpt-4o-mini",
        "niche": "science",
        "platform": "youtube_shorts",
        "provider": "openai",
    }

    def on_progress(event: dict) -> None:
        print(
            f"[{event.get('status')}] {event.get('label')}: {event.get('message')}",
            flush=True,
        )

    t0 = time.perf_counter()
    result = run_asset_production(asset, project, on_progress=on_progress, max_images=8)
    elapsed = round(time.perf_counter() - t0, 2)

    images = result.get("generated_images") or []
    real = [i for i in images if i.get("path") and not i.get("placeholder")]
    render = result.get("render_package") or {}
    assembly = render.get("assembly") or {}
    qc = result.get("production_qc") or {}
    scenes = result.get("scene_breakdown") or []

    report = {
        "ok": bool(result.get("production_ok") and qc.get("passed")),
        "elapsed_sec": elapsed,
        "scenes": len(scenes),
        "real_images": len(real),
        "visual_count": assembly.get("visual_count"),
        "color_bed": assembly.get("color_bed"),
        "assembly_log": assembly.get("log"),
        "qc_passed": qc.get("passed"),
        "qc_score": qc.get("score"),
        "mp4": render.get("mp4_path"),
        "final_export": result.get("final_export_path"),
        "error": result.get("production_error"),
        "media_types": [s.get("media_type") for s in scenes],
        "motions": [s.get("camera_motion") for s in scenes],
    }
    out = ROOT / "data" / "productions" / "_validation" / "cinematic_visual_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    return report


if __name__ == "__main__":
    main()
