"""Tests for the Trend Discovery & Forecasting Engine (Agent 11).

Covers: new provider adapters, forecasting, classification,
recommendations, quality control (duplicates / spam / expiry / conflicts),
configuration, learning integration, the opportunity feed query surface,
failure recovery, contract validation, and pipeline integration.

All tests run in Demo Mode (deterministic heuristics, no API key needed).
"""

from datetime import datetime, timedelta, timezone

import pytest

import engines  # noqa: F401 - importing registers all engines
from core.workflows import WorkflowEngine
from engines import registry
from providers.trend_sources import get_trend_provider_registry
from services.knowledge import CATEGORY, KnowledgeBase
from services.trend_intelligence import (
    CLASSIFICATION_FIELDS,
    FORECAST_FIELDS,
    RECOMMENDATION_FIELDS,
    OpportunityFeed,
    TrendIntelligenceConfig,
    classify_opportunity,
    enrich_opportunity,
    forecast_opportunity,
    historical_performance_for,
    recommend_opportunity,
    review_trends,
)
from services.trend_intelligence.models import (
    CONTENT_TYPES,
    LIFECYCLES,
    MARKET_REACH,
    TRAJECTORIES,
)
from services.trends.manager import TrendDiscoveryManager
from services.trends.models import Trend
from services.trends.scorer import score_opportunity

NEW_PROVIDERS = {
    "instagram_trends", "facebook_trends", "x_trends",
    "blog_feeds", "industry_publications", "internal_analytics",
}


def _trend(**overrides) -> Trend:
    base = dict(
        topic="dopamine detox", keywords=["dopamine", "focus"],
        growth_pct=100.0, search_volume=250_000, velocity=0.7,
        competition=0.3, freshness=0.8, category="psychology",
        platform="tiktok", source="test", confidence=0.8,
    )
    base.update(overrides)
    return Trend(**base)


def _opportunity(**overrides):
    return score_opportunity(_trend(**overrides))


# ---------------------------------------------------------------- providers

def test_new_providers_auto_discovered():
    registry_keys = set(get_trend_provider_registry().keys())
    assert NEW_PROVIDERS.issubset(registry_keys)


def test_new_providers_return_normalized_trends():
    provider_registry = get_trend_provider_registry()
    for key in NEW_PROVIDERS:
        trends = provider_registry[key].discover("sleep science", category="science")
        assert trends, key
        for trend in trends:
            assert isinstance(trend, Trend)
            assert trend.source == key
            assert trend.topic
            assert 0 <= trend.confidence <= 1


def test_internal_analytics_promotes_proven_performers(tmp_path, monkeypatch):
    from providers.trend_sources.internal_analytics import InternalAnalyticsProvider
    from services import knowledge

    kb = KnowledgeBase(directory=str(tmp_path / "kb"))
    kb.add_entry(
        CATEGORY.PERFORMANCE,
        {"topic": "sleep science explained", "performance": 0.9, "views": 500_000},
        metadata={"category": "science"},
    )
    monkeypatch.setattr(knowledge, "get_knowledge_base", lambda: kb)

    trends = InternalAnalyticsProvider().discover("sleep science", category="science", limit=3)
    assert len(trends) == 3
    assert trends[0].topic == "sleep science explained"
    assert trends[0].confidence == 0.85     # our own data is highest-trust
    assert trends[0].search_volume == 500_000


# --------------------------------------------------------------- forecasting

def test_forecast_has_full_contract_and_valid_ranges():
    forecast = forecast_opportunity(_opportunity())
    data = forecast.to_dict()
    for field in FORECAST_FIELDS:
        assert field in data, field
    assert 1 <= forecast.days_to_peak <= 14
    assert forecast.expected_lifespan_days >= 3
    assert forecast.trajectory in TRAJECTORIES
    assert 0 <= forecast.saturation_risk <= 1
    assert 0 <= forecast.future_opportunity_score <= 100
    assert 0 <= forecast.forecast_confidence <= 1
    assert 1 <= forecast.recommended_posts_per_week <= 7
    window = forecast.publishing_window
    assert window["start_in_days"] < window["end_in_days"]
    assert window["start"] <= window["end"]


