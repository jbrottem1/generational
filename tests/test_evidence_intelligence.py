"""Tests for Evidence & Visual Intelligence Engine."""

from __future__ import annotations

import engines  # noqa: F401
from core.workflows import WORKFLOWS
from engines import registry
from services.evidence_intelligence import (
    TRUSTED_SOURCES,
    AnnotationSpec,
    EvidencePackage,
    bind_package_to_visual_scenes,
    build_evidence_package,
    plan_scene_evidence,
    scene_builder_payload,
)
from services.evidence_intelligence.gather import build_annotation_plan, decide_modality
from services.evidence_intelligence.models import EvidenceHit, ModalityDecision


def test_trusted_sources_include_institutions():
    for name in ("NASA", "NOAA", "Wikimedia Commons", "Smithsonian", "Knowledge Atlas"):
        assert name in TRUSTED_SOURCES


def test_annotations_require_narration_cue_and_fade():
    plans = build_annotation_plan(
        "The Earth orbits the Sun with a tilted axis near the equator.",
        start_sec=0.0,
        end_sec=6.0,
    )
    assert plans
    cues = {a.narration_cue.lower() for a in plans}
    assert cues & {"earth", "sun", "axis", "equator", "orbits"} or any(
        c in {"earth", "sun", "equator", "axis"} for c in cues
    )
    for ann in plans:
        assert ann.narration_cue
        assert ann.target.startswith("keyword:")
        assert ann.end_sec > ann.start_sec
        assert ann.extras.get("fade_out")
        assert ann.kind in ("label", "arrow", "circle", "bracket", "measurement", "timeline", "comparison_overlay", "highlight")


def test_no_annotations_without_narration():
    assert build_annotation_plan("", start_sec=0, end_sec=5) == []


def test_modality_prefers_real_photos():
    hits = [
        EvidenceHit(source="NASA", image_id="earth", visual_type="photograph", provider_tier=1, evidence_confidence=90),
    ]
    decision = decide_modality("Earth from space", hits, topic="Earth")
    assert decision.real_image_available is True
    assert decision.ai_generation_fallback_only is False
    assert decision.chosen_modality == "photograph"


def test_modality_ai_only_when_empty():
    decision = decide_modality("Abstract quantum foam process", [], topic="quantum")
    assert decision.ai_generation_fallback_only is True
    assert decision.chosen_modality in ("ai_generated", "animation", "visualization_3d")


def test_scene_evidence_plan_structure():
    plan = plan_scene_evidence(
        "How the camera lens focuses light onto the sensor.",
        topic="How cameras are made",
        start_sec=0,
        end_sec=5,
    )
    data = plan.to_dict()
    assert "evidence_confidence" in data
    assert "image_source" in data
    assert "license_status" in data
    assert "visual_type" in data
    assert "motion_plan" in data
    assert "annotation_plan" in data
    assert "scene_builder" in data
    sb = scene_builder_payload(plan)
    assert set(sb.keys()) >= {"image", "motion_plan", "annotation_plan", "narration_timing", "transition_type", "expected_attention_score"}
    # No raw provider dumps
    assert "etag" not in str(data)


def test_package_round_trip():
    candidate = {
        "title": "Seasons Explained",
        "script": "Earth tilts on its axis. Summer comes when the northern hemisphere leans toward the Sun.",
        "hook": "Why seasons exist",
    }
    package = build_evidence_package(candidate, topic="Seasons Explained", domain="science")
    restored = EvidencePackage.from_dict(package.to_dict())
    assert restored.topic == package.topic
    assert len(restored.scenes) == len(package.scenes)
    assert restored.overall_evidence_confidence == package.overall_evidence_confidence


def test_bind_into_visual_package():
    evidence = build_evidence_package(
        {"title": "Coral reef", "script": "Coral reefs host thousands of species near the equator."},
        topic="Coral",
    )
    visual = {
        "visual_score": 70,
        "scenes": [
            {"scene_number": 1, "asset_type": "ai_image", "narration": "Coral reefs host species."},
        ],
        "thumbnails": [],
    }
    bound = bind_package_to_visual_scenes(visual, evidence)
    scene = bound["scenes"][0]
    assert "annotation_plan" in scene
    assert "scene_builder" in scene
    assert scene.get("asset_type") in ("atlas_image", "ai_image")


def test_engine_attaches_evidence_package():
    engine = registry.get_engine("evidence_intelligence")
    assert engine is not None
    updates = engine.run(
        {
            "candidates": [
                {
                    "title": "How black holes work",
                    "script": "A black hole bends spacetime. Light cannot escape past the event horizon.",
                    "human_attention_score": 70,
                }
            ],
            "niche": "science",
            "subject": "black holes",
        }
    )
    cand = updates["candidates"][0]
    assert cand["evidence_package"]
    assert "scene_builder_plans" in cand
    assert updates["evidence_intelligence_summary"]["prefer_real_over_ai"] is True


def test_workflow_order_evidence_before_visual():
    for key in ("intelligence", "full_content"):
        steps = WORKFLOWS[key]
        assert steps.index("attention_graph") < steps.index("evidence_intelligence")
        assert steps.index("evidence_intelligence") < steps.index("visual_intelligence")


def test_annotation_spec_rejects_unknown_kind():
    ann = AnnotationSpec.from_dict({"kind": "random_squiggle", "target": "keyword:Sun", "narration_cue": "Sun"})
    assert ann.kind == "label"
