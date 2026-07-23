"""Build Audience Intelligence reports from discovery + provider signals."""

from __future__ import annotations

from typing import Any

from core.log import get_logger, log_event
from services.audience_intelligence.models import AudienceIntelligenceReport
from services.audience_intelligence.scoring import (
    build_audience_profile,
    build_creative_directives,
    estimate_engagement,
    human_attention_score,
    score_psychological_drivers,
)

logger = get_logger(__name__)


def _extract_provider_signals(
    *,
    youtube_intelligence: dict[str, Any] | None = None,
    google_news: dict[str, Any] | None = None,
    production_brief: dict[str, Any] | None = None,
    cross_reference: dict[str, Any] | None = None,
    internal_analytics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize multi-provider inputs into compact numeric/text signals (no raw API)."""
    signals: dict[str, Any] = {}
    yt = youtube_intelligence or {}
    brief = production_brief or yt.get("brief") or {}
    market = yt.get("market") or {}
    videos = yt.get("videos") or []

    yt_scores: dict[str, Any] = {}
    if videos and isinstance(videos[0], dict):
        s0 = (videos[0].get("scores") or {}) if isinstance(videos[0], dict) else {}
        yt_scores = {
            "educational": int(s0.get("educational") or 0),
            "clickability": int(s0.get("clickability") or 0),
            "thumbnail_quality": int(s0.get("thumbnail_quality") or 0),
            "trend_momentum": int(s0.get("trend_momentum") or 0),
            "evergreen": int(s0.get("evergreen") or 0),
            "popularity": int(s0.get("popularity") or 0),
        }
    if brief:
        yt_scores["expected_watch_time_sec"] = int(brief.get("expected_watch_time_sec") or 0)
        yt_scores["ctr_hint"] = int(brief.get("expected_click_through_potential") or 0)
        if yt_scores["ctr_hint"] and not yt_scores.get("clickability"):
            yt_scores["clickability"] = yt_scores["ctr_hint"]
    if market:
        yt_scores["avg_views"] = float(market.get("average_view_count") or 0)
        yt_scores["avg_channel_size"] = float(market.get("average_channel_size") or 0)
    if yt_scores:
        signals["youtube"] = yt_scores

    gn = google_news or {}
    sample = gn.get("sample") or []
    if sample:
        first = sample[0] if isinstance(sample[0], dict) else {}
        sc = first.get("scores") or {}
        signals["google_news"] = {
            "breaking_news": int(sc.get("breaking_news") or 0),
            "educational": int(sc.get("educational_potential") or 0),
            "psychology": int(sc.get("psychology") or 0),
            "evergreen": int(sc.get("evergreen") or 0),
            "virality": int(sc.get("virality") or 0),
            "freshness": int(sc.get("freshness") or 0),
        }

    xref = cross_reference or brief.get("cross_reference") or {}
    sources = list(xref.get("sources") or [])
    if "reddit_trends" in sources or xref.get("has_reddit"):
        signals["reddit"] = {"discussion": 65 if xref.get("has_reddit") else 50}
    if "wikipedia_trending" in sources or xref.get("has_wikipedia"):
        signals["wikipedia"] = {"authority": 70}
    if "google_trends" in sources or xref.get("has_google_trends"):
        signals["google_trends"] = {"demand": 60}
    if internal_analytics:
        signals["internal_analytics"] = {
            k: internal_analytics[k]
            for k in ("historical_ctr", "historical_retention", "subscriber_rate")
            if k in internal_analytics
        }
    signals["cross_reference"] = {
        "agreeing_sources": int(xref.get("agreeing_sources") or len(sources)),
        "sources": sources[:24],
        "has_google_news": bool(xref.get("has_google_news")),
        "has_youtube": bool(xref.get("has_youtube")),
        "has_reddit": bool(xref.get("has_reddit")),
        "has_wikipedia": bool(xref.get("has_wikipedia")),
        "has_google_trends": bool(xref.get("has_google_trends")),
    }
    return signals


def analyze_topic(
    topic: str,
    *,
    category: str = "general",
    angle: str = "",
    discovery_type: str | None = None,
    youtube_intelligence: dict[str, Any] | None = None,
    google_news: dict[str, Any] | None = None,
    production_brief: dict[str, Any] | None = None,
    cross_reference: dict[str, Any] | None = None,
    internal_analytics: dict[str, Any] | None = None,
) -> AudienceIntelligenceReport:
    """Produce a full Audience Intelligence report for one topic."""
    brief = production_brief or {}
    signals = _extract_provider_signals(
        youtube_intelligence=youtube_intelligence,
        google_news=google_news,
        production_brief=brief,
        cross_reference=cross_reference,
        internal_analytics=internal_analytics,
    )
    text = " ".join(
        [
            topic,
            angle,
            str(brief.get("reasoning") or ""),
            " ".join(str(t) for t in (brief.get("keywords") or [])),
        ]
    )
    drivers = score_psychological_drivers(text, signals=signals)
    dtype = discovery_type or str(brief.get("recommended_video_type") or "") or None
    engagement = estimate_engagement(drivers, signals=signals, recommended_type=dtype or "short")
    # Prefer YT watch-time when present
    yt = signals.get("youtube") or {}
    if yt.get("expected_watch_time_sec"):
        engagement.average_watch_time_sec = int(yt["expected_watch_time_sec"])

    profile = build_audience_profile(drivers, category=category)
    creative = build_creative_directives(topic, drivers, engagement, discovery_type=dtype)
    attention = human_attention_score(drivers, engagement)

    agreeing = int((signals.get("cross_reference") or {}).get("agreeing_sources") or 0)
    conf = min(1.0, 0.45 + 0.08 * min(agreeing, 5) + 0.002 * attention)
    if yt:
        conf = min(1.0, conf + 0.08)
    if signals.get("google_news"):
        conf = min(1.0, conf + 0.05)

    reasoning = (
        f"Human Attention Score {attention}/100. "
        f"Top drivers: curiosity={drivers.curiosity_potential}, "
        f"education={drivers.educational_value}, emotion={drivers.emotional_intensity}. "
        f"CTR≈{engagement.ctr_potential}, retention≈{engagement.retention_probability}, "
        f"share≈{engagement.shareability}. "
        f"Format={creative.recommended_video_format}; "
        f"hook='{creative.suggested_opening_hook[:100]}'. "
        f"Cross-ref sources={agreeing}."
    )

    report = AudienceIntelligenceReport(
        topic=topic,
        human_attention_score=attention,
        psychological_drivers=drivers,
        engagement=engagement,
        audience_profile=profile,
        creative=creative,
        cross_reference=dict(signals.get("cross_reference") or {}),
        provider_signals={k: v for k, v in signals.items() if k != "cross_reference"},
        confidence=round(conf, 4),
        reasoning=reasoning,
    )
    log_event(
        logger,
        "audience_intelligence.analyzed",
        topic=topic[:80],
        attention=attention,
        format=creative.recommended_video_format,
        agreeing=agreeing,
    )
    return report


def enrich_queue_item(
    item: dict[str, Any] | Any,
    *,
    youtube_intelligence: dict[str, Any] | None = None,
    google_news: dict[str, Any] | None = None,
    category: str = "general",
) -> dict[str, Any]:
    """Attach audience_intelligence onto a QueueItem dict (additive)."""
    data = item.to_dict() if hasattr(item, "to_dict") else dict(item or {})
    brief = dict(data.get("production_brief") or {})
    report = analyze_topic(
        str(data.get("topic") or ""),
        category=str(data.get("category") or category),
        angle=str(brief.get("reasoning") or ""),
        discovery_type=str(data.get("recommended_video_type") or brief.get("recommended_video_type") or "") or None,
        youtube_intelligence=youtube_intelligence,
        google_news=google_news,
        production_brief=brief,
        cross_reference=brief.get("cross_reference") or {},
    )
    data["audience_intelligence"] = report.to_dict()
    # Align length/format hints when AI recommends a stronger format
    creative = report.creative
    if creative.recommended_video_length_sec:
        data["recommended_length_sec"] = dict(creative.recommended_video_length_sec)
    return data


def enrich_candidate(candidate: dict[str, Any], *, category: str = "general", context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Attach audience_intelligence to an ideation/script candidate (additive)."""
    ctx = context or {}
    topic = str(candidate.get("title") or candidate.get("topic") or ctx.get("subject") or "")
    report = analyze_topic(
        topic,
        category=str(ctx.get("trend_category") or category),
        angle=str(candidate.get("angle") or candidate.get("hook") or ""),
        discovery_type=str(candidate.get("recommended_video_type") or "") or None,
        youtube_intelligence=ctx.get("youtube_search_intelligence"),
        google_news=(ctx.get("discovery") or {}).get("google_news") if isinstance(ctx.get("discovery"), dict) else ctx.get("google_news"),
        production_brief=candidate.get("discovery_brief") or {},
        cross_reference=((candidate.get("discovery_brief") or {}).get("cross_reference") or {}),
    )
    candidate["audience_intelligence"] = report.to_dict()
    # Prefer AI opening hook for Agent 3 when stronger
    if report.creative.suggested_opening_hook:
        candidate["hook"] = report.creative.suggested_opening_hook
        candidate["audience_opening_hook"] = report.creative.suggested_opening_hook
    candidate["human_attention_score"] = report.human_attention_score
    candidate["recommended_video_format"] = report.creative.recommended_video_format
    candidate["estimated_runtime_hint_sec"] = report.engagement.average_watch_time_sec
    return candidate