def test_forecast_is_deterministic():
    opp = _opportunity()
    assert forecast_opportunity(opp).to_dict() == forecast_opportunity(opp).to_dict()


def test_fast_movers_peak_sooner_than_slow_movers():
    fast = forecast_opportunity(_opportunity(growth_pct=180, velocity=0.9, freshness=0.95))
    slow = forecast_opportunity(_opportunity(growth_pct=10, velocity=0.1, freshness=0.3))
    assert fast.days_to_peak < slow.days_to_peak


def test_evergreen_outlives_news():
    science = forecast_opportunity(_opportunity(category="science"))
    news = forecast_opportunity(_opportunity(category="news"))
    assert science.expected_lifespan_days > news.expected_lifespan_days


def test_crowded_stale_topics_carry_higher_saturation_risk():
    crowded = forecast_opportunity(_opportunity(competition=0.9, freshness=0.2, growth_pct=5))
    open_field = forecast_opportunity(_opportunity(competition=0.1, freshness=0.9, growth_pct=150))
    assert crowded.saturation_risk > open_field.saturation_risk
    assert crowded.trajectory == "declining"
    assert open_field.trajectory in ("explosive", "rising")


# ------------------------------------------------------------ classification

def test_classification_has_full_contract_and_known_labels():
    classification = classify_opportunity(_opportunity())
    for field in CLASSIFICATION_FIELDS:
        assert field in classification, field
    assert classification["lifecycle"] in LIFECYCLES
    assert classification["content_type"] in CONTENT_TYPES
    assert classification["market_reach"] in MARKET_REACH
    assert len(classification["labels"]) == 3


@pytest.mark.parametrize("overrides,expected", [
    (dict(growth_pct=200, velocity=0.9), "exploding"),
    (dict(growth_pct=100, velocity=0.5, freshness=0.95), "breaking"),
    (dict(growth_pct=80, velocity=0.5, freshness=0.7), "emerging"),
    (dict(growth_pct=5, freshness=0.2), "declining"),
    (dict(growth_pct=30, velocity=0.2, competition=0.85, freshness=0.5), "peak"),
])
def test_lifecycle_rules(overrides, expected):
    assert classify_opportunity(_opportunity(**overrides))["lifecycle"] == expected


def test_content_type_rules():
    assert classify_opportunity(_opportunity(category="psychology"))["content_type"] == "evergreen"
    assert classify_opportunity(
        _opportunity(topic="christmas gift ideas", category="entertainment")
    )["content_type"] == "seasonal"
    assert classify_opportunity(
        _opportunity(topic="morning routine science", category="entertainment", keywords=["routine"])
    )["content_type"] == "recurring"
    assert classify_opportunity(
        _opportunity(category="entertainment", keywords=["fun"])
    )["content_type"] == "topical"


def test_market_reach_rules():
    assert classify_opportunity(_opportunity(search_volume=5_000))["market_reach"] == "niche"
    assert classify_opportunity(_opportunity(search_volume=200_000))["market_reach"] == "mid_market"
    assert classify_opportunity(_opportunity(search_volume=5_000_000))["market_reach"] == "mass_market"


# ------------------------------------------------------------ recommendations

def test_recommendation_has_full_contract_and_valid_ranges():
    opp = _opportunity()
    forecast = forecast_opportunity(opp)
    rec = recommend_opportunity(opp, forecast, classify_opportunity(opp))
    data = rec.to_dict()
    for field in RECOMMENDATION_FIELDS:
        assert field in data, field
    assert rec.recommended_platform
    assert rec.hook_direction and rec.psychology_strategy
    assert rec.recommended_duration_sec["min"] < rec.recommended_duration_sec["max"]
    assert rec.recommended_format and rec.thumbnail_direction and rec.title_direction
    assert rec.seo_recommendations["primary_keyword"]
    assert 0 <= rec.estimated_roi <= 100
    assert 0 <= rec.confidence_score <= 1
    assert 0 <= rec.risk_score <= 100
    assert 0 <= rec.priority_score <= 100
    assert rec.publishing_window == forecast.publishing_window


