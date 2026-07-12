"""Tests for Generational OS V2.5."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.generational_os.export_classifier import classify_domain, export_root
from services.generational_os.pipeline import STAGE_ORDER, ProductionStage
from services.generational_os.brief import build_production_brief


def test_classify_biology_turtle():
    assert classify_domain(filename="Biology_001_202_Origin_of_Turtles.mp4", demo_id="foundation_v2_turtle_202") == "Biology"


def test_export_root_structure():
    path = export_root()
    assert path.name == "Videos"
    assert "AI Start-Up" in path.parts


def test_pipeline_order():
    assert STAGE_ORDER[0] == ProductionStage.IDEA.value
    assert ProductionStage.LOCAL_PRODUCTION.value in STAGE_ORDER
    assert STAGE_ORDER[-1] == ProductionStage.ANALYTICS.value


def test_production_brief_schema():
    brief = build_production_brief(
        project_id="turtle_202",
        title="Origin of Turtles",
        subject="Turtle evolution",
        hook="Hook?",
        takeaway="Takeaway.",
        main_concept="Shell evolution",
        educational_objective="Understand gradual shell formation",
        domain="Biology",
    )
    assert brief["layer"] == "intelligence"
    assert brief["domain"] == "Biology"


if __name__ == "__main__":
    test_classify_biology_turtle()
    test_export_root_structure()
    test_pipeline_order()
    test_production_brief_schema()
    print("all generational_os tests passed")
