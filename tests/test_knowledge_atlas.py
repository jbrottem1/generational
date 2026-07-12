"""Tests for Generational Knowledge Atlas."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_atlas_catalog_loaded():
    from services.knowledge_atlas.catalog import load_atlas

    atlas = load_atlas()
    assert len(atlas) >= 6
    for aid in (
        "hoverfly_lateral",
        "wasp_lateral",
        "coral_snake",
        "scarlet_kingsnake",
        "monarch_adult",
        "viceroy_adult",
    ):
        assert aid in atlas, f"missing {aid}"


def test_atlas_search_mimicry():
    from services.knowledge_atlas.search import search_visuals

    hits = search_visuals(query="batesian mimicry", concepts=["hoverfly", "wasp"])
    ids = [h["asset_id"] for h in hits]
    assert "hoverfly_lateral" in ids or "wasp_lateral" in ids


def test_atlas_planner_batesian_demo():
    from services.knowledge_atlas.planner import plan_visual_evidence

    plan = plan_visual_evidence(
        main_concept="Batesian mimicry: harmless species resembles harmful model",
        demo_id="foundation_batesian_101",
        domain="biology",
    )
    assert plan["recommended_asset_ids"]
    assert plan["panels"]


def test_atlas_qc_passes_seed_assets():
    from services.knowledge_atlas.catalog import load_atlas
    from services.knowledge_atlas.qc import validate_asset

    for asset in load_atlas().values():
        result = validate_asset(asset)
        assert result.passed, result.hard_fails


if __name__ == "__main__":
    test_atlas_catalog_loaded()
    test_atlas_search_mimicry()
    test_atlas_planner_batesian_demo()
    test_atlas_qc_passes_seed_assets()
    print("OK")
