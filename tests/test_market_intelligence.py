"""Tests for the Market Intelligence Department (Agent 11).

Covers: signal providers, learning calibration, competition analysis,
market forecasting (models + validation), the evergreen engine, strategic
recommendations, the opportunity engine, quality validation, roadmap
generation, reporting, configuration, the department query surface, the
pipeline engine, and failure handling.
"""

from __future__ import annotations

import pytest

from providers.trend_sources import get_trend_provider_registry, get_trend_providers
from services.market_intelligence import (
    COMPETITION_PROFILE_FIELDS,
    CONTENT_NATURES,
    MARKET_FORECAST_FIELDS,
    MARKET_OPPORTUNITY_FIELDS,
    MARKET_REPORT_SECTIONS,
    ROADMAP_FIELDS,
    ROADMAP_QUEUES,
    STRATEGIC_ACTION,
    MarketIntelligence,
    MarketIntelligenceConfig,
    analyze_competition,
    build_calibration,
    build_market_forecast,
    build_market_opportunities,
    build_market_opportunity,
    build_market_report,
    build_roadmap,
    competition_level,
    configure,
    content_nature,
    forecast_score,
    get_market_intelligence_config,
    register_forecast_model,
    reset_market_intelligence_config,
    validate_forecast,
    validate_opportunities,
)
from services.market_intelligence.forecasting import FORECAST_MODELS
from services.market_intelligence.models import MarketOpportunity
from services.trends.models import Trend
from services.trends.scorer import score_opportunity

NEW_PROVIDER_KEYS = (
    "academic_publications", "product_launches", "ai_research",
    "github_trending", "developer_communities", "podcast_rankings",
    "search_volume",
)


@pytest.fixture(autouse=True)
def fresh_config():
    reset_market_intelligence_config()
    yield
    reset_market_intelligence_config()


def _trend(**overrides) -> Trend:
    defaults = dict(
        topic="sleep science", keywords=["sleep", "science"],
        growth_pct=80.0, search_volume=250_000, velocity=0.6,
        competition=0.4, freshness=0.7, category="health",
        platform="youtube_shorts", source="google_trends", confidence=0.7,
    )
    defaults.update(overrides)
    return Trend(**defaults)


def _opportunity(**overrides):
    return score_opportunity(_trend(**overrides))


# ------------------------------------------------------------- providers


def test_new_signal_providers_registered():
    keys = {provider.key for provider in get_trend_providers()}
    for key in NEW_PROVIDER_KEYS:
        assert key in keys, f"provider {key} not auto-registered"


def test_new_providers_return_normalized_trends():
    registry = get_trend_provider_registry()
    for key in NEW_PROVIDER_KEYS:
        provider = registry[key]
        trends = provider.discover("quantum computing", category="technology", limit=2)
        assert len(trends) == 2
        for trend in trends:
            assert isinstance(trend, Trend)
            assert trend.source == key
            assert 0 <= trend.confidence <= 1


def test_provider_results_deterministic():
    provider = get_trend_provider_registry()["github_trending"]
    first = provider.discover("rust", limit=3)
    second = provider.discover("rust", limit=3)
    assert [t.topic for t in first] == [t.topic for t in second]
    assert [t.search_volume for t in first] == [t.search_volume for t in second]


# --------------------------------------------------------- learning loop


def test_calibration_neutral_without_history():
    calibration = build_calibration("health")
    assert calibration["roi_calibration"] == 1.0
    assert calibration["confidence_calibration"] == 1.0
    assert calibration["evidence_records"] == 0


def test_calibration_learns_from_analytics_records(tmp_path):
    from services.analytics import AnalyticsStore

    store = AnalyticsStore(directory=str(tmp_path))
    for i in range(12):
        store.add_record({
            "record_id": f"r{i}",
            "niche": "health",
            "platform": "youtube_shorts",
            "topic": f"sleep topic {i}",
            "metrics_status": "collected",
            "metrics": {
                "views": 90_000, "audience_retention": 85, "ctr": 12,
                "likes": 6_000, "comments": 900, "shares": 700, "saves": 400,
            },
        })
    calibration = build_calibration("health", analytics_store=store)
    assert calibration["evidence_records"] == 12
    # Strong outcomes push ROI expectations up.
    assert calibration["roi_calibration"] > 1.0
    assert calibration["winner_profiles"]