def test_recommendations_never_contain_scripts():
    enriched = enrich_opportunity(_opportunity())
    assert "script" not in enriched
    assert "script" not in enriched["recommendation"]


def test_strong_opportunity_gets_higher_priority_and_roi():
    strong = _opportunity(growth_pct=180, velocity=0.9, competition=0.1,
                          freshness=0.95, category="finance", confidence=0.9)
    weak = _opportunity(growth_pct=5, velocity=0.1, competition=0.95,
                        freshness=0.2, category="news", confidence=0.3,
                        search_volume=500)
    strong_rec = enrich_opportunity(strong)["recommendation"]
    weak_rec = enrich_opportunity(weak)["recommendation"]
    assert strong_rec["priority_score"] > weak_rec["priority_score"]
    assert strong_rec["estimated_roi"] > weak_rec["estimated_roi"]
    assert strong_rec["risk_score"] < weak_rec["risk_score"]


def test_out_of_scope_platform_falls_back_to_configured_best():
    rec = enrich_opportunity(_opportunity(platform="rss"))["recommendation"]
    assert rec["recommended_platform"] in ("youtube_shorts", "tiktok", "instagram", "youtube")


# ------------------------------------------------------------ quality control

def test_exact_duplicates_collapse_to_strongest():
    trends = [_trend(confidence=0.5), _trend(confidence=0.9), _trend(confidence=0.7)]
    kept, report = review_trends(trends)
    assert len(kept) == 1
    assert kept[0].confidence == 0.9
    assert report.dropped["duplicate"] == 2


def test_near_duplicates_dropped():
    trends = [
        _trend(topic="dopamine detox explained"),
        _trend(topic="dopamine detox fully explained"),   # near-identical token set
        _trend(topic="the history of rome", keywords=["rome", "history"]),
    ]
    kept, report = review_trends(trends)
    assert len(kept) == 2
    assert report.dropped["near_duplicate"] == 1


def test_expired_stale_spam_and_low_confidence_dropped():
    old = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    trends = [
        _trend(topic="valid signal one"),
        _trend(topic="expired signal", timestamp=old),
        _trend(topic="stale signal here", freshness=0.05),
        _trend(topic="FREE MONEY click here now!!!"),
        _trend(topic="whisper signal", confidence=0.05),
    ]
    kept, report = review_trends(trends)
    assert [t.topic for t in kept] == ["valid signal one"]
    assert report.dropped["expired"] == 1
    assert report.dropped["stale"] == 1
    assert report.dropped["spam"] == 1
    assert report.dropped["low_confidence"] == 1
    assert report.to_dict()["dropped_total"] == 4


def test_conflicting_signals_flagged_and_confidence_discounted():
    trends = [
        _trend(topic="Quantum Computing", source="source_a", growth_pct=300, confidence=0.8),
        _trend(topic="quantum computing", source="source_b", growth_pct=10, confidence=0.8),
    ]
    kept, report = review_trends(trends)
    # Conflict is detected across the divergent copies BEFORE dedup collapses them.
    assert report.conflicts
    assert report.conflicts[0]["growth_spread_pct"] == 290.0
    assert sorted(report.conflicts[0]["sources"]) == ["source_a", "source_b"]
    assert report.dropped["duplicate"] == 1
    assert len(kept) == 1
    assert kept[0].confidence < 0.8    # conflicting data is weaker data


def test_quality_review_never_raises_on_malformed_timestamp():
    kept, report = review_trends([_trend(timestamp="not-a-date")])
    assert kept == []
    assert report.dropped["expired"] == 1


# -------------------------------------------------------------- configuration

