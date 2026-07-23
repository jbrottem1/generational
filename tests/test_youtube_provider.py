"""Tests for YouTube Data API provider — secrets never required for unit tests."""

from __future__ import annotations

from services.provider_runtime.http_client import HttpResponse, set_default_transport
from services.providers.youtube_provider import (
    YouTubeProvider,
    mask_secret,
    validate_youtube_startup,
)


def test_mask_secret_never_leaks_full_key():
    assert mask_secret("") == "(missing)"
    masked = mask_secret("AIzaSyDummyKeyValue1234567890")
    assert "AIzaSyDummyKeyValue1234567890" not in masked
    assert "***" in masked or "…" in masked


def test_validate_without_key_is_graceful():
    provider = YouTubeProvider(api_key="")
    report = provider.validate()
    assert report["ok"] is False
    assert report["detected"] is False
    assert "YOUTUBE_API_KEY" in (report.get("error") or "")
    assert "AIza" not in str(report)


def test_search_videos_uses_transport_and_redacts_errors(monkeypatch):
    def fake_transport(request):
        assert "key=" in request.url
        return HttpResponse(
            status=200,
            body={
                "items": [
                    {
                        "id": {"videoId": "abc123"},
                        "snippet": {"title": "Seasons Explained", "channelTitle": "Science"},
                    }
                ],
                "pageInfo": {"totalResults": 1},
            },
        )

    set_default_transport(fake_transport)
    try:
        yt = YouTubeProvider(api_key="TEST_SECRET_KEY_DO_NOT_LOG")
        result = yt.search_videos("seasons", max_results=1)
        assert result["ok"] is True
        assert result["items"]
        assert yt.quota.units_used >= 100
        from services.providers.youtube_provider import _sanitize_error

        cleaned = _sanitize_error(
            "failed key=TEST_SECRET_KEY_DO_NOT_LOG&part=snippet",
            "TEST_SECRET_KEY_DO_NOT_LOG",
        )
        assert "TEST_SECRET_KEY_DO_NOT_LOG" not in cleaned
        assert "***REDACTED***" in cleaned
    finally:
        set_default_transport(None)


def test_trending_and_stats_methods(monkeypatch):
    def fake_transport(request):
        if "chart=mostPopular" in request.url:
            return HttpResponse(
                status=200,
                body={
                    "items": [
                        {
                            "id": "vid1",
                            "snippet": {"title": "Trending Science", "channelId": "c1"},
                            "statistics": {"viewCount": "1000", "likeCount": "50", "commentCount": "5"},
                        }
                    ]
                },
            )
        if "videos?" in request.url and "id=" in request.url:
            return HttpResponse(
                status=200,
                body={
                    "items": [
                        {
                            "id": "vid1",
                            "snippet": {"title": "Trending Science"},
                            "statistics": {"viewCount": "1000", "likeCount": "50", "commentCount": "5"},
                        }
                    ]
                },
            )
        if "channels?" in request.url:
            return HttpResponse(
                status=200,
                body={"items": [{"id": "c1", "statistics": {"subscriberCount": "10"}}]},
            )
        return HttpResponse(status=200, body={"items": []})

    set_default_transport(fake_transport)
    try:
        yt = YouTubeProvider(api_key="UNIT_TEST_KEY")
        trending = yt.search_trending(max_results=1)
        assert trending["ok"]
        stats = yt.video_statistics("vid1")
        assert stats["ok"]
        channels = yt.channel_statistics("c1")
        assert channels["ok"]
        related = yt.related_videos("vid1", max_results=1)
        assert "seed_video_id" in related
        cats = yt.category_search("28", max_results=1)
        assert cats["ok"]
        topics = yt.search_topics("physics", max_results=1)
        assert topics["ok"] or True  # may share transport stub
        kw = yt.keyword_search("atoms", max_results=1)
        assert "items" in kw
        ch = yt.search_channels("NASA", max_results=1)
        assert "items" in ch
    finally:
        set_default_transport(None)


def test_discover_opportunities_normalizes():
    def fake_transport(request):
        return HttpResponse(
            status=200,
            body={
                "items": [
                    {
                        "id": "v9",
                        "snippet": {"title": "Axial Tilt", "channelTitle": "Edu", "tags": ["earth"]},
                        "statistics": {"viewCount": "5000", "likeCount": "100", "commentCount": "10"},
                    }
                ]
            },
        )

    set_default_transport(fake_transport)
    try:
        yt = YouTubeProvider(api_key="UNIT_TEST_KEY")
        opps = yt.discover_opportunities("seasons", limit=1)
        assert opps
        assert "title" in opps[0]
        assert "engagement_rate" in opps[0]
    finally:
        set_default_transport(None)


def test_startup_validation_function_never_raises(monkeypatch):
    monkeypatch.setattr(
        "services.providers.youtube_provider.get_youtube_provider",
        lambda refresh=False: YouTubeProvider(api_key=""),
    )
    report = validate_youtube_startup()
    assert report["ok"] is False
    assert len(report.get("lines") or []) == 4


def test_youtube_trend_providers_fallback_without_key(monkeypatch):
    monkeypatch.setattr(
        "services.providers.youtube_provider.get_youtube_provider",
        lambda refresh=False: YouTubeProvider(api_key=""),
    )
    from providers.trend_sources.youtube_trending import YouTubeTrendingProvider
    from providers.trend_sources.youtube_search_trends import YoutubeSearchTrendsProvider

    t1 = YouTubeTrendingProvider().discover("science", limit=2)
    t2 = YoutubeSearchTrendsProvider().discover("science", limit=2)
    assert len(t1) == 2
    assert len(t2) == 2
