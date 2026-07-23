"""Tests for Trend Intelligence & Discovery Engine."""

from __future__ import annotations

from services.discovery.breaking_news import gate_for_production, is_breaking_candidate, verify_topic
from services.discovery.engine import run_discovery
from services.discovery.platform_meta import PLATFORMS, build_platform_packages
from services.discovery.scoring import DISCOVERY_WEIGHTS, score_discovery_opportunity
from services.discovery.series import detect_series
from services.trends.models import Opportunity, Trend
from providers.trend_sources import get_trend_provider_registry


def test_discovery_providers_registered():
    registry = get_trend_provider_registry()
    assert "wikipedia_trending" in registry
    assert "youtube_search_trends" in registry
    assert "google_news" in registry


def test_discovery_weights_sum_to_one():
    assert abs(sum(DISCOVERY_WEIGHTS.values()) - 1.0) < 1e-6


def test_educational_topics_outrank_pure_entertainment_bias():
    science = Trend(
        topic="Origin of turtles explained",
        keywords=["turtles", "evolution", "science"],
        search_volume=50_000,
        growth_pct=40,
        velocity=0.5,
        competition=0.4,
        freshness=0.6,
        category="science",
        confidence=0.85,
        source="wikipedia_trending",
        platform="wikipedia",
    )
    entertainment = Trend(
        topic="celebrity drama rumor",
        keywords=["celebrity", "drama"],
        search_volume=500_000,
        growth_pct=180,
        velocity=0.9,
        competition=0.8,
        freshness=0.95,
        category="entertainment",
        confidence=0.4,
        source="x_trends",
        platform="x",
    )
    _, sci = score_discovery_opportunity(science)
    _, ent = score_discovery_opportunity(entertainment)
    assert sci.educational_value > ent.educational_value
    assert sci.brand_alignment > ent.brand_alignment
    # Mission score should not crown pure rumor virality
    assert sci.total >= ent.total - 5


def test_breaking_news_defers_unverified_rumors():
    report = verify_topic(
        "allegedly leaked conspiracy about turtles",
        related_trends=[
            Trend(topic="allegedly leaked conspiracy", keywords=["rumor"], category="news", confidence=0.4, source="x_trends"),
        ],
    )
    assert report.status in ("rejected", "deferred")
    assert not report.production_allowed


def test_breaking_news_verifies_multi_source():
    peers = [
        Trend(topic="New fossil find", keywords=["fossil"], category="science", confidence=0.8, source="news_api", freshness=0.9),
        Trend(topic="New fossil find", keywords=["fossil"], category="science", confidence=0.75, source="wikipedia_trending", freshness=0.85),
        Trend(topic="New fossil find", keywords=["fossil"], category="science", confidence=0.7, source="google_trends", freshness=0.8),
    ]
    report = verify_topic("New fossil find", related_trends=peers)
    assert report.status in ("verified", "developing")
    assert report.confidence > 0.5


def test_series_detection_clusters_related_topics():
    opps = [
        Opportunity(
            trend=Trend(topic="Turtle shell evolution", keywords=["turtles"], category="science", confidence=0.8),
            opportunity_score=80,
            factors={"evergreen_potential": 85},
        ),
        Opportunity(
            trend=Trend(topic="Turtle fossil intermediates", keywords=["turtles"], category="science", confidence=0.8),
            opportunity_score=78,
            factors={"evergreen_potential": 80},
        ),
        Opportunity(
            trend=Trend(topic="Sea turtle migration", keywords=["turtles"], category="science", confidence=0.7),
            opportunity_score=75,
            factors={"evergreen_potential": 78},
        ),
    ]
    series = detect_series(opps, min_episodes=3)
    assert series
    assert len(series[0].episode_topics) >= 3
    assert "multi_part_series" in series[0].formats


def test_platform_packages_are_not_identical():
    trend = Trend(
        topic="Confirmation bias",
        keywords=["bias", "psychology"],
        category="psychology",
        confidence=0.8,
    )
    packages = build_platform_packages(trend)
    assert set(PLATFORMS).issubset(set(packages.keys()))
    titles = {p: packages[p]["title"] for p in PLATFORMS}
    # At least several platforms must differ
    assert len(set(titles.values())) >= 4
    ctas = {packages[p]["call_to_action"] for p in PLATFORMS}
    assert len(ctas) >= 4


def test_run_discovery_persists_queue(tmp_path, monkeypatch):
    import services.discovery.queue as queue_mod

    monkeypatch.setattr(queue_mod, "QUEUE_PATH", tmp_path / "PRODUCTION_QUEUE.json")
    monkeypatch.setattr(queue_mod, "QUEUE_DIR", tmp_path)

    result = run_discovery(
        subject="turtle evolution",
        category="science",
        limit_per_provider=1,
        top_n=12,
        persist=True,
    )
    assert result["ok"] is True
    assert result["discovered"] > 0
    assert result["ready"] >= 1
    assert (tmp_path / "PRODUCTION_QUEUE.json").is_file()
    top = result["top"]
    assert top is not None
    assert "platform_packages" in top
    assert "youtube_shorts" in top["platform_packages"]
    assert "discovery_score" in top


def test_discovery_engine_registered():
    import engines  # noqa: F401
    from engines.registry import get_engine

    engine = get_engine("discovery")
    assert engine is not None
    assert engine.is_ready()
    out = engine.run({"command": "science education about cells", "persist_discovery_queue": False})
    assert "discovery" in out
    assert out["discovery"]["ok"] is True
