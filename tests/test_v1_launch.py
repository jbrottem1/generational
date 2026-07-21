"""V1 Launch Program — catalog and recommendation logic (no live ops)."""

from __future__ import annotations

from services.v1_launch.executive import decide_launch_recommendation
from services.v1_launch.pilot_catalog import build_pilot_catalog, filter_pilot


def test_pilot_catalog_is_25_across_six_categories():
    cat = build_pilot_catalog()
    assert len(cat) == 25
    cats = {r["launch_category"] for r in cat}
    assert cats == {
        "biology",
        "artificial_intelligence",
        "astronomy",
        "physics",
        "psychology",
        "medicine",
    }
    assert len(filter_pilot(categories=["ai", "space"], limit=3)) <= 3


def test_launch_recommendation_requires_mp4_rate():
    dash = {
        "videos_in_pilot": 25,
        "production_success_rate": 1.0,
        "deliverable_mp4_rate": 0.1,
        "average_program_score": 85.0,
        "top_5_improvements": [],
        "strongest_categories": [],
        "weakest_categories": [],
        "failure_causes": [],
    }
    rec = decide_launch_recommendation(dash)
    assert rec["decision"] == "NOT_READY"

    dash["deliverable_mp4_rate"] = 0.95
    dash["production_success_rate"] = 0.95
    rec2 = decide_launch_recommendation(dash)
    assert rec2["decision"] == "READY_FOR_LAUNCH"
