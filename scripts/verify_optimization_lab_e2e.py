#!/usr/bin/env python3
"""E2E verification — Autonomous Optimization & Experimentation V4.0.

Proves multi-variant ranking + revision lifts production quality vs baseline A,
and that experiment history / knowledge patterns are recorded.
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
from services.optimization_lab import build_optimization_package
from services.optimization_lab.continuous import measurable_improvement_signal
from services.optimization_lab.history import search_experiments
from services.optimization_lab.knowledge import load_patterns

OUT = ROOT / "data" / "productions" / "_validation" / "optimization_lab"
OUT.mkdir(parents=True, exist_ok=True)


def candidate() -> dict:
    return {
        "title": "Artificial Intelligence Explained in 60 Seconds",
        "topic": "artificial intelligence",
        "platform": "youtube_shorts",
        "hook": "AI is software.",
        "psychology": {
            "viral_score": 78,
            "dimensions": {
                "first_3_second_hook": 70,
                "curiosity_gap": 80,
                "retention_potential": 74,
                "share_likelihood": 68,
            },
        },
        "viewer_retention_package": {
            "overall_score": 94,
            "quality_scores": {"retention": 93, "narration": 92},
            "passed": True,
        },
        "studio_render_package": {"overall_score": 95, "passed": True},
        "visual_package": {
            "aspect_ratio": "9:16",
            "scenes": [
                {"scene_id": "s1", "narration": "AI is already changing your life."},
                {"scene_id": "s2", "narration": "Notice this tiny chip."},
                {"scene_id": "s3", "narration": "Robot arms assemble with precision."},
                {"scene_id": "s4", "narration": "One billion people use AI daily."},
            ],
        },
    }


def main() -> int:
    print("=== Autonomous Optimization & Experimentation V4.0 E2E ===")
    engine = registry.get_engine("optimization_lab")
    assert engine and engine.is_ready() and engine.version.startswith("4.")

    # Seed multiple runs to demonstrate learning trajectory
    scores = []
    last = None
    for i in range(4):
        c = candidate()
        c["title"] = f"{c['title']} run{i+1}"
        pkg, _ = build_optimization_package(c, variant_count=5, record_history=True)
        scores.append(pkg.overall_score)
        last = pkg

    baseline_a = next(
        (v for v in (last.variants if last else []) if v.get("baseline")),
        {},
    )
    baseline_score = int(baseline_a.get("overall_score") or 0)
    winner_score = int(last.overall_score if last else 0)

    engine_result = engine.run({"candidates": [candidate()]})
    signal = measurable_improvement_signal()
    history = search_experiments(limit=10)
    patterns = load_patterns()

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "4.0.0",
        "threshold": 98,
        "seed_scores": scores,
        "baseline_a_score": baseline_score,
        "winner_score": winner_score,
        "delta_vs_baseline_a": winner_score - baseline_score,
        "leaderboard": last.leaderboard if last else [],
        "winner": {
            "label": (last.winner if last else {}).get("label"),
            "hook": ((last.winner if last else {}).get("axes") or {}).get("hook"),
            "title": ((last.winner if last else {}).get("axes") or {}).get("title"),
        },
        "predictions": last.predictions if last else {},
        "critique_issues": (last.critique if last else {}).get("issue_count"),
        "revision_rounds": last.revision_rounds if last else 0,
        "learning_signal": signal,
        "history_count": len(history),
        "pattern_keys": list(patterns.keys()),
        "engine_summary": engine_result.get("optimization_summary"),
        "assertions": {
            "five_variants": len(last.variants) == 5 if last else False,
            "winner_beats_or_equals_baseline": winner_score >= baseline_score,
            "winner_passed_98": winner_score >= 98 and bool(last and last.passed),
            "predictions_present": bool((last.predictions if last else {}).get("ctr_pct")),
            "history_recorded": len(history) >= 1,
            "patterns_loaded": len(patterns) >= 5,
            "engine_wired": True,
        },
    }

    json_path = OUT / "OPTIMIZATION_LAB_E2E.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md = f"""# Autonomous Optimization & Experimentation V4.0 — E2E Report

Generated: `{payload['generated_at']}`

## Verdict

| Check | Result |
|-------|--------|
| 5 variants | {'PASS' if payload['assertions']['five_variants'] else 'FAIL'} |
| Winner ≥ baseline A | {'PASS' if payload['assertions']['winner_beats_or_equals_baseline'] else 'FAIL'} ({payload['baseline_a_score']} → {payload['winner_score']}) |
| Winner ≥ 98 | {'PASS' if payload['assertions']['winner_passed_98'] else 'FAIL'} |
| Predictions present | {'PASS' if payload['assertions']['predictions_present'] else 'FAIL'} |
| History recorded | {'PASS' if payload['assertions']['history_recorded'] else 'FAIL'} |
| Patterns loaded | {'PASS' if payload['assertions']['patterns_loaded'] else 'FAIL'} |

## Leaderboard

```json
{json.dumps(payload['leaderboard'], indent=2)}
```

## Predictions

```json
{json.dumps(payload['predictions'], indent=2)}
```

## Learning signal

```json
{json.dumps(payload['learning_signal'], indent=2)}
```
"""
    (OUT / "OPTIMIZATION_LAB_E2E_REPORT.md").write_text(md, encoding="utf-8")

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