def test_config_overrides_change_behavior():
    config = TrendIntelligenceConfig(min_confidence=0.95)
    kept, report = review_trends([_trend(confidence=0.8)], config)
    assert kept == []
    assert report.dropped["low_confidence"] == 1


def test_config_round_trip_and_unknown_keys_ignored():
    config = TrendIntelligenceConfig(poll_interval_minutes=5)
    restored = TrendIntelligenceConfig.from_dict({**config.to_dict(), "unknown_future_key": 1})
    assert restored.poll_interval_minutes == 5


def test_config_provider_filtering():
    config = TrendIntelligenceConfig(disabled_providers=["x_trends"])
    assert config.provider_allowed("google_trends")
    assert not config.provider_allowed("x_trends")
    allowlist = TrendIntelligenceConfig(enabled_providers=["google_trends"])
    assert allowlist.provider_allowed("google_trends")
    assert not allowlist.provider_allowed("reddit_trends")


def test_configure_rejects_unknown_keys():
    from services.trend_intelligence.config import configure, reset_trend_intelligence_config

    reset_trend_intelligence_config()
    try:
        with pytest.raises(ValueError):
            configure(not_a_real_knob=1)
        assert configure(poll_interval_minutes=15).poll_interval_minutes == 15
    finally:
        reset_trend_intelligence_config()


# ----------------------------------------------------------- learning loop

def test_historical_performance_neutral_without_history(tmp_path):
    kb = KnowledgeBase(directory=str(tmp_path / "kb"))
    assert historical_performance_for("science", kb) == 0.5


def test_historical_performance_reflects_real_outcomes(tmp_path):
    kb = KnowledgeBase(directory=str(tmp_path / "kb"))
    kb.add_entry(CATEGORY.PERFORMANCE, {"category": "science", "performance": 0.9})
    kb.add_entry(CATEGORY.PERFORMANCE, {"category": "science", "score": 70})
    kb.add_entry(CATEGORY.PERFORMANCE, {"category": "news", "performance": 0.1})
    assert historical_performance_for("science", kb) == 0.8
    assert historical_performance_for("news", kb) == 0.1


def test_historical_performance_changes_rankings(tmp_path):
    kb = KnowledgeBase(directory=str(tmp_path / "kb"))
    kb.add_entry(CATEGORY.PERFORMANCE, {"category": "science", "performance": 1.0})
    strong_history = OpportunityFeed(knowledge_base=kb)
    no_history = OpportunityFeed(knowledge_base=KnowledgeBase(directory=str(tmp_path / "kb2")))

    with_history = strong_history.top_opportunity("sleep", category="science")
    without = no_history.top_opportunity("sleep", category="science")
    assert with_history["factors"]["historical_performance"] == 100
    assert without["factors"]["historical_performance"] == 50
    assert with_history["opportunity_score"] >= without["opportunity_score"]


# ----------------------------------------------------------------- the feed

@pytest.fixture
def feed(tmp_path):
    return OpportunityFeed(knowledge_base=KnowledgeBase(directory=str(tmp_path / "kb")))


def test_feed_top_queries(feed):
    top = feed.top_opportunity("black holes", category="space")
    assert top["opportunity_score"] > 0
    assert top["forecast"] and top["classification"] and top["recommendation"]

    top10 = feed.top("black holes", n=10, category="space")
    assert 0 < len(top10) <= 10
    scores = [item["opportunity_score"] for item in top10]
    assert scores == sorted(scores, reverse=True)
    assert top10[0] == top


def test_feed_filtered_queries(feed):
    for item in feed.emerging("ai agents", category="technology"):
        assert item["classification"]["lifecycle"] in ("emerging", "breaking", "exploding")
    for item in feed.evergreen("sleep", category="science"):
        assert item["classification"]["content_type"] == "evergreen"
    for item in feed.for_platform("sleep", "tiktok", category="science"):
        assert "tiktok" in (
            item["trend"]["platform"], item["recommendation"]["recommended_platform"]
        )


