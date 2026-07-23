"""Tests for Executive Orchestrator — one-command studio entry point."""

from __future__ import annotations

import engines  # noqa: F401
from core.workflows import WORKFLOWS
from engines import registry
from services.executive_orchestrator import (
    EXECUTIVE_STAGES,
    create_video,
    parse_production_request,
    stage_plan,
)
from services.executive_orchestrator.revision_loop import (
    collect_revision_engines,
    run_revision_loop,
)
from services.executive_orchestrator.state import get_run_registry


def test_parse_youtube_short_infrared():
    brief = parse_production_request(
        "Create a 60 second YouTube Short explaining why cameras can see infrared."
    )
    assert brief.runtime_sec == 60
    assert "youtube_shorts" in brief.platforms
    assert "infrared" in brief.topic.lower()
    assert brief.format == "short"


def test_parse_documentary_black_holes():
    brief = parse_production_request("Create a 12 minute documentary about black holes.")
    assert brief.runtime_sec == 12 * 60
    assert brief.format == "documentary"
    assert "black holes" in brief.topic.lower()
    assert brief.primary_platform in ("youtube", "youtube_long") or "youtube" in brief.platforms[0]


def test_parse_tiktok_default_runtime():
    brief = parse_production_request("Create a TikTok about photosynthesis")
    assert brief.runtime_sec == 60
    assert "tiktok" in brief.platforms


def test_stage_plan_covers_dashboard_stages():
    plan = stage_plan()
    keys = [p["key"] for p in plan]
    assert keys == list(EXECUTIVE_STAGES)
    assert "discovery" in keys and "publishing" in keys and "qa" in keys


def test_plan_only_create_video():
    result = create_video(
        "Create a 60 second YouTube Short explaining why cameras can see infrared.",
        plan_only=True,
        skip_publishing=True,
    )
    assert result["status"] == "completed"
    assert result["topic"]
    assert result["runtime_sec"] == 60
    assert all(result["stages"][k]["status"] == "completed" for k in EXECUTIVE_STAGES)
    assert result["export_paths"].get("seo_metadata")
    assert result.get("log_path")
    assert get_run_registry().get(result["id"]) is not None


def test_revision_loop_routes_engines():
    context = {
        "selected_ideas": [
            {
                "title": "test",
                "pqa_decision": "REQUEST_REVISION",
                "pqa_revision_requests": [
                    {
                        "category": "evidence",
                        "score": 70,
                        "target_engines": ["evidence_intelligence"],
                        "severity": "revision",
                        "message": "need photos",
                        "corrections": [],
                    }
                ],
            }
        ],
        "pqa_revision_by_engine": {"evidence_intelligence": [{"category": "evidence"}]},
        "pqa_summary": {"request_revision": 1, "blocked": 0},
    }
    assert "evidence_intelligence" in collect_revision_engines(context)

    # One round: revision engines then QA — use empty targets by clearing after first inspect
    # Mark approved so loop exits quickly after one QA if we mutate
    class FakeWF:
        def __init__(self):
            self.calls = []

        def execute(self, engines, context):
            self.calls.append(list(engines))
            # After any run, approve to stop
            for item in context.get("selected_ideas") or []:
                item["pqa_decision"] = "APPROVE"
                item["pqa_score"] = 95
            context["pqa_passed"] = True
            context["pqa_summary"] = {"request_revision": 0, "blocked": 0, "approved": 1}

            class R:
                def summary(self_inner):
                    return {"steps": [{"engine": e, "status": "succeeded"} for e in engines]}

            return R()

    wf = FakeWF()
    # Reset to request revision for first iteration
    context["selected_ideas"][0]["pqa_decision"] = "REQUEST_REVISION"
    context["pqa_passed"] = False
    summary = run_revision_loop(context, workflows=wf, max_rounds=2)
    assert summary["rounds"] >= 1
    assert any("evidence_intelligence" in call for call in wf.calls)
    assert summary["approved"] is True


def test_engine_registered():
    engine = registry.get_engine("executive_orchestrator")
    assert engine is not None
    assert engine.is_ready()
    out = engine.run(
        {
            "command": "Create a 45 second Short about coral reefs",
            "plan_only": True,
            "skip_publishing": True,
        }
    )
    assert out["executive_run"]["status"] == "completed"
    assert out["executive_dashboard"]["completed_count"] >= 1


def test_workflow_executive_key():
    assert WORKFLOWS["executive"] == ["executive_orchestrator"]


def test_dashboard_shape():
    create_video("Create a TikTok about tides", plan_only=True, skip_publishing=True)
    dash = get_run_registry().dashboard()
    assert "stages" in dash
    assert len(dash["stages"]) == len(EXECUTIVE_STAGES)
    assert "active_count" in dash
