"""Tests for the Creative Studio Engine (Agent 12, key: creative_studio).

Proves: the engine satisfies the shared contract, every packaged item is
designed into a complete CreativeProductionPackage written to the
`creative_package` slot, other agents' slots are never mutated, asset
sourcing is provider-driven and swappable, the ContentPackage carries the
new slot through round-trips, and the orchestrator creative stage runs
safely with and without input.
"""

from __future__ import annotations

import engines  # noqa: F401 - importing registers all engines
from engines import registry
from engines.contracts import ContractEngine
from providers.creative import (
    MockCreativeProvider,
    get_creative_provider,
    register_creative_provider,
)
from providers.creative_provider import CREATIVE_ASSET_TYPES, CreativeAssetProvider
from services.creative_studio import CREATIVE_PACKAGE_FIELDS, CREATIVE_SUMMARY_FIELDS
from services.creative_studio.models import ReadinessStatus
from services.orchestrator import ContentPackage, Orchestrator, StageStatus


def make_item(project_id="proj1"):
    """One canonical ContentPackage-style dict as packaging emits it."""
    return {
        "project_id": project_id,
        "topic": "deep sea creatures",
        "niche": "science",
        "title": "The Ocean Mystery",
        "hook": "What if the ocean disappeared tomorrow?",
        "script": (
            "The ocean vanishes overnight. Cities panic as the tides stop. "
            "Scientists trace the cause to a rift. The rift is growing. "
            "Humanity must act before dawn."
        ),
        "keywords": ["ocean", "science"],
        "quality_score": 80,
        "publish_ready": True,
        "script_package": {"script": "The ocean vanishes overnight...", "script_score": 78},
        "visual_package": {"scenes": []},
        "audio_package": {"voice_style": {"name": "narrator"}},
        "render_package": {"render_package_version": "2.0"},
    }


# ----------------------------------------------------------------- contract


def test_creative_studio_is_a_live_contract_engine():
    engine = registry.get_engine("creative_studio")
    assert isinstance(engine, ContractEngine)
    assert engine.is_ready() is True
    diag = engine.diagnostics()
    assert diag["engine_id"] == "creative_studio"
    assert diag["version"] == "1.1.0"
    assert "unified_packages" in diag["input_contract"]
    assert "creative_summary" in diag["output_contract"]
    assert "creative_packages" in diag["output_contract"]
    assert "quality" in diag["dependencies"]
    assert engine.health_check()["healthy"] is True


# ----------------------------------------------------------- package output


def test_every_item_is_designed_into_a_full_creative_package():
    items = [make_item("p1"), make_item("p2")]
    updates = registry.get_engine("creative_studio").run({"unified_packages": items})

    assert len(updates["creative_packages"]) == 2
    for item, package in zip(items, updates["creative_packages"]):
        assert item["creative_package"] is package
        for field in CREATIVE_PACKAGE_FIELDS:
            assert field in package, field
        assert package["storyboard"]
        assert package["shot_list"]
        assert package["asset_requirements"]
        assert package["production_readiness"]["status"] == ReadinessStatus.READY


def test_summary_carries_the_full_contract():
    updates = registry.get_engine("creative_studio").run({"unified_packages": [make_item()]})
    summary = updates["creative_summary"]
    for field in CREATIVE_SUMMARY_FIELDS:
        assert field in summary, field
    assert summary["status"] == "designed"
    assert summary["ready"] == 1
    assert summary["production_types"] == ["science_visualization"]


def test_other_agents_slots_are_never_mutated():
    item = make_item()
    before = {
        key: repr(item[key])
        for key in ("script_package", "visual_package", "audio_package", "render_package")
    }
    registry.get_engine("creative_studio").run({"unified_packages": [item]})
    for key, snapshot in before.items():
        assert repr(item[key]) == snapshot, f"{key} was mutated"


def test_empty_context_reports_no_items_never_fails():
    updates = registry.get_engine("creative_studio").run({"command": "probe"})
    assert updates["creative_summary"]["status"] == "no_items"
    assert updates["creative_summary"]["items"] == 0
    assert updates["creative_packages"] == []


def test_ideas_fallback_when_no_unified_packages():
    context = {"ideas": [make_item("i1")]}
    updates = registry.get_engine("creative_studio").run(context)
    assert updates["creative_summary"]["items"] == 1
    assert context["ideas"][0]["creative_package"]["storyboard"]


def test_a_broken_item_degrades_to_incomplete_not_a_crash():
    # scene_breakdown of non-dict garbage exercises the per-item guard path.
    broken = {"project_id": "bad1", "scene_breakdown": "not-a-list-of-dicts"}
    updates = registry.get_engine("creative_studio").run({"unified_packages": [broken, make_item("ok1")]})
    summary = updates["creative_summary"]
    assert summary["packages"] == 2
    assert summary["ready"] >= 1  # the good item still designed


# ---------------------------------------------------------------- providers


def test_mock_creative_provider_serves_every_asset_type_deterministically():
    provider = MockCreativeProvider()
    for asset_type in CREATIVE_ASSET_TYPES:
        assert provider.supports(asset_type)
    requirement = {"asset_id": "a1", "asset_type": "ai_video", "prompt": "ocean"}
    first = provider.fulfill(requirement)
    assert first == provider.fulfill(dict(requirement))
    assert first["placeholder"] is True
    assert first["uri"].startswith("mock://assets/creative/ai_video/")


def test_provider_registry_swaps_real_backends_per_asset_type():
    class FakeVideoModel(CreativeAssetProvider):
        name = "runway_style_api"
        asset_types = ("ai_video",)

        def is_available(self):
            return True

        def fulfill(self, requirement):
            return {"asset_id": requirement["asset_id"], "uri": "real://video"}

    register_creative_provider("ai_video", FakeVideoModel())
    try:
        assert get_creative_provider("ai_video").name == "runway_style_api"
        assert get_creative_provider("ai_image").name == "mock_creative"
    finally:
        from providers.creative import _providers

        _providers.pop("ai_video", None)


# ------------------------------------------------------------ content package


def test_content_package_carries_the_creative_slot_through_roundtrips():
    package = ContentPackage(creative_package={"creative_package_version": "1.0"})
    data = package.to_dict()
    assert data["creative_package"] == {"creative_package_version": "1.0"}
    restored = ContentPackage.from_dict(data)
    assert restored.creative_package == {"creative_package_version": "1.0"}


# ------------------------------------------------------------- orchestrator


def test_creative_stage_runs_through_orchestrator():
    context = {"command": "probe", "unified_packages": [make_item("p1")]}
    report = Orchestrator().run_creative_stage(context)
    assert report.status == StageStatus.SUCCESS
    assert not report.errors
    assert report.confidence > 0
    assert context["creative_summary"]["status"] == "designed"
    assert context["unified_packages"][0]["creative_package"]["storyboard"]


def test_creative_stage_is_safe_without_input():
    context = {"command": "probe"}
    report = Orchestrator().run_creative_stage(context)
    assert report.status == StageStatus.SUCCESS
    assert not report.errors
    assert context["creative_summary"]["items"] == 0
    assert context["creative_packages"] == []
