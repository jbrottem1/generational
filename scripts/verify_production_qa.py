#!/usr/bin/env python3
"""E2E validation for Production Quality Assurance Engine."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import engines  # noqa: F401
from engines import registry
from services.production_qa import inspect_production, write_validation_bundle
from services.production_qa.publish_gate import ProductionQAGate, ensure_pqa_gate_registered

OUT = ROOT / "data" / "productions" / "_validation" / "production_qa"


def strong_fixture() -> dict:
    return {
        "id": "pqa_seasons_demo",
        "title": "How the seasons work",
        "seo_score": 96,
        "psychology_score": 94,
        "human_attention_score": 93,
        "visual_score": 95,
        "script_quality": 95,
        "aspect_ratio": "9:16",
        "duration_sec": 42,
        "captions": [{"text": "Earth tilts", "start": 0, "end": 2}],
        "thumbnail": {"path": "thumb.jpg"},
        "seo_package": {
            "title": "How the Seasons Work",
            "description": "Axial tilt explained with NASA imagery.",
            "keywords": ["seasons", "earth", "tilt"],
            "hashtags": ["#science"],
        },
        "citations": {
            "citation_count": 5,
            "claim_confidence": 95,
            "unsupported_claims": [],
            "sources": [{"title": "NASA", "url": "https://nasa.gov"}],
        },
        "critique": {"score": 94},
        "psychology": {
            "first_3_second_hook": 95,
            "curiosity_gap": 92,
            "retention_potential": 93,
            "share_likelihood": 90,
            "replay_value": 88,
            "clarity": 94,
            "knowledge_density": 90,
            "ctr_estimate": 8.0,
        },
        "structured_script": {
            "quality_score": 95,
            "full_script": "The Earth tilts on its axis. Notice this fossil.",
            "caption_plan": [{"text": "tilt"}],
            "clarity": 94,
            "logical_progression": 93,
        },
        "evidence_package": {
            "authentic_hit_count": 4,
            "ai_fallback_count": 0,
            "overall_evidence_confidence": 0.95,
            "scenes": [
                {
                    "scene_id": "s1",
                    "narration": "The Earth tilts on its axis.",
                    "modality": "photo",
                    "evidence_confidence": 0.96,
                    "reality_image_ids": ["earth"],
                    "annotation_plan": [
                        {"narration_cue": "Earth", "target": "globe", "highlight_region": {"x0": 0.4, "y0": 0.3, "x1": 0.6, "y1": 0.5}}
                    ],
                }
            ],
        },
        "visual_package": {
            "visual_score": 95,
            "aspect_ratio": "9:16",
            "scenes": [{"scene_id": "s1", "shot_type": "wide", "assets": ["earth"]}],
            "thumbnails": [{}],
            "timeline": [{"t": 0}],
        },
        "cinematography_plan": {
            "overall_attention_score": 94,
            "scenes": [
                {
                    "scene_id": "s1",
                    "movement": "orbit",
                    "reason": "Tilt narration → orbit",
                    "camera_plan": {"movement": "orbit"},
                }
            ],
            "timeline": [{"t": 0}],
            "animation_handoff": {"scenes": [{"camera": "orbit"}]},
        },
        "cinematography_attention_score": 94,
        "animation_handoff": {"scenes": [{"camera": "orbit"}]},
        "voice_package": {"path": "n.mp3", "normalized": True, "music_balance": 0.3},
        "timeline": {"segments": [{"start": 0, "end": 6}]},
        "render_package": {"aspect_ratio": "9:16", "duration_sec": 42},
    }


def weak_fixture() -> dict:
    return {
        "id": "pqa_weak_demo",
        "title": "Untitled",
        "citations": {"citation_count": 0, "unsupported_claims": ["x", "y"], "claim_confidence": 10},
        "evidence_package": {
            "authentic_hit_count": 0,
            "ai_fallback_count": 4,
            "overall_evidence_confidence": 0.15,
            "scenes": [],
        },
    }


def main() -> int:
    ensure_pqa_gate_registered()
    engine = registry.get_engine("production_qa")
    strong = strong_fixture()
    weak = weak_fixture()

    strong_report = inspect_production(strong, {"research": {"research_confidence": 0.93}})
    weak_report = inspect_production(weak)

    out = engine.run(
        {
            "selected_ideas": [dict(strong), dict(weak)],
            "research": {"research_confidence": 0.93},
        }
    )

    gate = ProductionQAGate()
    gate_ok = gate.review({"enforce_pqa": True, "pqa_report": strong_report.to_dict()})
    gate_block = gate.review({"enforce_pqa": True, "pqa_report": weak_report.to_dict()})

    payload = {
        "status": "SUCCESS"
        if strong_report.decision == "APPROVE" and weak_report.decision != "APPROVE" and not gate_ok and gate_block
        else "FAIL",
        "strong": strong_report.to_dict(),
        "weak": weak_report.to_dict(),
        "engine_summary": out.get("pqa_summary"),
        "gate": {"approve_problems": gate_ok, "weak_problems": gate_block},
        "narration_examples": {
            "strong_decision": strong_report.decision,
            "strong_overall": strong_report.overall_score,
            "scores": {k: v.score for k, v in strong_report.categories.items()},
            "platforms": {p.platform: p.ready for p in strong_report.platform_ready},
        },
    }

    paths = write_validation_bundle(payload, name="PQA_E2E")
    # Overwrite markdown with human report
    md = [
        "# Production Quality Assurance — E2E",
        "",
        f"Generated status: **{payload['status']}**",
        "",
        "## Strong production",
        strong_report.to_dict()["report_markdown"],
        "",
        "## Weak production",
        f"Decision: {weak_report.decision} · Overall: {weak_report.overall_score}",
        "",
        f"Gate blocks weak: {bool(gate_block)}",
        "",
        f"JSON: `{paths['json']}`",
    ]
    paths["markdown"].write_text("\n".join(md), encoding="utf-8")

    print(json.dumps(payload["narration_examples"], indent=2))
    print(f"Report: {paths['markdown']}")
    print(f"=== RESULT: {payload['status']} ===")
    return 0 if payload["status"] == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
