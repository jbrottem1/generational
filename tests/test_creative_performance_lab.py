"""Unit tests for Creative Performance Lab — no live API / no publish."""

from __future__ import annotations

import pytest

from services.creative_performance_lab.experiment import create_experiment
from services.creative_performance_lab.evaluation import evaluate_experiment
from services.creative_performance_lab.guidance import guidance_for_production
from services.creative_performance_lab.knowledge import add_learning, search_learnings
from services.creative_performance_lab.models import CONTROLLED_VARIABLES
from services.creative_performance_lab.produce import HOOKS, OCTOPUS_BODY, build_controlled_hook_scripts
from services.creative_performance_lab.store import load_experiment, save_experiment


def test_controlled_variable_list():
    assert "hook_structure" in CONTROLLED_VARIABLES
    assert "thumbnail" in CONTROLLED_VARIABLES


def test_create_experiment_rejects_multi_variable_without_exploratory():
    with pytest.raises(ValueError):
        create_experiment(
            topic="t",
            variables_tested=["hook_structure", "thumbnail"],
            exploratory=False,
        )


def test_octopus_hooks_differ_only_in_hook():
    scripts = build_controlled_hook_scripts()
    assert len(scripts) == 3
    bodies = {s["body_constant"] for s in scripts}
    assert bodies == {OCTOPUS_BODY}
    hooks = {s["hook"] for s in scripts}
    assert len(hooks) == 3
    assert set(HOOKS) == {"A", "B", "C"}


def test_evaluate_without_analytics_is_insufficient(tmp_path, monkeypatch):
    exp = create_experiment(topic="t", variables_tested=["hook_structure"])
    result = evaluate_experiment(exp["experiment_id"])
    assert result["status"] == "INSUFFICIENT_DATA"


def test_knowledge_and_guidance_do_not_force():
    add_learning(
        creative_variable="hook_structure",
        winning_pattern="curiosity_gap",
        losing_pattern="definition",
        topic_category="science",
        platform="youtube_shorts",
        sample_size=50,
        confidence=0.2,
    )
    rows = search_learnings(creative_variable="hook_structure", limit=5)
    assert rows
    guide = guidance_for_production(topic="science", platform="youtube_shorts")
    assert guide["policy"]
    assert all(not r.get("forced") for r in guide["recommendations"])


def test_lab_refuses_auto_publish():
    from services.creative_performance_lab.lab import run_controlled_experiment

    with pytest.raises(ValueError):
        run_controlled_experiment(topic="x", publish=True)
