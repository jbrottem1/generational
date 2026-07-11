"""Tests for the Episode Design Engine (Agent 25, key: episode_design).

NOTE: Mission brief named this Agent 24; registry assigns Agent 25 because
Agent 24 is already Executive Intelligence (key: autonomous_executive).

Proves: engine contract, EpisodeDesignPackage slot ownership, other agents'
slots are never mutated, orchestrator stage integration, graceful degradation,
ContentPackage round-trip, playbook persistence, and AST peer-engine isolation.
"""

from __future__ import annotations

import ast
from pathlib import Path

import engines  # noqa: F401 - importing registers all engines
from engines import registry
from engines.contracts import ContractEngine
from services.episode_design import (
    EPISODE_DESIGN_PACKAGE_FIELDS,
    EPISODE_DESIGN_SUMMARY_FIELDS,
    RETENTION_SCORE_FIELDS,
    BLUEPRINT_BEATS,
)
from services.episode_design.models import EpisodeDesignStatus
from services.orchestrator import ContentPackage, Orchestrator, StageStatus


def make_item(project_id="proj1"):
    return {
        "project_id": project_id,
        "topic": "why your brain forgets things on purpose",
        "niche": "Psychology",
        "title": "The Forgetting Brain",
        "hook": "Your brain is deleting memories right now — and that's a feature, not a bug.",
        "script": (
            "Your brain is deleting memories right now. "
            "Scientists discovered that forgetting isn't failure — it's optimization. "
            "When you sleep, the brain prunes weak connections to strengthen the ones that matter. "
            "This is why cramming doesn't work: you're fighting your own biology. "
            "Instead, space your learning over days. "
            "Your brain will do the rest. "
            "Next time: why emotions make memories impossible to forget."
        ),
        "keywords": ["memory", "forgetting", "brain", "psychology"],
        "quality_score": 82,
        "psychology_score": 76,
        "publish_ready": True,
        "target_platforms": ["youtube_shorts"],
        "script_package": {
            "script": "Your brain is deleting memories right now...",
            "script_score": 79,
            "scene_breakdown": [{"scene": 1, "description": "close-up of synapses"}],
        },
        "visual_package": {"scenes": [{"id": "s1"}, {"id": "s2"}]},
        "audio_package": {"voice_style": {"name": "narrator"}},
        "director_package": {"production_strategy": {"format": "short_form"}},
        "render_package": {"render_package_version": "2.0"},
    }


# ──────────────────────────────────────────────────────────
# Contract + diagnostics
# ──────────────────────────────────────────────────────────


def test_episode_design_is_a_live_contract_engine():
    engine = registry.get_engine("episode_design")
    assert isinstance(engine, ContractEngine)
    assert engine.is_ready() is True
    diag = engine.diagnostics()
    assert diag["engine_id"] == "episode_design"
    assert diag["version"] == "1.0.0"
    assert "unified_packages" in diag["input_contract"]
    assert "episode_design_summary" in diag["output_contract"]
    assert "episode_design_packages" in diag["output_contract"]
    assert "quality" in diag["dependencies"]
    assert "retention" in diag["capabilities"]
    assert "lesson-blueprint" in diag["capabilities"]
    assert engine.health_check()["healthy"] is True


# ──────────────────────────────────────────────────────────
# Package output + field contract
# ──────────────────────────────────────────────────────────


def test_every_item_receives_a_full_episode_design_package():
    items = [make_item("p1"), make_item("p2")]
    updates = registry.get_engine("episode_design").run({"unified_packages": items})

    assert len(updates["episode_design_packages"]) == 2
    for item, package in zip(items, updates["episode_design_packages"]):
        assert item["episode_design_package"] is package
        for f in EPISODE_DESIGN_PACKAGE_FIELDS:
            assert f in package, f"Missing field: {f}"


def test_lesson_blueprint_has_all_seven_beats():
    item = make_item()
    updates = registry.get_engine("episode_design").run({"unified_packages": [item]})
    pkg = updates["episode_design_packages"][0]
    blueprint = pkg["lesson_blueprint"]

    assert blueprint["total_duration_sec"] == 49
    assert len(blueprint["beats"]) == len(BLUEPRINT_BEATS)

    beat_names = {b["beat"] for b in blueprint["beats"]}
    expected = {b["beat"] for b in BLUEPRINT_BEATS}
    assert beat_names == expected

    for beat in blueprint["beats"]:
        assert beat["content_guidance"], f"Beat {beat['beat']} missing content_guidance"
        assert beat["viewer_question"], f"Beat {beat['beat']} missing viewer_question"


