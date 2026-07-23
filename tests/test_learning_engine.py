"""Tests for the Learning Engine (Agent 9, key: learning).

Proves: pattern mining finds winners and losers with confidence scores,
recommendations route to the engines that own each decision, the
experimentation framework determines statistical winners, long-term memory
is cumulative and never overwritten, reports are machine- and
human-readable, and the closed loop runs end-to-end through the
orchestrator — every published video makes the next one more intelligent.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

import engines  # noqa: F401 - importing registers all engines
from engines import registry
from engines.contracts import ContractEngine
from services.learning import (
    EXPERIMENT_KINDS,
    ExperimentManager,
    ExperimentStatus,
    HistoricalMemory,
    INSIGHT_FIELDS,
    LEARNING_METADATA_FIELDS,
    MEMORY_CATEGORY,
    RECOMMENDATION_FIELDS,
    TARGET_ENGINES,
    best_performers,
    build_performance_report,
    build_recommendations,
    compare_variants,
    mine_patterns,
    platform_breakdown,
    psychology_guidance,
    recommendations_by_engine,
    render_report_text,
    seo_guidance,
)
from services.orchestrator import Orchestrator, StageStatus, get_orchestrator


@pytest.fixture
def analytics_dir(tmp_path, monkeypatch):
    """Function-scoped isolation of the whole Agent 9 persistence layer."""
    import services.analytics.store as analytics_store

    directory = str(tmp_path / "analytics")
    monkeypatch.setattr(analytics_store, "_DEFAULT_DIR", directory)
    return directory


def make_record(
    hook="strong hook",
    strategy="curiosity",
    platform="youtube_shorts",
    topic="oceans",
    retention=80,
    ctr=10,
    views=50_000,
    posting_time="2026-07-08T17:00:00+00:00",
):
    """One collected analytics record with controllable outcome quality."""
    return {
        "record_id": "r",
        "analytics_ref": "",
        "project_id": "p",
        "platform": platform,
        "topic": topic,
        "niche": "science",
        "title": f"Title for {hook}",
        "hook": hook,
        "keywords": ["ocean"],
        "psychology_strategy": [strategy],
        "video_length_sec": 45.0,
        "posting_time": posting_time,
        "published_at": posting_time,
        "experiment_id": "",
        "variant_id": "",
        "metrics": {
            "views": views,
            "watch_time_sec": views * 20,
            "average_view_duration_sec": 20,
            "audience_retention": retention,
            "ctr": ctr,
            "likes": views // 50,
            "comments": views // 500,
            "shares": views // 300,
            "saves": views // 400,
            "subscriber_growth": 10,
            "followers_gained": 25,
            "rpm": 0,
            "cpm": 0,
        },
        "metrics_status": "collected",
        "metrics_source": "mock",
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }


def winning_and_losing_history():
    """Six records: a hook/strategy that clearly wins and one that loses."""
    winners = [
        make_record(hook="WIN hook", strategy="curiosity", retention=85, ctr=12, views=80_000)
        for _ in range(3)
    ]
    losers = [
        make_record(hook="LOSE hook", strategy="fear", retention=25, ctr=2, views=1_500)
        for _ in range(3)
    ]
    return winners + losers


# ----------------------------------------------------------------- contract


def test_learning_engine_is_a_live_contract_engine():
    engine = registry.get_engine("learning")
    assert isinstance(engine, ContractEngine)
    assert engine.is_ready() is True
    diag = engine.diagnostics()
    assert diag["engine_id"] == "learning"
    assert "analytics_summary" in diag["input_contract"]
    assert "learning_report" in diag["output_contract"]
    assert "analytics" in diag["dependencies"]


# ------------------------------------------------------------ pattern mining


def test_mine_patterns_identifies_winners_and_losers_with_confidence():
    insights = mine_patterns(winning_and_losing_history())
    assert insights
    for insight in insights:
        for field in INSIGHT_FIELDS:
            assert field in insight, field

    hooks = {i["value"]: i for i in insights if i["dimension"] == "hook"}
    assert hooks["WIN hook"]["lift"] > 0
    assert hooks["LOSE hook"]["lift"] < 0
    assert hooks["WIN hook"]["samples"] == 3
    assert 0 < hooks["WIN hook"]["confidence"] <= 100


def test_confidence_grows_with_sample_size():
    few = mine_patterns([make_record(hook="h", retention=80)] * 2)
    many = mine_patterns([make_record(hook="h", retention=80)] * 10)
    conf_few = next(i for i in few if i["dimension"] == "hook")["confidence"]
    conf_many = next(i for i in many if i["dimension"] == "hook")["confidence"]
    assert conf_many > conf_few


def test_best_performers_and_platform_breakdown():
    records = winning_and_losing_history() + [
        make_record(hook="tiktok hook", platform="tiktok", retention=70, views=60_000)
    ]
    top_hooks = best_performers(records, "hook", limit=2)
    assert top_hooks[0]["value"] == "WIN hook"

    breakdown = platform_breakdown(records)
    assert set(breakdown) == {"youtube_shorts", "tiktok"}
    assert breakdown["tiktok"]["samples"] == 1


def test_mining_empty_or_pending_records_yields_no_insights():
    assert mine_patterns([]) == []
    pending = make_record()
    pending["metrics_status"] = "pending"
    assert mine_patterns([pending]) == []


# ----------------------------------------------------------- recommendations


def test_recommendations_route_to_owning_engines_with_evidence():
    insights = mine_patterns(winning_and_losing_history())
    recommendations = build_recommendations(insights)
    assert recommendations
    for rec in recommendations:
        for field in RECOMMENDATION_FIELDS:
            assert field in rec, field
        assert rec["target_engine"] in TARGET_ENGINES

    routed = recommendations_by_engine(recommendations)
    assert set(routed) == set(TARGET_ENGINES)
    # The winning psychology strategy reaches the Psychology Engine...
    assert any(r["value"] == "curiosity" for r in routed["psychology"])
    # ...and the winning hook reaches the Script Engine.
    assert any(r["value"] == "WIN hook" for r in routed["script_generation"])


def test_single_sample_signals_do_not_become_strategy():
    one_off = [make_record(hook="lucky one-off", retention=95, views=99_000)]
    one_off += [make_record(hook="steady", retention=50, views=10_000) for _ in range(2)]
    recommendations = build_recommendations(mine_patterns(one_off))
    assert not any(r["value"] == "lucky one-off" for r in recommendations)


def test_guidance_adapters_speak_each_engines_language():
    insights = mine_patterns(winning_and_losing_history())
    recommendations = build_recommendations(insights)

    psych = psychology_guidance(recommendations)
    assert "curiosity" in psych["preferred_strategies"]
    assert "fear" in psych["avoided_strategies"]

    seo = seo_guidance(recommendations)
    assert set(seo) >= {"winning_keywords", "winning_titles", "best_posting_hours", "platform_weights"}


# -------------------------------------------------------------- experiments


def test_experiment_lifecycle_determines_statistical_winner(analytics_dir):
    manager = ExperimentManager(directory=analytics_dir)
    experiment = manager.create_experiment(
        "thumbnail", "Bold vs subtle", [{"label": "bold"}, {"label": "subtle"}],
        hypothesis="Bold thumbnails lift CTR", min_samples=3,
    )
    assert experiment["kind"] in EXPERIMENT_KINDS
    assert experiment["status"] == ExperimentStatus.RUNNING

    # Deterministic, sticky round-robin assignment.
    variant_a = manager.assign_variant(experiment["experiment_id"], "content_1")
    variant_b = manager.assign_variant(experiment["experiment_id"], "content_2")
    assert variant_a["variant_id"] != variant_b["variant_id"]
    assert manager.assign_variant(experiment["experiment_id"], "content_1") == variant_a

    strong = {"views": 80_000, "audience_retention": 85, "ctr": 12,
              "likes": 4000, "comments": 300, "shares": 500, "saves": 400}
    weak = {"views": 2_000, "audience_retention": 25, "ctr": 2,
            "likes": 20, "comments": 2, "shares": 3, "saves": 1}
    for _ in range(3):
        manager.record_result(experiment["experiment_id"], variant_a["variant_id"], strong)
        result = manager.record_result(experiment["experiment_id"], variant_b["variant_id"], weak)

    assert result["status"] == ExperimentStatus.COMPLETED
    assert result["winner"]["variant_id"] == variant_a["variant_id"]
    assert result["winner"]["confidence"] >= 90
    assert result["winner"]["lift"] > 0

    # The concluded experiment became cumulative long-term memory.
    memory = HistoricalMemory(directory=analytics_dir)
    outcomes = memory.recall(MEMORY_CATEGORY.EXPERIMENT_OUTCOMES)
    assert outcomes and outcomes[0]["content"]["experiment_id"] == experiment["experiment_id"]


def test_experiment_withholds_judgment_without_enough_samples(analytics_dir):
    manager = ExperimentManager(directory=analytics_dir)
    experiment = manager.create_experiment("hook", "A vs B", ["hook A", "hook B"], min_samples=5)
    manager.record_result(
        experiment["experiment_id"], experiment["variants"][0]["variant_id"],
        {"views": 50_000, "audience_retention": 80, "ctr": 10},
    )
    updated = manager.get_experiment(experiment["experiment_id"])
    assert updated["status"] == ExperimentStatus.RUNNING
    assert updated["winner"] == {}


def test_experiment_validation():
    manager = ExperimentManager(directory="unused")
    with pytest.raises(ValueError):
        manager.create_experiment("nonsense_kind", "x", ["a", "b"])
    with pytest.raises(ValueError):
        manager.create_experiment("ab", "x", ["only one variant"])


def test_compare_variants_statistics():
    even = compare_variants([50, 50, 50], [50, 50, 50])
    assert even["confidence"] == 50.0
    decisive = compare_variants([90, 88, 92], [20, 22, 18])
    assert decisive["confidence"] > 99
    assert decisive["lift"] > 60


# ------------------------------------------------------------------- memory


def test_memory_is_cumulative_and_never_overwrites(tmp_path):
    memory = HistoricalMemory(directory=str(tmp_path / "mem"))
    first = memory.remember(MEMORY_CATEGORY.SUCCESSFUL_STRATEGIES, {"value": "curiosity hooks"}, confidence=80)
    second = memory.remember(MEMORY_CATEGORY.SUCCESSFUL_STRATEGIES, {"value": "curiosity hooks"}, confidence=90)

    entries = memory.recall(MEMORY_CATEGORY.SUCCESSFUL_STRATEGIES)
    assert len(entries) == 2                       # append-only: both survive
    assert entries[0]["entry_id"] == second["entry_id"]  # newest first
    assert entries[1]["entry_id"] == first["entry_id"]
    assert memory.count() == 2

    with pytest.raises(ValueError):
        memory.remember("not_a_category", "x")


def test_memory_search_and_category_counts(tmp_path):
    memory = HistoricalMemory(directory=str(tmp_path / "mem"))
    memory.remember(MEMORY_CATEGORY.PLATFORM_TRENDS, {"value": "tiktok favors fast cuts"})
    memory.remember(MEMORY_CATEGORY.AUDIENCE_PREFERENCES, {"value": "under_30s videos"})

    assert memory.search("tiktok")[0]["category"] == MEMORY_CATEGORY.PLATFORM_TRENDS
    counts = memory.counts_by_category()
    assert counts[MEMORY_CATEGORY.PLATFORM_TRENDS] == 1
    assert counts[MEMORY_CATEGORY.FAILED_STRATEGIES] == 0


# ------------------------------------------------------------------ reports


def test_performance_report_is_machine_and_human_readable():
    records = winning_and_losing_history()
    report = build_performance_report(records, period="daily")

    from services.learning import PERFORMANCE_REPORT_FIELDS

    for field in PERFORMANCE_REPORT_FIELDS:
        assert field in report, field
    assert report["totals"]["records"] == 6
    assert report["top_content"][0]["performance_score"] >= report["top_content"][-1]["performance_score"]
    assert report["worst_content"][0]["performance_score"] <= report["top_content"][0]["performance_score"]
    assert report["engine_recommendations"]["psychology"]
    assert report["optimization_priorities"]

    text = render_report_text(report)
    assert "Performance Report" in text
    assert "Top Performing Content" in text
    assert "Engine Recommendations" in text


def test_report_periods_window_records():
    stale = make_record()
    stale["collected_at"] = "2020-01-01T00:00:00+00:00"
    report = build_performance_report([stale] + winning_and_losing_history(), period="weekly")
    assert report["totals"]["records"] == 6      # the 2020 record fell outside

    with pytest.raises(ValueError):
        build_performance_report([], period="hourly")


# -------------------------------------------------------------- engine run


def test_learning_engine_writes_metadata_and_recommendations(analytics_dir):
    from services.analytics.store import AnalyticsStore

    AnalyticsStore(directory=analytics_dir).add_records(winning_and_losing_history())

    item = {"project_id": "p1", "hook": "WIN hook", "topic": "oceans",
            "target_platforms": ["youtube_shorts"]}
    context = {"unified_packages": [item], "analytics_summary": {"records": 6}}
    updates = registry.get_engine("learning").run(context)

    report = updates["learning_report"]
    assert report["status"] == "learned"
    assert report["records_analyzed"] == 6
    assert report["recommendations"]
    assert updates["learning_recommendations"]["psychology"]

    metadata = item["learning_metadata"]
    for field in LEARNING_METADATA_FIELDS:
        assert field in metadata, field
    assert metadata["status"] == "learned"
    assert metadata["knowledge_size"] == 6
    # The item's own winning hook shows up in its signals.
    assert any(signal["value"] == "WIN hook" for signal in metadata["signals"])


def test_learning_grows_long_term_memory_without_duplicates(analytics_dir):
    from services.analytics.store import AnalyticsStore

    AnalyticsStore(directory=analytics_dir).add_records(winning_and_losing_history())
    engine = registry.get_engine("learning")

    first = engine.run({})["learning_report"]
    assert first["memory_entries_added"] > 0

    # Re-learning the same history adds nothing new — cumulative, not noisy.
    second = engine.run({})["learning_report"]
    assert second["memory_entries_added"] == 0
    memory = HistoricalMemory(directory=analytics_dir)
    assert memory.count() > 0


# --------------------------------------------------------------- closed loop


def test_full_closed_loop_through_the_orchestrator(analytics_dir):
    """Publish (immediate, mock) → analytics stage → learning stage:
    analytics_package and learning_metadata land on every published
    package, the store grows, and the next run's guidance exists."""
    result = get_orchestrator().run_full_pipeline(
        "Create 2 science shorts about volcano lightning",
        count=2, threshold=0, publish_mode="immediate",
    )
    assert result.succeeded

    orch = Orchestrator()
    analytics_report = orch.run_analytics_stage(result.context)
    assert analytics_report.status == StageStatus.SUCCESS
    assert result.context["analytics_summary"]["collected"] > 0

    learning_report = orch.run_learning_stage(result.context)
    assert learning_report.status == StageStatus.SUCCESS
    assert result.context["learning_report"]["records_analyzed"] > 0
    assert result.context["learning_recommendations"]

    for package in result.context["unified_packages"]:
        if package.get("publishing_package", {}).get("status") == "published":
            assert package["analytics_package"]["status"] == "collected"
            assert package["learning_metadata"]["status"] in ("learned", "insufficient_data")

    # The feedback interface for the NEXT run is ready to consume.
    from services.analytics.integration import learning_context_extra

    extra = learning_context_extra()
    assert set(extra) == {"learning_recommendations"}
    assert set(extra["learning_recommendations"]) == set(TARGET_ENGINES)


def test_hooks_close_the_loop_automatically(analytics_dir):
    """With continuous learning enabled, one run_full_pipeline() call
    measures and learns on its own — no manual stage invocation."""
    from services.analytics.integration import (
        disable_continuous_learning,
        enable_continuous_learning,
    )

    enabled = enable_continuous_learning()
    assert enabled["hooks"] == ["agent9-analytics", "agent9-learning"]
    try:
        result = get_orchestrator().run_full_pipeline(
            "Create 2 shorts about desert wildlife",
            count=2, threshold=0, publish_mode="immediate",
        )
        assert result.succeeded
        assert "analytics_summary" in result.context
        assert "learning_report" in result.context
    finally:
        disable_continuous_learning()
