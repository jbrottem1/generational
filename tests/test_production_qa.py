"""Tests for Production Quality Assurance Engine."""

from __future__ import annotations

import engines  # noqa: F401
from core.workflows import WORKFLOWS
from engines import registry
from services.production_qa import (
    CATEGORY_PASS_THRESHOLD,
    ProductionQAReport,
    build_revision_requests,
    compare_predicted_vs_actual,
    inspect_production,
)
from services.production_qa.models import CategoryScore
from services.production_qa.publish_gate import ProductionQAGate
from services.production_qa.revision import group_revisions_by_engine


def _strong_item() -> dict:
    return {
        "id": "seasons-001",
        "title": "How the seasons work",
        "publishable": True,
        "seo_score": 94,
        "psychology_score": 93,
        "human_attention_score": 92,
        "visual_score": 95,
        "script_quality": 94,
        "aspect_ratio": "9:16",
        "duration_sec": 45,
        "captions": [{"text": "Earth tilts", "start": 0, "end": 2}],
        "thumbnail": {"path": "thumb.jpg"},
        "seo_package": {
            "title": "How the Seasons Work — Earth Tilt Explained",
            "description": "A clear documentary short on axial tilt and seasons.",
            "keywords": ["seasons", "earth", "tilt", "science"],
            "hashtags": ["#science", "#seasons"],
        },
        "citations": {
            "citation_count": 4,
            "claim_confidence": 92,
            "unsupported_claims": [],
            "sources": [
                {"title": "NASA Earth", "url": "https://earthobservatory.nasa.gov/"},
                {"title": "NOAA Climate"},
            ],
        },
        "critique": {"score": 92},
        "psychology": {
            "first_3_second_hook": 94,
            "curiosity_gap": 90,
            "retention_potential": 91,
            "share_likelihood": 88,
            "replay_value": 86,
            "clarity": 93,
            "knowledge_density": 88,
            "ctr_estimate": 7.5,
        },
        "audience_intelligence": {
            "human_attention_score": 92,
            "estimated_runtime_hint_sec": 48,
        },
        "structured_script": {
            "quality_score": 94,
            "full_script": "The Earth tilts. Notice this fossil. Seasons follow the tilt.",
            "caption_plan": [{"text": "tilt"}],
            "clarity": 93,
            "logical_progression": 92,
        },
        "evidence_package": {
            "authentic_hit_count": 5,
            "ai_fallback_count": 0,
            "overall_evidence_confidence": 0.94,
            "scenes": [
                {
                    "scene_id": "s1",
                    "narration": "The Earth tilts on its axis.",
                    "modality": "photo",
                    "evidence_confidence": 0.95,
                    "reality_image_ids": ["earth_1"],
                    "annotation_plan": [
                        {
                            "narration_cue": "Earth",
                            "target": "globe",
                            "highlight_region": {"x0": 0.4, "y0": 0.3, "x1": 0.6, "y1": 0.5},
                            "timing": {"appear": 0.2, "fade": 0.8},
                        }
                    ],
                },
                {
                    "scene_id": "s2",
                    "narration": "Notice this fossil in the limestone.",
                    "modality": "photo",
                    "evidence_confidence": 0.9,
                    "atlas_asset_ids": ["fossil_1"],
                    "annotation_plan": [
                        {
                            "narration_cue": "fossil",
                            "target": "fossil",
                            "highlight_region": {"x0": 0.3, "y0": 0.4, "x1": 0.5, "y1": 0.6},
                        }
                    ],
                },
            ],
        },
        "visual_package": {
            "visual_score": 95,
            "aspect_ratio": "9:16",
            "scenes": [
                {"scene_id": "s1", "shot_type": "establishing", "assets": ["earth"]},
                {"scene_id": "s2", "shot_type": "detail", "assets": ["fossil"]},
            ],
            "thumbnails": [{"concept": "earth tilt"}],
            "timeline": [{"t": 0, "scene": "s1"}, {"t": 5, "scene": "s2"}],
        },
        "cinematography_plan": {
            "overall_attention_score": 93,
            "pacing": "brisk",
            "scenes": [
                {
                    "scene_id": "s1",
                    "movement": "orbit",
                    "reason": "Narration describes Earth tilt — orbit reinforces motion",
                    "camera_plan": {"movement": "orbit"},
                    "easing": "ease_in_out",
                },
                {
                    "scene_id": "s2",
                    "movement": "slow_push_in",
                    "reason": "Notice cue — push in to fossil",
                    "camera_plan": {"movement": "slow_push_in"},
                },
            ],
            "timeline": [{"t": 0}, {"t": 1}],
            "animation_handoff": {"scenes": [{"scene_id": "s1", "camera": "orbit"}]},
        },
        "cinematography_attention_score": 93,
        "animation_handoff": {"scenes": [{"scene_id": "s1", "camera": "orbit"}]},
        "voice_package": {"path": "narration.mp3", "normalized": True, "music_balance": 0.35},
        "timeline": {"segments": [{"start": 0, "end": 5}, {"start": 5, "end": 10}]},
        "render_package": {"aspect_ratio": "9:16", "duration_sec": 45},
    }