def test_feed_roi_and_confidence_orderings(feed):
    rois = [i["recommendation"]["estimated_roi"] for i in feed.highest_roi("sleep")]
    assert rois == sorted(rois, reverse=True)
    confidences = [
        i["recommendation"]["confidence_score"] for i in feed.highest_confidence("sleep")
    ]
    assert confidences == sorted(confidences, reverse=True)


def test_feed_caches_within_polling_window(feed):
    first = feed.discover("caching test")
    assert not feed.needs_refresh("caching test")
    assert feed.discover("caching test") == first
    assert feed.last_quality_report("caching test")["kept"] > 0


def test_feed_survives_provider_failure(tmp_path):
    class _Broken:
        key = "broken"
        label = "Broken"
        platform = ""

        def is_available(self):
            return True

        def discover(self, *args, **kwargs):
            raise RuntimeError("provider exploded")

    class _Ok:
        key = "ok"
        label = "OK"
        platform = "tiktok"

        def is_available(self):
            return True

        def discover(self, topic, category="general", country="US", language="en", limit=3):
            return [_trend(topic=topic, source=self.key)]

    feed = OpportunityFeed(
        manager=TrendDiscoveryManager(providers=[_Broken(), _Ok()]),
        knowledge_base=KnowledgeBase(directory=str(tmp_path / "kb")),
    )
    results = feed.discover("resilience")
    assert len(results) == 1
    assert results[0]["trend"]["source"] == "ok"


# ------------------------------------------------------ pipeline integration

def test_engine_registered_with_contracts():
    engine = registry.get_engine("trend_forecasting")
    assert engine is not None and engine.is_ready()
    diagnostics = engine.diagnostics()
    assert diagnostics["input_contract"] == ["trend_opportunities"]
    assert set(diagnostics["output_contract"]) == {
        "trend_forecasts", "trend_classifications",
        "opportunity_recommendations", "trend_intelligence_report",
    }
    assert diagnostics["dependencies"] == ["trend_discovery", "opportunity_ranking"]


def test_intelligence_pipeline_runs_forecasting_after_ranking():
    context = {"command": "Create 3 science shorts about black holes",
               "count": 5, "model": "gpt-4o-mini", "threshold": 0}
    run = WorkflowEngine().execute("intelligence", context)
    assert run.succeeded, run.summary()

    step_keys = [s.engine_key for s in run.steps]
    assert step_keys[:3] == ["trend_discovery", "opportunity_ranking", "trend_forecasting"]

    # Existing trend keys untouched; new keys are additive.
    assert context["trends"] and context["trend_opportunities"]
    assert len(context["trend_forecasts"]) == len(context["trend_opportunities"])
    assert len(context["opportunity_recommendations"]) == len(context["trend_opportunities"])
    priorities = [r["priority_score"] for r in context["opportunity_recommendations"]]
    assert priorities == sorted(priorities, reverse=True)
    report = context["trend_intelligence_report"]
    assert report["opportunities"] == len(context["trend_opportunities"])
    assert report["quality"]["total"] >= report["quality"]["kept"]
    assert report["top_recommendation"]["priority_score"] == priorities[0]


def test_engine_safe_with_empty_context():
    updates = registry.get_engine("trend_forecasting").run({})
    assert updates["trend_forecasts"] == []
    assert updates["opportunity_recommendations"] == []
    assert updates["trend_intelligence_report"]["opportunities"] == 0


def test_orchestrated_trend_stage_includes_forecasting():
    from services.orchestrator import StageStatus, get_orchestrator

    context = {"command": "Create 3 science shorts about black holes"}
    report = get_orchestrator().run_trend_stage(context)
    assert report.status == StageStatus.SUCCESS
    engines_run = [step["engine"] for step in report.diagnostics["steps"]]
    assert engines_run == ["trend_discovery", "opportunity_ranking", "trend_forecasting"]
    assert context["trend_forecasts"]
    assert context["trend_intelligence_report"]
