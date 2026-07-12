"""Tests for Knowledge & Standards (Agent 27)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.knowledge_standards import (
    KnowledgeValidationError,
    load_experiment_registry,
    record_lesson,
    register_experiment,
    validate_experiment,
    validate_lesson,
    validate_standard_markers,
)
from services.knowledge_standards.capture import KNOWLEDGE_STANDARDS_DIR

REPO = Path(__file__).resolve().parents[1]
KS = REPO / "data" / "knowledge_standards"
NAMED_DOCS = (
    "COMPANY_WIKI.md",
    "PRODUCTION_STANDARDS.md",
    "PROMPT_LIBRARY.md",
    "LESSONS_LEARNED.md",
    "EXPERIMENT_REGISTRY.md",
    "BEST_PRACTICES.md",
    "STYLE_GUIDES.md",
)


def test_named_docs_and_root_pointer_exist():
    for name in NAMED_DOCS:
        assert (KS / name).is_file(), name
    assert (KS / "experiments.json").is_file()
    assert (KS / "registry.json").is_file()
    assert (REPO / "COMPANY_WIKI.md").is_file()
    root = (REPO / "COMPANY_WIKI.md").read_text(encoding="utf-8")
    assert "data/knowledge_standards/COMPANY_WIKI.md" in root


def test_lessons_index_does_not_duplicate_full_gcis_body():
    index = (KS / "LESSONS_LEARNED.md").read_text(encoding="utf-8")
    gcis = (REPO / "data" / "gcis" / "knowledge" / "lessons_learned.md").read_text(encoding="utf-8")
    assert "data/gcis/knowledge/lessons_learned.md" in index
    assert "canonical" in index.lower() or "Canonical" in index
    # Index should be much shorter than the full log
    assert len(index) < len(gcis)
    # Should not copy standing anti-patterns section wholesale
    assert "Standing anti-patterns (do not repeat)" not in index


def test_load_experiment_registry():
    registry = load_experiment_registry()
    assert "experiments" in registry
    experiments = registry["experiments"]
    assert len(experiments) >= 4
    ids = {e["id"] for e in experiments}
    assert "EXP-FLUID-MOTION" in ids
    assert "EXP-SPRINT-6H30" in ids
    assert "EXP-FOUNDATION" in ids
    assert "EXP-ES001" in ids
    for exp in experiments:
        validate_experiment(exp)


def test_validate_lesson_rejects_empty():
    with pytest.raises(KnowledgeValidationError, match="title"):
        validate_lesson(title="  ", source="sprint", what_worked=["x"])
    with pytest.raises(KnowledgeValidationError, match="source"):
        validate_lesson(title="T", source="", what_worked=["x"])
    with pytest.raises(KnowledgeValidationError, match="what_worked"):
        validate_lesson(title="T", source="S")


def test_validate_experiment_rejects_duplicate_fields_missing():
    with pytest.raises(KnowledgeValidationError, match="missing"):
        validate_experiment({"id": "X"})


def test_register_experiment_rejects_duplicate_id(tmp_path: Path):
    src = KS / "experiments.json"
    target = tmp_path / "experiments.json"
    target.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    existing = load_experiment_registry(target)["experiments"][0]
    with pytest.raises(KnowledgeValidationError, match="Duplicate"):
        register_experiment(dict(existing), path=target, dry_run=False)


def test_register_experiment_dry_run_and_write(tmp_path: Path):
    src = KS / "experiments.json"
    target = tmp_path / "experiments.json"
    target.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    new_exp = {
        "id": "EXP-TEST-UNIT",
        "objective": "Unit test registration",
        "method": "pytest dry/write",
        "variables": ["tmp"],
        "outcome": "Registered in temp file",
        "metrics": {"ok": True},
        "decision": "discard",
        "lessons": ["Temp experiments stay out of prod registry"],
        "date": "2026-07-11",
    }
    entry = register_experiment(new_exp, path=target, dry_run=True)
    assert entry["id"] == "EXP-TEST-UNIT"
    assert all(e["id"] != "EXP-TEST-UNIT" for e in load_experiment_registry(target)["experiments"])

    register_experiment(new_exp, path=target, dry_run=False)
    ids = {e["id"] for e in load_experiment_registry(target)["experiments"]}
    assert "EXP-TEST-UNIT" in ids


def test_record_lesson_dry_run_and_append(tmp_path: Path):
    lessons = tmp_path / "lessons_learned.md"
    lessons.write_text("# Lessons Learned (GCIS)\n\n", encoding="utf-8")
    block = record_lesson(
        "Unit capture",
        source="test_knowledge_standards",
        what_worked=["dry_run path works"],
        lessons_path=lessons,
        dry_run=True,
    )
    assert "Unit capture" in block
    assert "Unit capture" not in lessons.read_text(encoding="utf-8")

    record_lesson(
        "Unit capture",
        source="test_knowledge_standards",
        what_worked=["append works"],
        standard="Always use dry_run in tests first",
        lessons_path=lessons,
        dry_run=False,
    )
    text = lessons.read_text(encoding="utf-8")
    assert "Unit capture" in text
    assert "append works" in text
    assert "agent_27" in text


def test_validate_standard_markers_conflict():
    ok = validate_standard_markers("| LOCKED | Purposeful gestures |\n| ASPIRATIONAL | Phonemes |")
    assert ok == []
    conflicts = validate_standard_markers("| LOCKED ASPIRATIONAL | bad row |")
    assert len(conflicts) == 1
    with pytest.raises(KnowledgeValidationError):
        validate_standard_markers("   ")


def test_registry_manifest_lists_assets():
    manifest = json.loads((KS / "registry.json").read_text(encoding="utf-8"))
    assert manifest["owner_agent"] == 27
    paths = {a["path"] for a in manifest["assets"]}
    assert "data/knowledge_standards/COMPANY_WIKI.md" in paths
    assert "data/gcis/knowledge/lessons_learned.md" in paths
    assert KNOWLEDGE_STANDARDS_DIR == KS
