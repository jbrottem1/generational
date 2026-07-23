"""Tests for Universal Asset Intelligence — no render engine / pipeline edits."""

from __future__ import annotations

from services.asset_intelligence import (
    ASSET_KINDS,
    COLLECTIONS,
    attach_package_to_candidate,
    build_asset_intelligence_package,
    score_asset_quality,
    seed_from_existing_sources,
    semantic_search,
    upsert_asset,
    validate_asset_intelligence_package,
)
from services.asset_intelligence.models import empty_metadata
from services.asset_intelligence.search import duplicate_risk


def test_supported_kinds_and_collections():
    for kind in ("image", "video_clip", "animation", "chart", "map", "music", "overlay"):
        assert kind in ASSET_KINDS
    for c in ("biology", "astronomy", "physics", "history", "finance", "psychology"):
        assert c in COLLECTIONS


def test_seed_and_search_returns_ranked_hits():
    seed = seed_from_existing_sources(limit_per_source=40)
    assert seed["ok"] is True
    assert seed["total"] >= 10

    upsert_asset(
        empty_metadata(
            asset_id="test_dna_diagram",
            kind="scientific_diagram",
            topic="DNA double helix",
            keywords=["dna", "cell", "biology", "helix"],
            collection="biology",
            scientific_accuracy=90,
            visual_quality=85,
            animation_quality=70,
            resolution="1920x1080",
            width=1920,
            height=1080,
            license="test",
            source_system="unit_test",
            uri="memory://dna",
        )
    )
    hits = semantic_search("DNA", limit=5)
    assert hits
    assert any("dna" in str(h.get("topic") or "").lower() or "dna" in [str(k).lower() for k in (h.get("keywords") or [])] for h in hits)
    assert "scores" in hits[0]
    assert hits[0]["rank_score"] >= hits[-1]["rank_score"]


def test_quality_scores_have_mission_fields():
    scores = score_asset_quality(
        empty_metadata(asset_id="x", kind="image", visual_quality=80, scientific_accuracy=75, motion_score=50, width=1280, height=720),
        query="Space",
    )
    for key in ("visual_score", "educational_score", "retention_score", "motion_score", "thumbnail_usefulness", "overall_score"):
        assert key in scores


def test_package_and_validation():
    upsert_asset(
        empty_metadata(
            asset_id="test_space_nebula",
            kind="image",
            topic="Space nebula",
            keywords=["space", "nebula", "astronomy"],
            collection="astronomy",
            scientific_accuracy=80,
            visual_quality=88,
            resolution="1920x1080",
            width=1920,
            height=1080,
            license="test",
            source_system="unit_test",
            uri="memory://space",
        )
    )
    upsert_asset(
        empty_metadata(
            asset_id="test_space_orbit",
            kind="animation",
            topic="Orbital motion",
            keywords=["space", "orbit", "physics"],
            collection="astronomy",
            scientific_accuracy=85,
            visual_quality=80,
            animation_quality=75,
            motion_score=80,
            resolution="1920x1080",
            width=1920,
            height=1080,
            license="test",
            source_system="unit_test",
            uri="memory://orbit",
        )
    )
    pkg = build_asset_intelligence_package(
        topic="Space",
        keywords=["astronomy", "nebula"],
        collection="astronomy",
        needed=3,
    )
    assert pkg.get("selected_media")
    assert "backup_choices" in pkg
    assert "licensing" in pkg
    assert "quality_scores" in pkg
    assert "reuse_analysis" in pkg
    assert "visual_diversity_score" in pkg
    assert "renderer_feed" in pkg
    assert pkg["validation"]["selected_count"] >= 1

    candidate = attach_package_to_candidate({"title": "Space Short"}, pkg)
    assert candidate.get("visual_assets")
    assert "asset_intelligence_package" in candidate


def test_validate_rejects_duplicates():
    bad = {
        "selected_media": [
            {"asset_id": "a", "topic": "same", "kind": "image", "width": 100, "height": 100, "scores": {"overall_score": 20}},
            {"asset_id": "a", "topic": "same", "kind": "image", "width": 100, "height": 100, "scores": {"overall_score": 20}},
        ],
        "visual_diversity_score": 10,
    }
    v = validate_asset_intelligence_package(bad)
    assert v["ok"] is False
    assert "contains_duplicates" in v["hard_fails"]


def test_duplicate_risk_detects_same_fingerprint():
    selected = [{"asset_id": "1", "fingerprint": "abc", "uri": "/x", "topic": "dna", "kind": "image"}]
    risk = duplicate_risk({"asset_id": "2", "fingerprint": "abc", "uri": "/y", "topic": "other", "kind": "image"}, selected)
    assert risk["is_duplicate"] is True
    assert "same_fingerprint" in risk["reasons"]
