#!/usr/bin/env python3
"""End-to-end visual pipeline repair validation — Why Octopuses Have Three Hearts.

Exercises the EXISTING Image → Scene plan → Render path with hard visual QA.
Does not redesign architecture. Writes VISUAL_PIPELINE_REPORT.md at repo root.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    from engines.image import ImageEngine
    from engines.render.engine import build_render_output
    from services.media_production.visual_qa import validate_scene_visuals, write_visual_pipeline_report

    idea = {
        "title": "Why Octopuses Have Three Hearts",
        "hook": "This animal has three hearts — and two of them stop when it hunts.",
        "script": (
            "This animal has three hearts. Two pump blood through the gills. "
            "The third pushes blood through the body. When an octopus swims, "
            "those gill hearts pause — which is why it usually crawls instead."
        ),
        "visual_package": {
            "scenes": [
                {
                    "scene_number": 1,
                    "purpose": "hook",
                    "emotion": "curiosity",
                    "length_sec": 3.5,
                    "narration": "This animal has three hearts.",
                    "visual_description": "Photorealistic common octopus underwater close-up, cinematic lighting",
                    "ai_image_prompt": "Photorealistic octopus underwater, three-chamber circulatory concept, documentary still",
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
                    "visual_description": "Educational cutaway of octopus circulatory system with gills",
                    "ai_image_prompt": "Realistic octopus anatomy gills and systemic heart educational documentary photo",
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
                    "narration": "When an octopus swims, those gill hearts pause — which is why it usually crawls instead.",
                    "visual_description": "Octopus crawling across reef then brief jet swim",
                    "ai_image_prompt": "Photorealistic octopus crawling on reef then swimming, nature documentary",
                    "camera_motion": "handheld drift",
                    "asset_type": "ai_image",
                    "text_overlay": "Swim = hearts pause",
                    "caption_timing": {"start_sec": 8.5, "end_sec": 13.0},
                },
            ],
            "asset_requests": [],
            "image_prompts": [],
        },
        "audio_package": {
            "scene_cues": [],
            "narration_tracks": [],
        },
    }
    # Derive asset requests from scenes
    for scene in idea["visual_package"]["scenes"]:
        idea["visual_package"]["asset_requests"].append(
            {
                "source": "ai_image",
                "asset_kind": "image",
                "scene_number": scene["scene_number"],
                "duration_sec": scene["length_sec"],
                "prompt": scene["ai_image_prompt"],
                "query": "octopus",
            }
        )
        idea["visual_package"]["image_prompts"].append(
            {"scene_number": scene["scene_number"], "prompt": scene["ai_image_prompt"]}
        )

    print("=== IMAGE ENGINE ===")
    image_out = ImageEngine().run({"ideas": [idea]})
    summary = image_out.get("render_assets_summary") or {}
    print("image_summary=", json.dumps(summary))
    idea = (image_out.get("ideas") or [idea])[0]

    print("=== RENDER PACKAGE ===")
    package = build_render_output(idea, {})
    print("render_status=", package.get("render_status"))
    print("mp4_path=", package.get("mp4_path") or package.get("output_path"))
    print("mock=", package.get("mock"))
    print("warnings=", package.get("render_warnings") or package.get("warnings"))

    plan = package.get("scene_render_plan") or []
    qa = validate_scene_visuals(plan, require_all=True)
    report = write_visual_pipeline_report(
        qa,
        output_path=ROOT / "VISUAL_PIPELINE_REPORT.md",
        title=idea["title"],
        extra={
            "render_status": package.get("render_status"),
            "mp4_path": package.get("mp4_path") or package.get("output_path"),
            "assembly": (package.get("assembly") or package.get("render_result") or {}).get("error")
            if isinstance(package.get("assembly") or package.get("render_result"), dict)
            else "",
            "image_resolved": summary.get("resolved"),
            "image_missing": summary.get("missing"),
        },
    )
    # Also copy under data/outputs for the production folder convention.
    out_dir = ROOT / "data" / "outputs" / "octopus_three_hearts_visual_v2"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "render_package.json").write_text(json.dumps(package, indent=2)[:500000], encoding="utf-8")
    write_visual_pipeline_report(
        qa,
        output_path=out_dir / "VISUAL_PIPELINE_REPORT.md",
        title=idea["title"],
    )

    mp4 = package.get("mp4_path") or ""
    mp4_path = Path(mp4)
    if not mp4_path.is_absolute() and mp4:
        mp4_path = ROOT / mp4
    visual_count = int(((package.get("assembly") or {}) if isinstance(package.get("assembly"), dict) else {}).get("visual_count") or 0)
    # assembly may be nested under render result depending on packager
    if not visual_count:
        rr = package.get("render_result") or {}
        if isinstance(rr, dict):
            visual_count = int(((rr.get("assembly") or {}) if isinstance(rr.get("assembly"), dict) else {}).get("visual_count") or 0)

    ok = bool(qa.get("ok")) and bool(mp4_path and mp4_path.exists() and mp4_path.stat().st_size > 50_000)
    print("=== RESULT ===")
    print("visual_qa_ok=", qa.get("ok"))
    print("report=", report)
    print("mp4_exists=", mp4_path.exists() if mp4 else False)
    print("mp4_bytes=", mp4_path.stat().st_size if mp4 and mp4_path.exists() else 0)
    print("SUCCESS=" + str(ok).lower())
    if not ok:
        print("DIAGNOSTIC: production incomplete — see VISUAL_PIPELINE_REPORT.md")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
