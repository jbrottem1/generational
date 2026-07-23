"""Tests for Google News RSS provider — parsing, filters, scoring, cache, failures."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

import pytest

from providers.news.google_news_provider import (
    ArticleScores,
    DiscoveryItem,
    FeedCache,
    GoogleNewsProvider,
    GoogleNewsProviderError,
    dedupe_items,
    discovery_items_to_trends,
    estimate_language,
    is_low_authority,
    is_spam_headline,
    normalize_headline,
    parse_rss_items,
    score_article,
)
from services.discovery.cross_reference import boost_multi_source_confidence
from services.trends.models import Trend

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Google News</title>
    <item>
      <title>How Scientists Study Black Holes - NASA</title>
      <link>https://news.google.com/articles/abc123</link>
      <pubDate>{pub}</pubDate>
      <description>&lt;a href="https://example.com"&gt;Researchers explain&lt;/a&gt; new imaging methods.</description>
      <source url="https://www.nasa.gov">NASA</source>
    </item>
    <item>
      <title>How Scientists Study Black Holes - Reuters</title>
      <link>https://news.google.com/articles/dup</link>
      <pubDate>{pub}</pubDate>
      <description>Duplicate headline should collapse.</description>
      <source url="https://www.reuters.com">Reuters</source>
    </item>
    <item>
      <title>YOU WON'T BELIEVE THIS CRYPTO GIVEAWAY!!!</title>
      <link>https://beforeitsnews.com/spam</link>
      <pubDate>{pub}</pubDate>
      <description>click here for free iPhone</description>
      <source url="https://beforeitsnews.com">Before It's News</source>
    </item>
    <item>
      <title>Ancient Pottery Discovery Explained - Smithsonian</title>
      <link>https://news.google.com/articles/old</link>
      <pubDate>{old}</pubDate>
      <description>Archaeology guide for beginners.</description>
      <source url="https://www.si.edu">Smithsonian</source>
    </item>
  </channel>
</rss>
"""

EMPTY_CHANNEL = """<?xml version="1.0"?><rss version="2.0"><channel><title>x</title></channel></rss>"""


def _fresh_rss() -> bytes:
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=10)
    return SAMPLE_RSS.format(
        pub=format_datetime(now),
        old=format_datetime(old),
    ).encode("utf-8")


# ---------------------------------------------------------------- parsing


def test_parse_rss_items_extracts_fields():
    items = parse_rss_items(_fresh_rss(), feed_key="science", region="US")
    assert len(items) == 4
    first = items[0]
    assert first["title"] == "How Scientists Study Black Holes"
    assert first["publisher"] == "NASA"
    assert "news.google.com" in first["url"]
    assert "Researchers explain" in first["summary"]
    assert "<" not in first["summary"]


def test_malformed_xml_raises_safe_error():
    with pytest.raises(GoogleNewsProviderError, match="malformed"):
        parse_rss_items(b"<rss><item><title>broken")


def test_empty_feed_body_raises():
    with pytest.raises(GoogleNewsProviderError, match="empty"):
        parse_rss_items(b"   ")


def test_empty_channel_returns_no_items():
    assert parse_rss_items(EMPTY_CHANNEL.encode("utf-8")) == []


# ---------------------------------------------------------------- filters


def test_normalize_and_dedupe():
    a = DiscoveryItem(title="Climate Change Explained - CNN", scores=ArticleScores(confidence=70))
    b = DiscoveryItem(title="Climate Change Explained - BBC", scores=ArticleScores(confidence=90))
    assert normalize_headline(a.title) == normalize_headline(b.title)
    out = dedupe_items([a, b])
    assert len(out) == 1
    assert out[0].scores.confidence == 90


def test_spam_and_low_authority():
    assert is_spam_headline("YOU WON'T BELIEVE THIS!!!", "click here")
    assert is_low_authority("Before It's News", "https://beforeitsnews.com/x")
    assert not is_low_authority("Reuters", "https://www.reuters.com/world")


def test_language_estimate():
    assert estimate_language("The scientists are studying the climate crisis today") == "en"
    assert estimate_language("東京で大きな地震が発生しました 緊急速報") == "other"


# ---------------------------------------------------------------- scoring