def test_calibration_never_raises_on_broken_store():
    class Broken:
        def list_records(self, **_):
            raise RuntimeError("store offline")

    calibration = build_calibration("health", analytics_store=Broken())
    assert calibration["roi_calibration"] == 1.0


# --------------------------------------------------- competition analysis


def test_competition_profile_contract_and_ranges():
    profile = analyze_competition(_trend())
    assert set(profile) == set(COMPETITION_PROFILE_FIELDS)
    assert 0 <= profile["market_difficulty"] <= 100
    assert 0 <= profile["content_gap_score"] <= 100
    assert 0 <= profile["creator_saturation"] <= 1
    assert profile["average_views"] > 0


def test_saturated_markets_are_harder():
    open_market = analyze_competition(_trend(competition=0.1))
    crowded = analyze_competition(_trend(competition=0.9))
    assert crowded["market_difficulty"] > open_market["market_difficulty"]
    assert crowded["content_gap_score"] < open_market["content_gap_score"]
    assert competition_level(crowded) in ("medium", "high")
    assert competition_level(open_market) == "low"


def test_competition_is_deterministic():
    assert analyze_competition(_trend()) == analyze_competition(_trend())


# --------------------------------------------------------- forecasting


def test_market_forecast_contract():
    opportunity = _opportunity()
    profile = analyze_competition(opportunity.trend)
    forecast = build_market_forecast(opportunity, profile)
    for field in MARKET_FORECAST_FIELDS:
        assert field in forecast, f"forecast missing {field}"
    assert forecast["peak_date"] <= forecast["decline_date"]
    assert 0 <= forecast["forecast_confidence"] <= 1
    assert forecast["expected_longevity"] in ("short", "medium", "long", "evergreen")
    assert validate_forecast(forecast) == []


def test_invalid_forecast_detected():
    problems = validate_forecast({
        "peak_date": "2026-09-01", "decline_date": "2026-08-01",
        "forecast_confidence": 1.4, "market_saturation": 0.5,
        "lifespan_days": 0, "expected_longevity": "forever",
    })
    assert len(problems) >= 3


def test_forecast_models_pluggable():
    def custom_model(opportunity, profile, calibration=None):
        forecast = FORECAST_MODELS["momentum"](opportunity, profile, calibration)
        forecast["model"] = "custom"
        return forecast

    register_forecast_model("custom", custom_model)
    try:
        opportunity = _opportunity()
        profile = analyze_competition(opportunity.trend)
        forecast = build_market_forecast(opportunity, profile, model="custom")
        assert forecast["model"] == "custom"
        # Unknown model falls back to the baseline instead of failing.
        fallback = build_market_forecast(opportunity, profile, model="does_not_exist")
        assert fallback["model"] == "momentum"
    finally:
        FORECAST_MODELS.pop("custom", None)


def test_forecast_score_rewards_upside():
    strong = forecast_score({
        "virality_potential": 90, "future_opportunity_score": 85,
        "market_saturation": 0.1, "forecast_confidence": 0.9,
    })
    weak = forecast_score({
        "virality_potential": 15, "future_opportunity_score": 20,
        "market_saturation": 0.9, "forecast_confidence": 0.3,
    })
    assert strong > weak
    assert 0 <= weak <= strong <= 100


# ------------------------------------------------------ evergreen engine


def test_content_nature_classes():
    cases = {
        "news": _opportunity(topic="breaking AI model announced", category="news", freshness=0.95),
        "educational": _opportunity(topic="how to fall asleep fast", category="education"),
        "reference": _opportunity(topic="top 10 sleep facts about the brain"),
        "seasonal": _opportunity(topic="christmas gift ideas", category="entertainment"),
    }
    for expected, opportunity in cases.items():
        assert content_nature(opportunity) == expected


