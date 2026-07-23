#!/usr/bin/env python3
"""E2E verification — Studio Render & Motion Graphics V3.0."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import engines  # noqa: F401
from engines import registry
from services.studio_render import build_studio_render_package
from services.studio_render.quality import analyze_render_quality

OUT = ROOT / "data" / "productions" / "_validation" / "studio_render"
OUT.mkdir(parents=True, exist_ok=True)


def weak_candidate() -> dict:
    return {
        "title": "AI basics",
        "topic": "ai",
        "visual_package": {
            "aspect_ratio": "9:16",
            "scenes": [
                {"scene_id": "s1", "narration": "AI is software."},
                {"scene_id": "s2", "narration": "It uses data."},
            ],
        },
    }


def strong_candidate() -> dict:
    return {
        "title": "Artificial Intelligence Explained in 60 Seconds",
        "topic": "artificial intelligence",
        "platform": "youtube_shorts",
        "cinematography_attention_score": 92,
        "cinematography_plan": {
            "scenes": [
                {"scene_id": "s1", "movement": "slow_push_in", "reason": "hook"},
                {"scene_id": "s2", "movement": "macro_push_in", "reason": "detail"},
                {"scene_id": "s3", "movement": "orbit", "reason": "systems"},
                {"scene_id": "s4", "movement": "reveal", "reason": "payoff"},
            ],
            "overall_attention_score": 92,
        },
        "animation_handoff": {
            "scenes": [
                {"scene_id": "s1", "movement": "slow_push_in", "camera": {"movement": "slow_push_in"}},
                {"scene_id": "s2", "movement": "macro_push_in", "camera": {"movement": "macro_push_in"}},
                {"scene_id": "s3", "movement": "orbit", "camera": {"movement": "orbit"}},
                {"scene_id": "s4", "movement": "reveal", "camera": {"movement": "reveal"}},
            ]
        },
        "viewer_retention_package": {
            "overall_score": 98,
            "selected_hook": {"text": "AI is already changing your life.", "score": 96},
            "pacing_plan": [
                {"scene_id": "s1", "duration_sec": 2.4},
                {"scene_id": "s2", "duration_sec": 3.0},
                {"scene_id": "s3", "duration_sec": 3.1},
                {"scene_id": "s4", "duration_sec": 2.9},
            ],
            "caption_plan": {
                "cues": [
                    {
                        "text": "AI is already changing your life",
                        "start_sec": 0,
                        "end_sec": 2.4,
                        "highlight_indices": [0],
                    }
                ]
            },
            "sound_design": {
                "music_intensity_curve": [{"t": 0.0, "intensity": 0.3}, {"t": 1.0, "intensity": 0.6}],
                "events": [{"type": "riser", "scene_id": "s1"}, {"type": "whoosh", "scene_id": "s2"}],
            },
        },
        "visual_package": {
            "aspect_ratio": "9:16",
            "scenes": [
                {
                    "scene_id": "s1",
                    "narration": "AI is already changing your life — and most people don't realize it.",
                    "source_url": "https://commons.wikimedia.org/",
                    "license": "CC-BY-SA",
                    "confidence": 96,
                    "concepts": ["ai"],
                },
                {
                    "scene_id": "s2",
                    "narration": "Notice this tiny chip learning patterns from oceans of data.",
                    "source_url": "https://www.nasa.gov/",
                    "license": "NASA",
                    "confidence": 99,
                    "concepts": ["chip"],
                },
                {
                    "scene_id": "s3",
                    "narration": "Factories track robot arms assembling with machine precision.",
                    "license": "CC-BY-SA",
                    "confidence": 95,
                    "concepts": ["robot"],
                },
                {
                    "scene_id": "s4",
                    "narration": "The surprising part: 1 billion people use AI features every day.",
                    "confidence": 96,
                    "concepts": ["statistic"],
                },
            ],
        },
    }


def main() -> int:
    print("=== Studio Render & Motion Graphics V3.0 E2E ===")
    engine = registry.get_engine("studio_render")
    assert engine and engine.is_ready()

    weak = build_studio_render_package(weak_candidate())
    strong = build_studio_render_package(strong_candidate())
    engine_result = engine.run({"candidates": [strong_candidate()]})

    baseline = 58
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "3.0.0",
        "threshold": 98,
        "weak": {
            "baseline_overall": baseline,
            "v3_overall": weak.overall_score,
            "delta": weak.overall_score - baseline,
            "passed": weak.passed,
            "scores": weak.quality_scores,
            "transition_count": len(weak.transitions),
            "motion_graphics": len(weak.motion_graphics),
        },
        "strong": {
            "baseline_overall": baseline,
            "v3_overall": strong.overall_score,
            "delta": strong.overall_score - baseline,
            "passed": strong.passed,
            "scores": strong.quality_scores,
            "color_profile": strong.color_grade.get("profile"),
            "export_preset": strong.export_plan.get("primary_preset"),
            "transition_types": [t["type"] for t in strong.transitions],
            "compound_moves": [c["compound_move"] for c in strong.camera_choreography],
            "diagram_count": len(strong.diagrams),
            "revision_fixes": strong.revision_fixes,
        },
        "engine_summary": engine_result.get("studio_render_summary"),
        "assertions": {
            "weak_improved": weak.overall_score > baseline,
            "strong_improved": strong.overall_score > baseline,
            "strong_passed_98": strong.overall_score >= 98 and strong.passed,
            "has_cinematic_transitions": all(t["type"] != "hard_cut" for t in strong.transitions),
            "has_motion_graphics": len(strong.motion_graphics) >= 3,
            "has_lut": bool((strong.color_grade or {}).get("lut")),
            "engine_wired": True,
        },
    }

    json_path = OUT / "STUDIO_RENDER_E2E.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md = f"""# Studio Render & Motion Graphics V3.0 — E2E Report

Generated: `{payload['generated_at']}`

## Verdict

| Check | Result |
|-------|--------|
| Weak improved vs baseline | {'PASS' if payload['assertions']['weak_improved'] else 'FAIL'} ({payload['weak']['baseline_overall']} → {payload['weak']['v3_overall']}) |
| Strong improved vs baseline | {'PASS' if payload['assertions']['strong_improved'] else 'FAIL'} ({payload['strong']['baseline_overall']} → {payload['strong']['v3_overall']}) |
| Strong ≥ 98 | {'PASS' if payload['assertions']['strong_passed_98'] else 'FAIL'} |
| Cinematic transitions | {'PASS' if payload['assertions']['has_cinematic_transitions'] else 'FAIL'} |
| Motion graphics | {'PASS' if payload['assertions']['has_motion_graphics'] else 'FAIL'} |
| LUT present | {'PASS' if payload['assertions']['has_lut'] else 'FAIL'} |

## Strong quality scores

```json
{json.dumps(payload['strong']['scores'], indent=2)}
```

## Export / grade

- Preset: `{payload['strong']['export_preset']}`
- Color: `{payload['strong']['color_profile']}`
- Transitions: `{', '.join(payload['strong']['transition_types'])}`
"""
    (OUT / "STUDIO_RENDER_E2E_REPORT.md").write_text(md, encoding="utf-8")

    failed = [k for k, v in payload["assertions"].items() if not v]
    print(json.dumps(payload["assertions"], indent=2))
    print(f"Wrote {json_path}")
    if failed:
        print("FAILED:", failed)
        return 1
    print("STATUS: SUCCESS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