def test_scoring_ranges():
    scores = score_article(
        title="Breaking: Scientists discover how black holes form",
        summary="New research explains the physics behind event horizons.",
        publisher="Nature",
        publish_time=datetime.now(timezone.utc),
        category="science",
        language="en",
    )
    for value in scores.to_dict().values():
        assert 0 <= value <= 100
    assert scores.educational_potential >= 60
    assert scores.freshness >= 70
    assert scores.breaking_news >= 50


# ---------------------------------------------------------------- cache + network


def test_cache_hit_avoids_second_fetch(tmp_path: Path):
    calls = {"n": 0}
    body = _fresh_rss()

    def fetch(_url: str) -> bytes:
        calls["n"] += 1
        return body

    provider = GoogleNewsProvider(
        refresh_sec=3600,
        max_age_hours=72,
        english_only=True,
        cache_dir=tmp_path,
        fetch_fn=fetch,
    )
    first = provider.pull_feed("science", use_cache=True)
    second = provider.pull_feed("science", use_cache=True)
    assert calls["n"] == 1
    assert provider.cache.stats()["hits"] >= 1
    assert len(first) >= 1
    assert len(second) == len(first)
    # spam + old filtered
    titles = " ".join(i.title.lower() for i in first)
    assert "crypto giveaway" not in titles
    assert "pottery" not in titles


def test_network_failure_raises(tmp_path: Path):
    def boom(_url: str) -> bytes:
        raise ConnectionError("offline")

    provider = GoogleNewsProvider(
        fetch_fn=boom,
        cache=FeedCache(cache_dir=tmp_path / "net_fail", ttl_sec=1),
    )
    with pytest.raises(GoogleNewsProviderError, match="network"):
        provider.pull_feed("world", use_cache=False)


def test_invalid_feed_key():
    provider = GoogleNewsProvider(fetch_fn=lambda u: b"")
    with pytest.raises(GoogleNewsProviderError, match="unknown feed"):
        provider.feed_url("not_a_real_feed")


def test_discovery_item_to_trend_contract():
    item = DiscoveryItem(
        title="How cameras are made",
        summary="Factory process explained",
        url="https://example.com/a",
        publisher="How It's Made",
        publish_time=datetime.now(timezone.utc).isoformat(),
        category="technology",
        region="US",
        language="en",
    )
    item.scores = score_article(
        title=item.title,
        summary=item.summary,
        publisher=item.publisher,
        publish_time=datetime.now(timezone.utc),
        category=item.category,
        language="en",
    )
    trends = discovery_items_to_trends([item])
    assert len(trends) == 1
    t = trends[0]
    assert isinstance(t, Trend)
    assert t.source == "google_news"
    assert t.platform == "news"
    assert t.topic.startswith("How cameras")
    d = item.to_dict()
    assert d["provider"] == "Google News"
    assert "scores" in d
    # Never leak XML
    assert "<rss" not in str(d)


def test_cross_provider_confidence_boost():
    a = Trend(topic="axial tilt seasons", keywords=["axial", "tilt"], source="google_news", confidence=0.6)
    b = Trend(topic="axial tilt seasons explained", keywords=["axial", "tilt"], source="youtube_trending", confidence=0.6)
    c = Trend(topic="unrelated volcano lava", keywords=["volcano"], source="reddit_trends", confidence=0.5)
    boost_multi_source_confidence([a, b, c])
    assert a.confidence > 0.6
    assert b.confidence > 0.6
    assert c.confidence == 0.5


def test_trend_source_adapter_uses_live_items(tmp_path: Path, monkeypatch):
    from providers.trend_sources.google_news import GoogleNewsProvider as TrendAdapter

    body = _fresh_rss()
    gn = GoogleNewsProvider(
        refresh_sec=3600,
        max_age_hours=72,
        cache_dir=tmp_path / "c",
        fetch_fn=lambda _u: body,
    )
    monkeypatch.setattr(
        "providers.news.google_news_provider.get_google_news_provider",
        lambda refresh=False: gn,
    )
    adapter = TrendAdapter()
    trends = adapter.discover("black holes", category="science", limit=2)
    assert trends
    assert all(isinstance(t, Trend) for t in trends)
    assert all(t.source == "google_news" for t in trends)