def test_content_nature_always_valid():
    for topic in ("sleep science", "quantum computing", "stock market crash"):
        nature = content_nature(_opportunity(topic=topic))
        assert nature in CONTENT_NATURES


# ------------------------------------------------------ opportunity engine


def test_market_opportunity_contract():
    opportunity = build_market_opportunity(_opportunity())
    data = opportunity.to_dict()
    for field in MARKET_OPPORTUNITY_FIELDS:
        assert field in data, f"MarketOpportunity missing {field}"
    assert data["opportunity_id"].startswith("opp_")
    assert 0 <= data["priority"] <= 100
    assert 0 <= data["roi_estimate"] <= 100
    assert 0 <= data["confidence"] <= 1
    assert data["recommended_content_type"] in ("short_form", "long_form", "series")
    assert data["strategic_actions"]
    assert all(action in STRATEGIC_ACTION.ALL for action in data["strategic_actions"])
    assert data["recommended_content_length"]["min_sec"] > 0


def test_opportunities_ranked_by_priority():
    batch = [
        _opportunity(topic="strong topic", growth_pct=180, velocity=0.8, competition=0.2),
        _opportunity(topic="weak topic", growth_pct=10, velocity=0.1,
                     competition=0.9, confidence=0.4, search_volume=5_000),
    ]
    built = build_market_opportunities(batch)
    priorities = [o.priority for o in built]
    assert priorities == sorted(priorities, reverse=True)


def test_learning_calibration_raises_roi():
    base = build_market_opportunity(_opportunity())
    boosted = build_market_opportunity(
        _opportunity(),
        calibration={"roi_calibration": 1.4, "historical_performance": 0.9,
                     "confidence_calibration": 1.0, "competition_calibration": 1.0},
    )
    assert boosted.roi_estimate > base.roi_estimate


# ------------------------------------------------------------- quality


def _built(**overrides) -> MarketOpportunity:
    return build_market_opportunity(_opportunity(**overrides))


def test_duplicate_opportunities_collapsed():
    first = _built()
    second = _built()
    second.priority = first.priority + 5
    kept, report = validate_opportunities([first, second])
    assert len(kept) == 1
    assert report.dropped["duplicate"] == 1
    assert kept[0].priority == second.priority  # highest priority survives


def test_low_confidence_dropped():
    weak = _built()
    weak.confidence = 0.05
    kept, report = validate_opportunities([weak])
    assert kept == []
    assert report.dropped["low_confidence"] == 1


def test_invalid_forecast_dropped():
    broken = _built()
    broken.forecast["lifespan_days"] = 0
    kept, report = validate_opportunities([broken])
    assert kept == []
    assert report.dropped["invalid_forecast"] == 1


def test_missing_signals_dropped():
    orphan = _built()
    orphan.signals = {}
    kept, report = validate_opportunities([orphan])
    assert kept == []
    assert report.dropped["missing_signals"] == 1


def test_conflicting_recommendations_repaired():
    conflicted = _built()
    conflicted.strategic_actions = [
        STRATEGIC_ACTION.PUBLISH_IMMEDIATELY, STRATEGIC_ACTION.DELAY,
    ]
    kept, report = validate_opportunities([conflicted])
    assert report.repaired_conflicts == 1
    actions = kept[0].strategic_actions
    assert not (
        STRATEGIC_ACTION.PUBLISH_IMMEDIATELY in actions
        and STRATEGIC_ACTION.DELAY in actions
    )


# -------------------------------------------------------------- roadmap