def test_retention_review_has_all_score_fields():
    item = make_item()
    updates = registry.get_engine("episode_design").run({"unified_packages": [item]})
    pkg = updates["episode_design_packages"][0]
    review = pkg["retention_review"]

    for field in RETENTION_SCORE_FIELDS:
        assert field in review["scores"], f"Missing score field: {field}"

    overall = review["scores"]["overall_score"]
    assert 0 <= overall <= 100, f"Overall score out of range: {overall}"
    assert isinstance(review["revisions"], list)
    assert "strategic_answers" in review


def test_summary_carries_the_full_contract():
    updates = registry.get_engine("episode_design").run({"unified_packages": [make_item()]})
    summary = updates["episode_design_summary"]
    for f in EPISODE_DESIGN_SUMMARY_FIELDS:
        assert f in summary, f"Missing summary field: {f}"
    assert summary["status"] == "designed"
    assert summary["packages"] == 1
    assert 0 <= summary["average_retention_score"] <= 100


def test_series_design_is_present_in_package():
    item = make_item()
    updates = registry.get_engine("episode_design").run({"unified_packages": [item]})
    pkg = updates["episode_design_packages"][0]
    series = pkg["series_design"]
    assert series["series_type"] in ("mini_series", "standalone", "anthology", "season")
    assert series["series_title"]
    assert isinstance(series["recurring_elements"], list)


def test_design_questions_answer_all_six_strategic_questions():
    item = make_item()
    updates = registry.get_engine("episode_design").run({"unified_packages": [item]})
    pkg = updates["episode_design_packages"][0]
    questions = pkg["design_questions"]
    for q in ("why_care", "whats_surprising", "what_first", "biggest_reveal", "where_pause", "how_end"):
        assert q in questions, f"Missing strategic answer: {q}"
        assert questions[q], f"Empty strategic answer: {q}"


# ──────────────────────────────────────────────────────────
# Slot ownership — never mutate other agents' slots
# ──────────────────────────────────────────────────────────


def test_other_agents_slots_are_never_mutated():
    item = make_item()
    before = {
        key: repr(item[key])
        for key in (
            "script_package", "visual_package", "audio_package",
            "director_package", "render_package",
        )
    }
    registry.get_engine("episode_design").run({"unified_packages": [item]})
    for key, snapshot in before.items():
        assert repr(item[key]) == snapshot, f"{key} was mutated by episode_design"


# ──────────────────────────────────────────────────────────
# Graceful degradation
# ──────────────────────────────────────────────────────────


def test_empty_context_reports_no_items_never_fails():
    updates = registry.get_engine("episode_design").run({"command": "probe"})
    assert updates["episode_design_summary"]["status"] == "no_items"
    assert updates["episode_design_summary"]["items"] == 0
    assert updates["episode_design_packages"] == []


def test_ideas_fallback_when_no_unified_packages():
    context = {"ideas": [make_item("i1")]}
    updates = registry.get_engine("episode_design").run(context)
    assert updates["episode_design_summary"]["items"] == 1
    assert context["ideas"][0]["episode_design_package"]["lesson_blueprint"]


def test_broken_item_degrades_not_a_crash():
    broken = {"project_id": "bad1", "target_platforms": object()}
    good = make_item("ok1")
    updates = registry.get_engine("episode_design").run({"unified_packages": [broken, good]})
    summary = updates["episode_design_summary"]
    assert summary["packages"] == 2
    # At least one package must have a valid status
    statuses = [
        pkg.get("validation", {}).get("status")
        for pkg in updates["episode_design_packages"]
    ]
    assert any(s in EpisodeDesignStatus.ALL for s in statuses)


# ──────────────────────────────────────────────────────────
# ContentPackage round-trip
# ──────────────────────────────────────────────────────────


def test_content_package_carries_episode_design_slot_through_roundtrip():
    package = ContentPackage(
        episode_design_package={"episode_design_package_version": "1.0", "lesson_blueprint": {}}
    )
    data = package.to_dict()
    assert data["episode_design_package"]["episode_design_package_version"] == "1.0"
    restored = ContentPackage.from_dict(data)
    assert restored.episode_design_package["episode_design_package_version"] == "1.0"


