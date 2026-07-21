"""Tests for YouTube Search Intelligence — structured only, no live key required."""

from __future__ import annotations

from datetime import datetime, timezone

from services.discovery.cross_reference import agreeing_sources_for_topic
from services.discovery.script_handoff import brief_to_script_context, queue_item_to_script_context
from services.providers.youtube_search_intelligence import (
    TopicMarketStats,
    VideoWatchSignal,
    YouTubeSearchIntelligence,
    build_unified_brief,
    parse_iso8601_duration,
    pick_thumbnail,
    recommend_video_type,
    score_watch_signal,
    signals_to_trends,
)
from services.trends.models import Trend


def test_parse_iso8601_duration():
    assert parse_iso8601_duration("PT45S") == 45
    assert parse_iso8601_duration("PT1M30S") == 90
    assert parse_iso8601_duration("PT1H2M3S") == 3723
    assert parse_iso8601_duration("") == 0
    assert parse_iso8601_duration("bogus") == 0


def test_pick_thumbnail_prefers_maxres():
    url = pick_thumbnail(
        {
            "default": {"url": "http://d.jpg"},
            "high": {"url": "http://h.jpg"},
            "maxres": {"url": "http://m.jpg"},
        }
    )
    assert url == "http://m.jpg"


def test_score_watch_signal_ranges():
    scores = score_watch_signal(
        title="How Black Holes Work Explained",
        description="Educational science documentary guide",
        views=250_000,
        likes=12_000,
        comments=900,
        duration_sec=540,
        publish_date=datetime.now(timezone.utc),
        thumbnail="https://i.ytimg.com/vi/x/hqdefault.jpg",
        tags=["space", "science"],
        category="Science & Technology",
        market_avg_views=80_000,
    )
    for v in scores.to_dict().values():
        assert 0 <= v <= 100
    assert scores.educational >= 65
    assert scores.popularity >= 40


def test_recommend_video_types():
    assert recommend_video_type(duration_sec=42, title="Quick fact", description="", evergreen=40, freshness_hours=10) == "short"
    assert recommend_video_type(duration_sec=600, title="Full documentary", description="", evergreen=40, freshness_hours=10) == "long_form"
    assert recommend_video_type(duration_sec=50, title="Breaking update today", description="", evergreen=20, freshness_hours=5) == "live_update"
    assert recommend_video_type(duration_sec=300, title="Part 1: Gravity", description="", evergreen=80, freshness_hours=100) == "series"


def test_unified_brief_and_json_only():
    videos = [
        VideoWatchSignal(
            title="How Cameras Are Made Explained",
            channel="Factory Science",
            view_count=100_000,
            duration_sec=48,
            thumbnail="https://i.ytimg.com/vi/abc/hqdefault.jpg",
            tags=["camera", "manufacturing"],
            scores=score_watch_signal(
                title="How Cameras Are Made Explained",
                description="factory tour educational",
                views=100_000,
                likes=4000,
                comments=200,
                duration_sec=48,
                publish_date=datetime.now(timezone.utc),
                thumbnail="https://i.ytimg.com/vi/abc/hqdefault.jpg",
                tags=["camera"],
                category="Science & Technology",
                market_avg_views=50_000,
            ),
        )
    ]
    market = TopicMarketStats(average_view_count=50_000, average_upload_frequency_per_week=2.5, average_channel_size=1e6, sample_size=1)
    brief = build_unified_brief(
        "how cameras are made",
        videos,
        market,
        cross_reference={"agreeing_sources": 3, "sources": ["google_news", "reddit_trends", "youtube_search_trends"]},
        discovery_score_hint=70,
    )
    data = brief.to_dict()
    assert "overall_opportunity_score" in data
    assert "reasoning" in data
    assert data["recommended_video_type"] in ("short", "long_form", "series", "live_update")
    assert "items" not in data  # no raw API
    assert "<" not in data["reasoning"] or "etag" not in data["reasoning"].lower()


def test_signals_to_trends_contract():
    v = VideoWatchSignal(title="Seasons Explained", view_count=10_000, tags=["seasons", "earth"])
    v.scores = score_watch_signal(
        title=v.title,
        description="axial tilt",
        views=10_000,
        likes=100,
        comments=10,
        duration_sec=55,
        publish_date=datetime.now(timezone.utc),
        thumbnail="",
        tags=v.tags,
        category="Education",
        market_avg_views=8_000,
    )
    trends = signals_to_trends([v], category="science")
    assert trends[0].source == "youtube_search_trends"
    assert trends[0].search_volume == 10_000


def test_script_handoff_feeds_agent_3_shape():
    brief = {
        "overall_opportunity_score": 77,
        "unified_discovery_score": 74,
        "confidence": 0.82,
        "reasoning": "Strong educational watch demand.",
        "recommended_video_type": "short",
        "estimated_audience": 120000,
        "expected_click_through_potential": 68,
        "expected_watch_time_sec": 45,
        "estimated_competition": 0.48,
        "target_platform": "youtube_shorts",
        "cross_reference": {"agreeing_sources": 2, "sources": ["google_news", "youtube_search_trends"]},
    }
    ctx = brief_to_script_context("How cameras are made", brief)
    assert ctx["target_platform"] == "youtube_shorts"
    assert ctx["candidates"][0]["title"]
    assert ctx["research"]["opportunity_score"] == 77
    assert ctx["discovery_fed"] is True

    queue_ctx = queue_item_to_script_context(
        {
            "topic": "How cameras are made",
            "trend_score": 70,
            "discovery_score": 74,
            "estimated_audience": 120000,
            "competition": 0.48,
            "recommended_length_sec": {"min": 30, "max": 55},
            "confidence_score": 0.8,
            "production_brief": brief,
            "queue_id": "abc123",
        }
    )
    assert queue_ctx["discovery_queue_id"] == "abc123"
    assert queue_ctx["candidates"]


def test_agreeing_sources_detects_news_and_youtube():
    trends = [
        Trend(topic="how cameras are made", keywords=["cameras", "made"], source="google_news"),
        Trend(topic="Camera manufacturing explained", keywords=["camera", "manufacturing"], source="youtube_search_trends"),
        Trend(topic="unrelated volcano", keywords=["volcano"], source="reddit_trends"),
    ]
    xref = agreeing_sources_for_topic("how cameras are made", trends)
    assert xref["has_google_news"]
    assert xref["has_youtube"]
    assert xref["agreeing_sources"] >= 2


def test_intelligence_offline_without_key():
    from services.providers.youtube_provider import YouTubeProvider

    intel = YouTubeSearchIntelligence(yt=YouTubeProvider(api_key=""))
    report = intel.analyze_topic("black holes")
    assert report.live is False
    assert report.to_dict()["brief"]["overall_opportunity_score"] == 0
    # Structured only
    assert "kind" not in report.to_dict()
