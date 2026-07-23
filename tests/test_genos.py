"""Tests for GenOS — orchestration only."""

from __future__ import annotations

from services.generational_os.departments import OPERATING_LOOP, department_health, list_departments
from services.generational_os.errors import classify_error, should_retry
from services.generational_os.resources import estimate_production_cost
from services.generational_os.scheduler import has_duplicate, schedule_production


def test_departments_cover_v1_stack():
    keys = {d["key"] for d in list_departments()}
    for required in (
        "trend_opportunity",
        "research",
        "psychology",
        "world_builder",
        "visual_asset_director",
        "cinematic_director",
        "voice_studio",
        "audience_intelligence",
        "publishing_intelligence",
        "production_operations",
    ):
        assert required in keys
    assert len(OPERATING_LOOP) >= 15
    health = department_health()
    assert health["available_count"] >= 10


def test_error_classification_retry_policy():
    lim = classify_error("ElevenLabs quota exceeded 429")
    assert lim["class"] == "api_limit"
    assert lim["retryable"] is True
    auth = classify_error("Unauthorized invalid api key 401")
    assert auth["class"] == "authentication"
    assert auth["escalate"] is True
    assert should_retry(lim, attempt=1) is True
    assert should_retry(auth, attempt=1) is False


def test_cost_estimate():
    cost = estimate_production_cost(length_sec=45, used_elevenlabs=True, used_images=5)
    assert cost["estimated_usd"] > 0
    assert "elevenlabs_usd" in cost["breakdown"]


def test_schedule_and_dedupe(monkeypatch, tmp_path):
    from services.generational_os import scheduler as sched

    monkeypatch.setattr(sched, "GENOS_QUEUE", tmp_path / "PRODUCTION_QUEUE.json")

    calls = {"n": 0}

    def fake_enqueue(**kwargs):
        calls["n"] += 1
        return {"job_id": f"job_{calls['n']}", "status": "pending", "result": None}

    monkeypatch.setattr(sched, "enqueue_production", fake_enqueue)
    monkeypatch.setattr(sched, "ensure_ops_queue_handler", lambda: None)

    a = schedule_production(topic="Why ice floats on water", priority=90, run_immediately=False)
    assert a["ok"] is True
    assert a["job"]["priority"] == 90
    assert a["job"]["current_stage"] == "queued"

    dup = schedule_production(topic="Why ice floats on water", priority=10, run_immediately=False)
    assert dup["ok"] is False
    assert dup["duplicate"] is True
    assert has_duplicate("Why ice floats on water") is not None


def test_cycle_no_execute(tmp_path, monkeypatch):
    from services.generational_os import genos as genos_mod
    from services.generational_os import scheduler as sched
    from services.trend_opportunity.brief import build_production_brief
    from services.trend_opportunity.scoring import score_opportunity_card
    import services.trend_opportunity as toi

    monkeypatch.setattr(sched, "GENOS_QUEUE", tmp_path / "PRODUCTION_QUEUE.json")

    def fake_enqueue(**kwargs):
        return {"job_id": f"j_{str(kwargs.get('topic', ''))[:8]}", "status": "pending", "result": None}

    monkeypatch.setattr(sched, "enqueue_production", fake_enqueue)
    monkeypatch.setattr(sched, "ensure_ops_queue_handler", lambda: None)

    def fake_trends(*a, **k):
        opps = []
        for i, topic in enumerate(
            [
                "Why ice floats on water",
                "How vaccines train the immune system",
                "Why the moon controls tides",
                "How plants make oxygen",
                "Why volcanoes erupt",
            ]
        ):
            scored = score_opportunity_card(topic, category="science")
            brief = build_production_brief(topic, scores=scored, category="science")
            opps.append(
                {
                    "topic": topic,
                    "overall_opportunity_score": scored["overall_opportunity_score"],
                    "production_priority": 90 - i,
                    "production_brief": brief,
                    "confidence": 0.8,
                }
            )
        return {"ok": True, "top_opportunities": opps, "production_briefs": [o["production_brief"] for o in opps]}

    monkeypatch.setattr(toi, "run_trend_opportunity", fake_trends)
    monkeypatch.setattr(
        genos_mod,
        "generate_all_reports",
        lambda publishing_enabled=False: {
            "DAILY_REPORT.md": str(tmp_path / "DAILY_REPORT.md"),
            "SYSTEM_STATE.json": str(tmp_path / "SYSTEM_STATE.json"),
        },
    )
    monkeypatch.setattr(genos_mod, "write_system_state", lambda publishing_enabled=False: tmp_path / "SYSTEM_STATE.json")
    (tmp_path / "SYSTEM_STATE.json").write_text("{}", encoding="utf-8")

    out = genos_mod.run_operating_cycle(
        category="science",
        queue_count=5,
        execute_one=False,
        publishing_enabled=False,
        top_n=5,
    )
    assert out["ok"] is True
    assert out["queued_ok_count"] == 5
    assert out["publishing_enabled"] is False
    assert out.get("report_paths")
    assert "DAILY_REPORT.md" in out["report_paths"]
