"""Tests for the AI Director Engine (Agent 18, key: ai_director).

Proves: engine contract, DirectorPackage slot ownership, other agents' slots
are never mutated, orchestrator stage integration, configuration, and failure
handling.
"""

from __future__ import annotations

import engines  # noqa: F401 - importing registers all engines
from engines import registry
from engines.contracts import ContractEngine
from services.ai_director import DIRECTOR_PACKAGE_FIELDS, DIRECTOR_SUMMARY_FIELDS
from services.ai_director.models import DirectorStatus
from services.orchestrator import ContentPackage, Orchestrator, StageStatus


def make_item(project_id="proj1"):
    return {
        "project_id": project_id,
        "topic": "mystery of the deep ocean",
        "niche": "entertainment",
        "title": "The Ocean Mystery",
        "hook": "What if the ocean disappeared tomorrow?",
        "script": (
            "The ocean vanishes overnight. Cities panic as the tides stop. "
            "Experts trace the cause to a rift. The rift is growing."
        ),
        "keywords": ["ocean"],
        "quality_score": 80,
        "publish_ready": True,
        "target_platforms": ["youtube_shorts"],
        "script_package": {"script": "The ocean vanishes overnight...", "script_score": 78},
        "visual_package": {"scenes": []},
        "audio_package": {"voice_style": {"name": "narrator"}},
        "creative_package": {"storyboard": []},
        "render_package": {"render_package_version": "2.0"},
    }


# ----------------------------------------------------------------- contract


def test_ai_director_is_a_live_contract_engine():
    engine = registry.get_engine("ai_director")
    assert isinstance(engine, ContractEngine)
    assert engine.is_ready() is True
    diag = engine.diagnostics()
    assert diag["engine_id"] == "ai_director"
    assert diag["version"] == "1.0.0"
    assert "unified_packages" in diag["input_contract"]
    assert "ai_director_summary" in diag["output_contract"]
    assert "ai_director_packages" in diag["output_contract"]
    assert "quality" in diag["dependencies"]
    assert "executive-direction" in diag["capabilities"]
    assert engine.health_check()["healthy"] is True


# ----------------------------------------------------------- package output


def test_every_item_receives_a_full_director_package():
    items = [make_item("p1"), make_item("p2")]
    updates = registry.get_engine("ai_director").run({"unified_packages": items})

    assert len(updates["ai_director_packages"]) == 2
    for item, package in zip(items, updates["ai_director_packages"]):
        assert item["director_package"] is package
        for field in DIRECTOR_PACKAGE_FIELDS:
            assert field in package, field
        assert package["production_strategy"]["format"]
        assert package["orchestration_notes"]["creative_studio"]


def test_summary_carries_the_full_contract():
    updates = registry.get_engine("ai_director").run({"unified_packages": [make_item()]})
    summary = updates["ai_director_summary"]
    for field in DIRECTOR_SUMMARY_FIELDS:
        assert field in summary, field
    assert summary["status"] == "directed"
    assert summary["packages"] == 1
    assert "short_form" in summary["formats"]


def test_other_agents_slots_are_never_mutated():
    item = make_item()
    before = {
        key: repr(item[key])
        for key in (
            "script_package", "visual_package", "audio_package",
            "creative_package", "render_package",
        )
    }
    registry.get_engine("ai_director").run({"unified_packages": [item]})
    for key, snapshot in before.items():
        assert repr(item[key]) == snapshot, f"{key} was mutated"


def test_empty_context_reports_no_items_never_fails():
    updates = registry.get_engine("ai_director").run({"command": "probe"})
    assert updates["ai_director_summary"]["status"] == "no_items"
    assert updates["ai_director_summary"]["items"] == 0
    assert updates["ai_director_packages"] == []


def test_ideas_fallback_when_no_unified_packages():
    context = {"ideas": [make_item("i1")]}
    updates = registry.get_engine("ai_director").run(context)
    assert updates["ai_director_summary"]["items"] == 1
    assert context["ideas"][0]["director_package"]["production_strategy"]


def test_broken_item_degrades_to_incomplete_not_a_crash():
    broken = {"project_id": "bad1", "target_platforms": object()}
    updates = registry.get_engine("ai_director").run({"unified_packages": [broken, make_item("ok1")]})
    summary = updates["ai_director_summary"]
    assert summary["packages"] == 2
    assert summary["ready"] + summary["incomplete"] + summary["needs_review"] + summary["degraded"] >= 1


# ------------------------------------------------------------ content package


def test_content_package_carries_the_director_slot_through_roundtrips():
    package = ContentPackage(director_package={"director_package_version": "1.0"})
    data = package.to_dict()
    assert data["director_package"] == {"director_package_version": "1.0"}
    restored = ContentPackage.from_dict(data)
    assert restored.director_package == {"director_package_version": "1.0"}


# ------------------------------------------------------------- orchestrator


def test_ai_director_stage_runs_through_orchestrator():
    context = {"command": "probe", "unified_packages": [make_item("p1")]}
    report = Orchestrator().run_ai_director_stage(context)
    assert report.status == StageStatus.SUCCESS
    assert not report.errors
    assert context["ai_director_summary"]["status"] == "directed"
    assert context["unified_packages"][0]["director_package"]["production_strategy"]


def test_ai_director_stage_is_safe_without_input():
    context = {"command": "probe"}
    report = Orchestrator().run_ai_director_stage(context)
    assert report.status == StageStatus.SUCCESS
    assert not report.errors
    assert context["ai_director_summary"]["items"] == 0
    assert context["ai_director_packages"] == []


# ---------------------------------------------------------- integration flow


def test_director_then_creative_studio_both_write_own_slots():
    """AI Director runs before Creative Studio — each owns its slot."""
    item = make_item()
    context = {"unified_packages": [item]}

    registry.get_engine("ai_director").run(context)
    assert item["director_package"]["production_strategy"]

    registry.get_engine("creative_studio").run(context)
    assert item["creative_package"]["storyboard"]
    # Director slot unchanged by Creative Studio.
    assert item["director_package"]["production_strategy"]["format"] == "short_form"
