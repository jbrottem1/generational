#!/usr/bin/env python3
"""E2E verification — AI Studio Director V5.0.

Proves Production Blueprint is created before production engines, that style
selection varies by topic (not mechanically identical), and that applying the
blueprint improves cross-engine consistency vs undirected candidates.
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
from core.workflows import WORKFLOWS
from services.ai_director import (
    PRODUCTION_BLUEPRINT_FIELDS,
    STYLE_LIBRARY,
    apply_blueprint_to_candidate,
    blueprint_consistency_score,
    build_director_package,
    build_production_blueprint,
)
from services.executive_orchestrator.stages import EXECUTIVE_STAGES, STAGE_ENGINES

OUT = ROOT / "data" / "productions" / "_validation" / "studio_director"
OUT.mkdir(parents=True, exist_ok=True)


TOPICS = [
    {
        "title": "Artificial Intelligence Explained in 60 Seconds",
        "topic": "artificial intelligence",
        "platform": "youtube_shorts",
    },
    {
        "title": "How the James Webb Telescope Sees the Universe",
        "topic": "nasa space telescope orbit",
        "platform": "youtube_shorts",
    },
    {
        "title": "The Fall of the Roman Empire in 60 Seconds",
        "topic": "ancient roman empire history",
        "platform": "youtube_longform",
    },
]


def enrich(base: dict) -> dict:
    return {
        **base,
        "quality_score": 84,
        "audience_intelligence": {
            "primary_audience": "Curious adults 18–45",
            "target_age": "18-45",
            "knowledge_level": "beginner",
            "human_attention_score": 80,
        },
        "psychology": {
            "viral_score": 82,
            "dimensions": {"curiosity_gap": 88, "emotional_intensity": 72},
        },
    }


def main() -> int:
    print("=== AI Studio Director V5.0 E2E ===")
    engine = registry.get_engine("ai_director")
    assert engine and engine.is_ready() and engine.version.startswith("5.")

    # Pipeline order
    intel = WORKFLOWS["intelligence"]
    assert intel.index("audience_intelligence") < intel.index("ai_director")
    assert intel.index("ai_director") < intel.index("script_generation")
    assert WORKFLOWS["media_production"][0] == "ai_director"
    assert STAGE_ENGINES["direction"] == ["ai_director"]
    assert "direction" in EXECUTIVE_STAGES

    directed = []
    blueprints = []
    for topic in TOPICS:
        cand = enrich(topic)
        pkg = build_director_package(cand)
        bp = pkg["production_blueprint"]
        for field in PRODUCTION_BLUEPRINT_FIELDS:
            assert field in bp, field
        applied = apply_blueprint_to_candidate(cand, bp, pkg)
        directed.append(applied)
        blueprints.append({
            "title": topic["title"],
            "style_id": bp["production_style_id"],
            "visual_style": bp["visual_style"],
            "narration_style": bp["narration_style"],
            "music_style": bp["music_style"],
            "platform": bp["platform"],
            "expected_ctr": bp["expected_ctr"],
            "expected_completion_rate": bp["expected_completion_rate"],
            "competitor_niche": (bp.get("competitor_analysis") or {}).get("niche"),
            "differentiation": (bp.get("competitor_analysis") or {}).get(
                "differentiation_recommendations", []
            )[:2],
        })

    # Engine path
    engine_result = engine.run({"candidates": [enrich(TOPICS[0])]})
    summary = engine_result["ai_director_summary"]

    undirected = [enrich(t) for t in TOPICS]
    undirected_score = blueprint_consistency_score(undirected)
    directed_score = blueprint_consistency_score(directed)
    unique_styles = {b["style_id"] for b in blueprints}

    # Planning-before-production proof: directed has full vision; variety across topics
    planning_improves = (
        directed_score["unified_vision"]
        and directed_score["score"] > undirected_score["score"]
        and len(unique_styles) >= 2
    )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "5.0.0",
        "engine_version": engine.version,
        "style_library_size": len(STYLE_LIBRARY),
        "workflow_order": {
            "audience_before_director": True,
            "director_before_script": True,
            "director_first_in_media_production": True,
            "executive_direction_stage": True,
        },
        "blueprints": blueprints,
        "unique_styles": sorted(unique_styles),
        "consistency": {
            "undirected": undirected_score,
            "directed": directed_score,
        },
        "engine_summary": {
            "status": summary["status"],
            "blueprints": summary.get("blueprints"),
            "production_styles": summary.get("production_styles"),
            "average_confidence": summary.get("average_confidence"),
        },
        "planning_before_production_improves_consistency": planning_improves,
        "passed": planning_improves and summary.get("blueprints", 0) >= 1,
    }

    report_json = OUT / "STUDIO_DIRECTOR_E2E.json"
    report_md = OUT / "STUDIO_DIRECTOR_E2E_REPORT.md"
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# AI Studio Director V5.0 — E2E Report",
        "",
        f"Generated: {payload['generated_at']}",
        f"Version: {payload['version']}",
        f"**Passed: {payload['passed']}**",
        "",
        "## Pipeline",
        "- Audience → Director → Script (intelligence)",
        "- `direction` executive stage owns `ai_director`",
        "- media_production starts with `ai_director`",
        "",
        "## Style variety (not mechanically identical)",
    ]
    for b in blueprints:
        lines.append(
            f"- **{b['title']}** → `{b['style_id']}` / {b['narration_style']} / {b['music_style']}"
        )
    lines.extend([
        "",
        "## Consistency",
        f"- Undirected blueprint score: {undirected_score['score']} (blueprints={undirected_score['has_blueprints']})",
        f"- Directed blueprint score: {directed_score['score']} (unique styles={directed_score['unique_styles']})",
        f"- Planning improves consistency: {planning_improves}",
        "",
        "## Expectations (sample)",
        f"- CTR: {blueprints[0]['expected_ctr']}",
        f"- Completion: {blueprints[0]['expected_completion_rate']}",
        "",
    ])
    report_md.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "passed": payload["passed"],
        "unique_styles": payload["unique_styles"],
        "directed_score": directed_score["score"],
        "undirected_score": undirected_score["score"],
        "report": str(report_md),
    }, indent=2))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