# ──────────────────────────────────────────────────────────
# Orchestrator integration
# ──────────────────────────────────────────────────────────


def test_episode_design_stage_runs_through_orchestrator():
    context = {"command": "probe", "unified_packages": [make_item("p1")]}
    report = Orchestrator().run_episode_design_stage(context)
    assert report.status == StageStatus.SUCCESS
    assert not report.errors
    assert context["episode_design_summary"]["status"] == "designed"
    assert context["unified_packages"][0]["episode_design_package"]["lesson_blueprint"]


def test_episode_design_stage_is_safe_without_input():
    context = {"command": "probe"}
    report = Orchestrator().run_episode_design_stage(context)
    assert report.status == StageStatus.SUCCESS
    assert not report.errors
    assert context["episode_design_summary"]["items"] == 0
    assert context["episode_design_packages"] == []


def test_episode_design_then_ai_director_both_write_own_slots():
    """Episode Design runs before AI Director — each owns its slot."""
    item = make_item()
    context = {"unified_packages": [item]}

    registry.get_engine("episode_design").run(context)
    assert item["episode_design_package"]["lesson_blueprint"]

    registry.get_engine("ai_director").run(context)
    assert item["director_package"]["production_strategy"]
    # Episode Design slot is untouched by AI Director
    assert item["episode_design_package"]["lesson_blueprint"]["topic"]


# ──────────────────────────────────────────────────────────
# Playbook persistence
# ──────────────────────────────────────────────────────────


def test_playbook_persists_and_retrieves_patterns(tmp_path):
    from services.episode_design.playbook import EpisodePlaybook

    pb = EpisodePlaybook(data_dir=tmp_path)
    pid = pb.record_pattern(
        pattern_name="Curiosity Hook + Reveal",
        niche="Science",
        description="Open with a counterintuitive question, reveal in explanation beat.",
        strengths=["high curiosity score", "strong ending"],
        weaknesses=["requires strong visual demonstration"],
    )
    assert pid

    found = pb.get_pattern(pid)
    assert found["pattern_name"] == "Curiosity Hook + Reveal"
    assert found["niche"] == "Science"

    pb.record_success(pid, project_id="proj_test", retention_score=85)
    found2 = pb.get_pattern(pid)
    assert found2["times_used"] == 1
    assert found2["average_retention_score"] == 85

    # Reload from disk to prove persistence
    pb2 = EpisodePlaybook(data_dir=tmp_path)
    reloaded = pb2.get_pattern(pid)
    assert reloaded["pattern_name"] == "Curiosity Hook + Reveal"
    assert reloaded["times_used"] == 1


def test_playbook_summary_is_correct(tmp_path):
    from services.episode_design.playbook import EpisodePlaybook

    pb = EpisodePlaybook(data_dir=tmp_path)
    pb.record_pattern("Pattern A", "Psychology", "A test pattern")
    pb.record_pattern("Pattern B", "Science", "Another test pattern")
    summary = pb.summary()
    assert summary["pattern_count"] == 2
    assert "Psychology" in summary["niches_covered"]
    assert "Science" in summary["niches_covered"]


# ──────────────────────────────────────────────────────────
# AST: episode_design modules do not import peer engines.*
# ──────────────────────────────────────────────────────────


def test_episode_design_modules_do_not_import_peer_engines():
    """Directive #1: episode_design service modules must not import engines.*
    other than the shared foundation (engines.base, engines.contracts, etc.)."""
    allowed = {
        "engines",
        "engines.base",
        "engines.contracts",
        "engines.heuristics",
        "engines.analysis",
        "engines.registry",
    }
    services_dir = Path(__file__).resolve().parent.parent / "services" / "episode_design"
    violations = []
    for py_file in sorted(services_dir.glob("*.py")):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if (alias.name.startswith("engines.") or alias.name == "engines") and alias.name not in allowed:
                        violations.append(f"{py_file.name}: imports {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module
                if (mod.startswith("engines.") or mod == "engines") and mod not in allowed:
                    violations.append(f"{py_file.name}: imports from {mod}")
    assert not violations, (
        "episode_design service modules violate Directive #1:\n  " + "\n  ".join(violations)
    )