def _opportunity_dicts(n: int = 6) -> list:
    topics = [
        ("sleep science", "health"), ("how to invest explained", "finance"),
        ("quantum computing", "technology"), ("top 10 space facts", "space"),
        ("dopamine detox", "psychology"), ("ai agents", "technology"),
    ]
    built = build_market_opportunities(
        [_opportunity(topic=t, category=c) for t, c in topics[:n]]
    )
    return [o.to_dict() for o in built]


def test_roadmap_contract_and_queues():
    roadmap = build_roadmap(_opportunity_dicts(), topic="sleep science")
    for field in ROADMAP_FIELDS:
        assert field in roadmap, f"roadmap missing {field}"
    for queue in ROADMAP_QUEUES:
        assert queue in roadmap["queues"]
    config = get_market_intelligence_config()
    assert 1 <= len(roadmap["daily"]) <= config.daily_slots
    assert roadmap["daily"][0]["priority"] >= roadmap["daily"][-1]["priority"]


def test_roadmap_calendar_is_dated_and_ordered():
    calendar = build_roadmap(_opportunity_dicts())["calendar"]
    assert calendar
    dates = [entry["date"] for entry in calendar]
    assert dates == sorted(dates)
    for entry in calendar:
        assert entry["opportunity_id"] and entry["topic"]


def test_quarterly_strategy_focuses_categories():
    strategy = build_roadmap(_opportunity_dicts())["quarterly_strategy"]
    assert strategy["focus_categories"]
    assert "localization_targets" in strategy


# ------------------------------------------------------------- reports


def test_market_report_sections():
    opportunities = _opportunity_dicts()
    report = build_market_report(opportunities, {"dropped_total": 2}, topic="sleep")
    for section in MARKET_REPORT_SECTIONS:
        assert section in report, f"report missing {section}"
    summary = report["executive_summary"]
    assert summary["opportunities_identified"] == len(opportunities)
    assert "Top opportunity" in summary["headline"]
    assert report["quality"]["dropped_total"] == 2


def test_market_report_survives_empty_and_malformed_input():
    empty = build_market_report([])
    assert empty["executive_summary"]["opportunities_identified"] == 0
    broken = build_market_report([{"forecast": None, "competition": None}])
    assert broken["report_version"]


# --------------------------------------------------------- configuration


def test_configure_and_reset():
    configure(min_confidence=0.9, daily_slots=1)
    config = get_market_intelligence_config()
    assert config.min_confidence == 0.9
    assert config.daily_slots == 1
    reset_market_intelligence_config()
    assert get_market_intelligence_config().min_confidence != 0.9


def test_unknown_config_key_rejected():
    with pytest.raises(ValueError):
        configure(not_a_real_knob=1)


def test_config_weight_helpers():
    config = MarketIntelligenceConfig()
    assert config.market_weight("finance") > config.market_weight("entertainment")
    assert config.platform_weight("tiktok") > config.platform_weight("facebook")
    assert config.provider_priority("internal_analytics") > config.provider_priority("blog_feeds")
    assert config.provider_priority("unknown_future_provider") == 1.0


def test_config_round_trips():
    config = MarketIntelligenceConfig()
    clone = MarketIntelligenceConfig.from_dict(config.to_dict())
    assert clone.ranking_weights == config.ranking_weights


# ------------------------------------------------------ department surface


def _department() -> MarketIntelligence:
    return MarketIntelligence()


def test_department_answers_every_pipeline_question():
    department = _department()
    best = department.highest_priority_opportunity("sleep science", category="health")
    assert best["topic"]
    assert best["priority"] >= 1

    top10 = department.top_opportunities("sleep science", n=10, category="health")
    assert 1 <= len(top10) <= 10
    assert top10[0]["priority"] == best["priority"]

    for opportunity in department.trending_opportunities("sleep science", category="health"):
        assert opportunity["content_nature"] in ("trending", "news")
    for opportunity in department.evergreen_opportunities("sleep science", category="health"):
        assert opportunity["content_nature"] in ("evergreen", "educational", "reference")

    calendar = department.publishing_calendar("sleep science", category="health")
    assert calendar and calendar[0]["date"]

    report = department.market_report("sleep science", category="health")
    assert report["executive_summary"]["opportunities_identified"] >= 1


