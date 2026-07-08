"""Tests for the v7.0 Trend Discovery Engine — providers, model, scoring, pipeline."""

from core.workflows import WorkflowEngine
from providers.trend_sources import get_trend_provider_registry, get_trend_providers
from providers.trend_sources.base import TrendSourceProvider
from services.trends.manager import TrendDiscoveryManager
from services.trends.models import Opportunity, Trend
from services.trends.scorer import FACTOR_WEIGHTS, rank_opportunities, score_opportunity

EXPECTED_PROVIDERS = {
    "google_trends", "youtube_trending", "tiktok_trends",
    "reddit_trends", "rss_feeds", "news_api", "keyword_api",
}


# ---------------------------------------------------------------- registry

def test_registry_auto_discovers_all_providers():
    registry = get_trend_provider_registry()
    assert EXPECTED_PROVIDERS.issubset(set(registry.keys()))


def test_providers_implement_interface():
    for provider in get_trend_providers():
        assert isinstance(provider, TrendSourceProvider)
        assert provider.key
        assert provider.label
        assert provider.is_available() in (True, False)


# ---------------------------------------------------------------- universal model

def test_all_providers_return_normalized_trends():
    for provider in get_trend_providers():
        trends = provider.discover("sleep science", category="science")
        assert trends, provider.key
        for trend in trends:
            assert isinstance(trend, Trend)
            assert trend.topic
            assert trend.keywords
            assert trend.source == provider.key
            assert 0 <= trend.confidence <= 1
            assert 0 <= trend.competition <= 1
            assert trend.timestamp


def test_trend_dict_round_trip():
    trend = get_trend_providers()[0].discover("black holes", category="space")[0]
    restored = Trend.from_dict(trend.to_dict())
    assert restored.to_dict() == trend.to_dict()


# ---------------------------------------------------------------- scoring

def test_opportunity_score_range_and_factors():
    trend = Trend(topic="dopamine detox", search_volume=250_000, growth_pct=120,
                  velocity=0.8, competition=0.3, freshness=0.9,
                  category="psychology", platform="tiktok", confidence=0.8)
    opp = score_opportunity(trend)
    assert 0 <= opp.opportunity_score <= 100
    assert set(opp.factors.keys()) == set(FACTOR_WEIGHTS.keys())
    assert all(0 <= v <= 100 for v in opp.factors.values())


def test_scoring_is_deterministic():
    trend = Trend(topic="ai agents", search_volume=90_000, category="technology")
    assert score_opportunity(trend).opportunity_score == score_opportunity(trend).opportunity_score


def test_strong_trend_outscores_weak_trend():
    strong = Trend(topic="a", search_volume=1_000_000, growth_pct=150, velocity=0.9,
                   competition=0.2, freshness=0.9, category="finance",
                   platform="tiktok", confidence=0.9)
    weak = Trend(topic="b", search_volume=100, growth_pct=2, velocity=0.1,
                 competition=0.95, freshness=0.1, category="news",
                 platform="rss", confidence=0.3)
    assert score_opportunity(strong).opportunity_score > score_opportunity(weak).opportunity_score


def test_rank_opportunities_sorted_and_limited():
    trends = [Trend(topic=f"t{i}", search_volume=1000 * (i + 1)) for i in range(8)]
    ranked = rank_opportunities(trends, top_n=5)
    assert len(ranked) == 5
    scores = [o.opportunity_score for o in ranked]
    assert scores == sorted(scores, reverse=True)


def test_opportunity_dict_round_trip():
    opp = score_opportunity(Trend(topic="ocean mysteries", search_volume=40_000))
    restored = Opportunity.from_dict(opp.to_dict())
    assert restored.opportunity_score == opp.opportunity_score
    assert restored.trend.topic == "ocean mysteries"


# ---------------------------------------------------------------- manager

def test_manager_collects_from_all_providers():
    manager = TrendDiscoveryManager()
    trends = manager.discover("sleep", category="health")
    sources = {t.source for t in trends}
    assert EXPECTED_PROVIDERS.issubset(sources)


class _BrokenProvider(TrendSourceProvider):
    key = "broken"
    label = "Broken"

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        raise RuntimeError("provider exploded")


class _OkProvider(TrendSourceProvider):
    key = "ok"
    label = "OK"

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        return [Trend(topic=topic, source=self.key)]


def test_manager_survives_provider_failure():
    manager = TrendDiscoveryManager(providers=[_BrokenProvider(), _OkProvider()])
    trends = manager.discover("resilience")
    assert len(trends) == 1
    assert trends[0].source == "ok"


def test_manager_full_opportunity_flow():
    manager = TrendDiscoveryManager()
    opportunities = manager.discover_opportunities("black holes", category="space", top_n=3)
    assert len(opportunities) == 3
    assert all(isinstance(o, Opportunity) for o in opportunities)


# ---------------------------------------------------------------- pipeline integration

def test_intelligence_pipeline_includes_trend_stages():
    context = {"command": "Create 3 science shorts about black holes",
               "count": 5, "model": "gpt-4o-mini", "threshold": 0}
    run = WorkflowEngine().execute("intelligence", context)
    assert run.succeeded, run.summary()

    step_keys = [s.engine_key for s in run.steps]
    assert step_keys[0] == "trend_discovery"
    assert step_keys[1] == "opportunity_ranking"

    assert context["trends"]
    assert context["trend_opportunities"]
    assert len(context["trend_opportunities"]) <= 5
    assert context["top_opportunity"]["opportunity_score"] >= 0
    dashboard = context["trend_dashboard"]
    assert dashboard["top_score"] == context["trend_opportunities"][0]["opportunity_score"]
    assert dashboard["platforms"]
    assert dashboard["countries"]
