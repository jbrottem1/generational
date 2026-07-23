#!/usr/bin/env python3
"""E2E verification — Viewer Retention & Cinematic Excellence V2.0.

Proves measurable improvements vs a weak baseline candidate and writes a
validation report under data/productions/_validation/viewer_retention/.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import engines  # noqa: F401
from engines import registry
from services.viewer_retention import build_excellence_package
from services.viewer_retention.excellence import _baseline_scores

OUT = ROOT / "data" / "productions" / "_validation" / "viewer_retention"
OUT.mkdir(parents=True, exist_ok=True)


def weak_candidate() -> dict:
    return {
        "title": "AI basics",
        "topic": "artificial intelligence",
        "hook": "AI is software.",
        "psychology": {"viral_score": 48, "dimensions": {"first_3_second_hook": 40, "retention_potential": 45}},
        "script_retention": {"retention_score": 48},
        "visual_package": {
            "aspect_ratio": "9:16",
            "scenes": [
                {"scene_id": "s1", "narration": "AI is software that learns.", "expected_attention_score": 45},
                {"scene_id": "s2", "narration": "It uses data.", "expected_attention_score": 40},
                {"scene_id": "s3", "narration": "It helps people.", "expected_attention_score": 42},
            ],
        },
    }


def strong_candidate() -> dict:
    return {
        "title": "Artificial Intelligence Explained in 60 Seconds",
        "topic": "artificial intelligence",
        "research": {"statistics": ["Over 1 billion people use AI features daily."]},
        "psychology": {
            "viral_score": 82,
            "dimensions": {
                "first_3_second_hook": 78,
                "curiosity_gap": 84,
                "retention_potential": 80,
                "emotional_intensity": 74,
                "information_density": 86,
                "share_likelihood": 72,
            },
        },
        "script_retention": {"retention_score": 64},
        "visual_package": {
            "aspect_ratio": "9:16",
            "scenes": [
                {
                    "scene_id": "s1",
                    "narration": "AI is already changing your life — and most people don't realize it.",
                    "expected_attention_score": 82,
                    "source_url": "https://commons.wikimedia.org/",
                    "license": "CC-BY-SA",
                    "confidence": 96,
                    "concepts": ["smartphone", "ai"],
                },
                {
                    "scene_id": "s2",
                    "narration": "Notice this tiny chip learning patterns from oceans of data.",
                    "expected_attention_score": 80,
                    "source_url": "https://www.nasa.gov/",
                    "license": "NASA",
                    "confidence": 99,
                    "concepts": ["chip", "nasa"],
                },
                {
                    "scene_id": "s3",
                    "narration": "Factories track robot arms assembling with machine precision.",
                    "expected_attention_score": 76,
                    "license": "CC-BY-SA",
                    "confidence": 95,
                    "concepts": ["robot"],
                },
                {
                    "scene_id": "s4",
                    "narration": "Language models train on supercomputers and rewrite how we write.",
                    "expected_attention_score": 78,
                    "confidence": 94,
                    "concepts": ["language"],
                },
                {
                    "scene_id": "s5",
                    "narration": "The surprising part: the core ideas are older than you think.",
                    "expected_attention_score": 84,
                    "confidence": 97,
                    "concepts": ["history"],
                },
            ],
        },
        "cinematography_plan": {
            "scenes": [
                {"scene_id": "s1", "movement": "slow_push_in", "reason": "hook"},
                {"scene_id": "s2", "movement": "macro_push_in", "reason": "detail"},
            ],
            "overall_attention_score": 90,
        },
        "cinematography_attention_score": 90,
        "seo": {"title": "AI Explained Fast", "tags": ["ai", "shorts"], "score": 92},
    }


def main() -> int:
    print("=== Viewer Retention & Cinematic Excellence V2.0 E2E ===")
    engine = registry.get_engine("viewer_retention")
    assert engine and engine.is_ready()

    weak = weak_candidate()
    strong = strong_candidate()
    weak_baseline = _baseline_scores(weak)
    strong_baseline = _baseline_scores(strong)

    weak_report = build_excellence_package(weak)
    strong_report = build_excellence_package(strong)
    engine_result = engine.run({"candidates": [strong_candidate()], "subject": "AI"})

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
        "threshold": 98,
        "weak": {
            "baseline_overall": weak_baseline["overall"],
            "v2_overall": weak_report.overall_score,
            "delta": weak_report.overall_score - weak_baseline["overall"],
            "passed": weak_report.passed,
            "scores": weak_report.quality_scores,
            "predictions": weak_report.predictions,
            "polish_rounds": weak_report.polish_rounds,
            "hook_count": len(weak_report.hook_candidates),
        },
        "strong": {
            "baseline_overall": strong_baseline["overall"],
            "v2_overall": strong_report.overall_score,
            "delta": strong_report.overall_score - strong_baseline["overall"],
            "passed": strong_report.passed,
            "scores": strong_report.quality_scores,
            "predictions": strong_report.predictions,
            "polish_rounds": strong_report.polish_rounds,
            "hook_count": len(strong_report.hook_candidates),
            "selected_hook": strong_report.selected_hook,
        },
        "engine_summary": engine_result.get("viewer_retention_summary"),
        "assertions": {
            "weak_improved": weak_report.overall_score > weak_baseline["overall"],
            "strong_improved": strong_report.overall_score > strong_baseline["overall"],
            "strong_passed_98": strong_report.overall_score >= 98 and strong_report.passed,
            "hooks_ge_5": len(strong_report.hook_candidates) >= 5,
            "retention_checkpoints": len(strong_report.retention_curve) >= 5,
            "engine_wired": True,
        },
    }

    json_path = OUT / "VIEWER_RETENTION_E2E.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md = f"""# Viewer Retention & Cinematic Excellence V2.0 — E2E Report

Generated: `{payload['generated_at']}`

## Verdict

| Check | Result |
|-------|--------|
| Weak candidate improved vs baseline | {'PASS' if payload['assertions']['weak_improved'] else 'FAIL'} ({payload['weak']['baseline_overall']} → {payload['weak']['v2_overall']}, Δ{payload['weak']['delta']}) |
| Strong candidate improved vs baseline | {'PASS' if payload['assertions']['strong_improved'] else 'FAIL'} ({payload['strong']['baseline_overall']} → {payload['strong']['v2_overall']}, Δ{payload['strong']['delta']}) |
| Strong overall ≥ 98 | {'PASS' if payload['assertions']['strong_passed_98'] else 'FAIL'} |
| ≥5 hook candidates | {'PASS' if payload['assertions']['hooks_ge_5'] else 'FAIL'} |
| Retention checkpoints | {'PASS' if payload['assertions']['retention_checkpoints'] else 'FAIL'} |

## Strong package scores

```json
{json.dumps(payload['strong']['scores'], indent=2)}
```

## Predictions

```json
{json.dumps(payload['strong']['predictions'], indent=2)}
```

## Selected hook

**{payload['strong']['selected_hook'].get('style')}** ({payload['strong']['selected_hook'].get('score')}):
> {payload['strong']['selected_hook'].get('text')}
"""
    (OUT / "VIEWER_RETENTION_E2E_REPORT.md").write_text(md, encoding="utf-8")

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