def _weak_item() -> dict:
    return {
        "id": "weak-001",
        "title": "Vague clip",
        "publishable": True,
        "citations": {"citation_count": 0, "unsupported_claims": ["claim a", "claim b", "claim c"], "claim_confidence": 20},
        "evidence_package": {"authentic_hit_count": 0, "ai_fallback_count": 3, "overall_evidence_confidence": 0.2, "scenes": []},
        "psychology_score": 40,
    }


def test_strong_production_approves():
    report = inspect_production(_strong_item(), {"research": {"research_confidence": 0.9}})
    assert report.overall_score >= 90
    assert report.decision == "APPROVE"
    assert report.categories["research_accuracy"].score >= 90
    assert report.categories["evidence"].details["real_image_pct"] == 100.0
    assert all(p.ready for p in report.platform_ready if p.platform in ("tiktok", "youtube_shorts", "instagram_reels"))
    data = report.to_dict()
    assert "Overall Score" in data["report_markdown"]
    assert data["passed"] is True


def test_weak_production_blocks_or_revises():
    report = inspect_production(_weak_item())
    assert report.decision in ("BLOCK_EXPORT", "REQUEST_REVISION")
    assert report.overall_score < 90
    assert report.revision_requests
    owners = group_revisions_by_engine(report.revision_requests)
    assert "evidence_intelligence" in owners or "research" in owners or "citation" in owners


def test_category_below_90_never_approves():
    item = _strong_item()
    item["seo_score"] = 40
    item["seo_package"] = {}
    item["title"] = ""
    report = inspect_production(item, {"research": {"research_confidence": 0.9}})
    assert report.categories["seo"].score < CATEGORY_PASS_THRESHOLD
    assert report.decision != "APPROVE"


def test_revision_routing():
    cats = {
        "evidence": CategoryScore(key="evidence", label="Evidence", score=70, corrections_required=["Add photos"]),
        "cinematography": CategoryScore(key="cinematography", label="Cinematography", score=80),
    }
    reqs = build_revision_requests(cats)
    assert len(reqs) == 2
    cine = next(r for r in reqs if r.category == "cinematography")
    assert "cinematography" in cine.target_engines


def test_report_round_trip():
    report = inspect_production(_strong_item(), {"research": {"research_confidence": 0.85}})
    again = ProductionQAReport.from_dict(report.to_dict())
    assert again.overall_score == report.overall_score
    assert again.decision == report.decision


def test_learning_compare():
    report = inspect_production(_strong_item()).to_dict()
    comparison = compare_predicted_vs_actual(
        report,
        {"ctr": 0.08, "shares": 90, "avg_watch_time": 40},
    )
    assert comparison["comparisons"]
    assert "mean_abs_error" in comparison


def test_publish_gate_blocks_revision():
    gate = ProductionQAGate()
    problems = gate.review(
        {
            "enforce_pqa": True,
            "pqa_report": {"decision": "REQUEST_REVISION", "passed": False},
        }
    )
    assert problems
    assert gate.review({"enforce_pqa": True, "pqa_report": {"decision": "APPROVE", "passed": True}}) == []
    assert gate.review({"mode": "dry_run", "pqa_report": {"decision": "BLOCK_EXPORT"}}) == []


def test_engine_attaches_report_and_blocks_publishable():
    engine = registry.get_engine("production_qa")
    assert engine is not None
    weak = _weak_item()
    weak["render_package"] = {"mp4_path": "mock://weak.mp4"}
    out = engine.run(
        {
            "selected_ideas": [weak],
            "research": {"research_confidence": 0.2},
            "enforce_pqa": True,
        }
    )
    assert out["pqa_summary"]["items"] == 1
    assert weak["pqa_report"]["decision"] in ("BLOCK_EXPORT", "REQUEST_REVISION")
    assert weak["publishable"] is False
    assert "production_qa" in weak["gate_failures"]


def test_engine_approves_strong():
    engine = registry.get_engine("production_qa")
    strong = _strong_item()
    out = engine.run({"selected_ideas": [strong], "research": {"research_confidence": 0.92}})
    assert strong["pqa_decision"] == "APPROVE"
    assert strong["pqa_passed"] is True
    assert out["pqa_passed"] is True


def test_workflow_order_intelligence():
    steps = WORKFLOWS["intelligence"]
    assert steps.index("quality") < steps.index("production_qa")
    assert steps[-1] == "production_qa"


def test_workflow_order_full_content():
    steps = WORKFLOWS["full_content"]
    assert steps.index("video") < steps.index("production_qa") < steps.index("publishing")


def test_workflow_order_media_production():
    steps = WORKFLOWS["media_production"]
    assert steps.index("render_package") < steps.index("production_qa") < steps.index("publishing_queue")