def test_department_platform_filter():
    department = _department()
    for opportunity in department.platform_opportunities("sleep science", "tiktok"):
        assert opportunity["platform"] == "tiktok"


def test_department_returns_structured_data_only():
    """The department must never emit scripts or creative assets."""
    best = _department().highest_priority_opportunity("sleep science")
    forbidden = {"script", "scenes", "narration", "hook_text", "voiceover", "assets"}
    assert not forbidden & set(best)
    assert set(MARKET_OPPORTUNITY_FIELDS) <= set(best)


def test_department_caches_analysis_per_topic():
    department = _department()
    department.top_opportunities("sleep science")
    cache_size = len(department._cache)
    department.highest_priority_opportunity("sleep science")
    assert len(department._cache) == cache_size  # reused, not re-analyzed


def test_department_survives_provider_failures():
    class FailingProvider:
        key = "broken"
        label = "Broken"
        platform = "broken"

        def is_available(self):
            return True

        def discover(self, *args, **kwargs):
            raise RuntimeError("provider exploded")

    from providers.trend_sources import get_trend_providers as _all
    from services.trends.manager import TrendDiscoveryManager

    manager = TrendDiscoveryManager(providers=[FailingProvider(), *_all()[:3]])
    department = MarketIntelligence(manager=manager)
    assert department.top_opportunities("sleep science")


# ------------------------------------------------------ pipeline engine


def test_engine_registered_and_contracted():
    import engines  # noqa: F401
    from engines import registry

    engine = registry.get_engine("market_intelligence")
    assert engine is not None
    assert engine.is_ready()
    assert "trend_opportunities" in engine.input_contract
    assert set(engine.output_contract) == {
        "market_opportunities", "market_roadmap", "market_intelligence_report",
    }
    assert "trend_forecasting" in engine.dependencies


def test_engine_runs_on_ranked_opportunities():
    import engines  # noqa: F401
    from engines import registry

    ranked = [
        score_opportunity(_trend(topic=f"sleep angle {i}", growth_pct=60 + i * 20)).to_dict()
        for i in range(4)
    ]
    engine = registry.get_engine("market_intelligence")
    updates = engine.run({
        "trend_opportunities": ranked,
        "trend_subject": "sleep science",
        "trend_category": "health",
    })
    assert updates["market_opportunities"]
    assert updates["market_roadmap"]["daily"]
    assert updates["market_intelligence_report"]["executive_summary"]
    top = updates["market_opportunities"][0]
    assert set(MARKET_OPPORTUNITY_FIELDS) <= set(top)


def test_engine_handles_empty_context():
    import engines  # noqa: F401
    from engines import registry

    updates = registry.get_engine("market_intelligence").run({})
    assert updates["market_opportunities"] == []
    assert updates["market_intelligence_report"]["executive_summary"][
        "opportunities_identified"
    ] == 0


def test_intelligence_pipeline_runs_market_intelligence_after_forecasting():
    from core.workflows import WorkflowEngine

    context = {"command": "create a video about sleep science"}
    run = WorkflowEngine().execute("intelligence", context)
    step_keys = [s.engine_key for s in run.steps]
    assert step_keys[:4] == [
        "trend_discovery", "opportunity_ranking",
        "trend_forecasting", "market_intelligence",
    ]
    assert context["market_opportunities"]
    assert context["market_roadmap"]["queues"]
    assert context["market_intelligence_report"]["executive_summary"]
    # Additive only: the upstream keys are untouched.
    assert context["trend_opportunities"]
    assert context["trend_forecasts"]


def test_market_intelligence_in_trend_stage_group():
    from services.orchestrator.stages import STAGE_GROUPS, STAGE_OF_ENGINE

    assert STAGE_OF_ENGINE["market_intelligence"] == "trend"
    assert "market_intelligence" in STAGE_GROUPS["trend"]
