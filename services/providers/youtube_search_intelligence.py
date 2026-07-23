"""YouTube Search Intelligence — what people are actively watching.

Production discovery layer on top of YouTubeProvider.
Returns only structured JSON (VideoWatchSignal / TopicIntelligenceReport).
Never exposes raw YouTube API payloads to callers.
"""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from statistics import mean
from typing import Any

from core.log import get_logger, log_event
from services.providers.youtube_provider import YouTubeProvider, get_youtube_provider

logger = get_logger(__name__)

PROVIDER_NAME = "YouTube Search Intelligence"
PROVIDER_KEY = "youtube_search_intelligence"

_ISO_DUR = re.compile(
    r"^P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?$",
    re.I,
)

_EDU_CUES = re.compile(
    r"\b(how|why|explained|science|learn|educational|documentary|tutorial|"
    r"what is|guide|facts|history|physics|biology|chemistry|space|nasa)\b",
    re.I,
)
_EVERGREEN_CUES = re.compile(
    r"\b(how to|beginner|basics|complete guide|explained|history of|"
    r"ultimate|everything you need|101)\b",
    re.I,
)
_CLICK_CUES = re.compile(
    r"\b(you won't believe|secret|shocking|hidden|vs|versus|insane|"
    r"amazing|mind[- ]?blowing|actually|truth about)\b",
    re.I,
)
_SERIES_CUES = re.compile(r"\b(part\s*\d|episode\s*\d|ep\.?\s*\d|#\d+|season\s*\d|series)\b", re.I)
_LIVE_CUES = re.compile(r"\b(breaking|live|just in|update|today|tonight|happening now)\b", re.I)

# Common YouTube category IDs → names (fallback if list_categories unavailable)
_CATEGORY_FALLBACK = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "15": "Pets & Animals",
    "17": "Sports",
    "19": "Travel & Events",
    "20": "Gaming",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology",
    "29": "Nonprofits & Activism",
}


def _clamp(value: float, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, int(round(value))))


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_iso8601_duration(value: str) -> int:
    """Parse YouTube contentDetails.duration (ISO-8601) → seconds."""
    raw = (value or "").strip()
    if not raw:
        return 0
    match = _ISO_DUR.match(raw)
    if not match:
        return 0
    days = int(match.group("days") or 0)
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def pick_thumbnail(thumbnails: dict[str, Any] | None) -> str:
    if not thumbnails:
        return ""
    for key in ("maxres", "standard", "high", "medium", "default"):
        node = thumbnails.get(key) or {}
        url = node.get("url") if isinstance(node, dict) else ""
        if url:
            return str(url)
    return ""


def parse_published_at(value: str) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def recommend_video_type(
    *,
    duration_sec: int,
    title: str,
    description: str,
    evergreen: int,
    freshness_hours: float,
) -> str:
    blob = f"{title} {description}"
    if _LIVE_CUES.search(blob) and freshness_hours <= 48:
        return "live_update"
    if _SERIES_CUES.search(blob) or (evergreen >= 70 and duration_sec >= 180):
        if duration_sec <= 60:
            return "series"  # short series episode
        return "series"
    if 0 < duration_sec <= 60:
        return "short"
    if duration_sec > 60:
        return "long_form"
    # Unknown duration — bias short for educational explainers, long if evergreen cues
    if evergreen >= 65:
        return "long_form"
    return "short"


@dataclass
class VideoWatchScores:
    popularity: int = 0
    velocity: int = 0
    educational: int = 0
    evergreen: int = 0
    clickability: int = 0
    trend_momentum: int = 0
    thumbnail_quality: int = 0
    competition: int = 50

    def to_dict(self) -> dict[str, int]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VideoWatchScores":
        return cls(**{k: int(data.get(k, getattr(cls(), k))) for k in asdict(cls()).keys()})


@dataclass
class VideoWatchSignal:
    """One structured watch-signal — never a raw API item."""

    title: str
    description: str = ""
    channel: str = ""
    channel_id: str = ""
    publish_date: str = ""
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    duration_sec: int = 0
    thumbnail: str = ""
    category: str = ""
    category_id: str = ""
    tags: list[str] = field(default_factory=list)
    language: str = "en"
    video_id: str = ""
    url: str = ""
    scores: VideoWatchScores = field(default_factory=VideoWatchScores)
    provider: str = PROVIDER_NAME

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "channel": self.channel,
            "channel_id": self.channel_id,
            "publish_date": self.publish_date,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "duration_sec": self.duration_sec,
            "thumbnail": self.thumbnail,
            "category": self.category,
            "category_id": self.category_id,
            "tags": list(self.tags),
            "language": self.language,
            "video_id": self.video_id,
            "url": self.url,
            "scores": self.scores.to_dict(),
            "provider": self.provider,
        }


@dataclass
class TopicMarketStats:
    average_view_count: float = 0.0
    average_upload_frequency_per_week: float = 0.0
    average_channel_size: float = 0.0
    sample_size: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UnifiedDiscoveryBrief:
    """Production brief that feeds Agent 3 Script Generation."""

    overall_opportunity_score: int = 0
    confidence: float = 0.0
    reasoning: str = ""
    recommended_video_type: str = "short"  # short | long_form | series | live_update
    estimated_audience: int = 0
    expected_click_through_potential: int = 0
    expected_watch_time_sec: int = 0
    estimated_competition: float = 0.5
    unified_discovery_score: int = 0
    target_platform: str = "youtube_shorts"
    cross_reference: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_opportunity_score": self.overall_opportunity_score,
            "confidence": round(float(self.confidence), 4),
            "reasoning": self.reasoning,
            "recommended_video_type": self.recommended_video_type,
            "estimated_audience": self.estimated_audience,
            "expected_click_through_potential": self.expected_click_through_potential,
            "expected_watch_time_sec": self.expected_watch_time_sec,
            "estimated_competition": round(float(self.estimated_competition), 4),
            "unified_discovery_score": self.unified_discovery_score,
            "target_platform": self.target_platform,
            "cross_reference": dict(self.cross_reference),
        }


@dataclass
class TopicIntelligenceReport:
    topic: str
    videos: list[VideoWatchSignal] = field(default_factory=list)
    market: TopicMarketStats = field(default_factory=TopicMarketStats)
    brief: UnifiedDiscoveryBrief = field(default_factory=UnifiedDiscoveryBrief)
    provider: str = PROVIDER_NAME
    live: bool = False
    quota: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "videos": [v.to_dict() for v in self.videos],
            "market": self.market.to_dict(),
            "brief": self.brief.to_dict(),
            "provider": self.provider,
            "live": self.live,
            "quota": dict(self.quota),
        }


def score_watch_signal(
    *,
    title: str,
    description: str,
    views: int,
    likes: int,
    comments: int,
    duration_sec: int,
    publish_date: datetime | None,
    thumbnail: str,
    tags: list[str],
    category: str,
    market_avg_views: float,
) -> VideoWatchScores:
    blob = f"{title} {description} {' '.join(tags)}"
    age_days = 365.0
    if publish_date is not None:
        age_days = max(0.1, (_now_utc() - publish_date).total_seconds() / 86400.0)

    # Popularity — log-scaled views
    popularity = _clamp(15 + 12 * math.log10(max(views, 1)))

    views_per_day = views / age_days
    velocity = _clamp(10 + 18 * math.log10(max(views_per_day, 1)))
    engagement = (likes + comments) / views if views else 0.0
    velocity = _clamp(0.7 * velocity + 0.3 * min(100, engagement * 8000))

    educational = 72 if _EDU_CUES.search(blob) else 38
    if "education" in (category or "").lower() or "science" in (category or "").lower():
        educational = max(educational, 70)

    evergreen = 70 if _EVERGREEN_CUES.search(blob) else 32
    if educational >= 65 and age_days > 30 and views_per_day > 50:
        evergreen = max(evergreen, 60)

    clickability = 68 if _CLICK_CUES.search(blob) else 42
    if len(title) <= 60 and any(c.isupper() for c in title):
        clickability = min(100, clickability + 8)
    if thumbnail:
        clickability = min(100, clickability + 6)

    # Momentum: recent + high velocity relative to market
    rel = views / max(market_avg_views, 1) if market_avg_views else 1.0
    momentum = _clamp(0.45 * velocity + 0.35 * min(100, rel * 40) + 0.20 * (90 if age_days <= 14 else 40))

    thumb_q = 75 if thumbnail else 25
    low = (thumbnail or "").lower()
    if "maxres" in low or "sddefault" in low:
        thumb_q = 90
    elif "hqdefault" in low or "mqdefault" in low:
        thumb_q = 80
    elif thumbnail and low.endswith("default.jpg") and "hq" not in low and "mq" not in low and "sd" not in low:
        thumb_q = 45

    # Competition: crowded if many high-view peers (proxy via market avg)
    competition = _clamp(30 + 25 * math.log10(max(market_avg_views, 1)) / 2 + (10 if views > market_avg_views else 0))

    return VideoWatchScores(
        popularity=popularity,
        velocity=velocity,
        educational=educational,
        evergreen=evergreen,
        clickability=clickability,
        trend_momentum=momentum,
        thumbnail_quality=thumb_q,
        competition=competition,
    )


def compute_market_stats(
    videos: list[VideoWatchSignal],
    channel_subscribers: dict[str, int] | None = None,
) -> TopicMarketStats:
    if not videos:
        return TopicMarketStats()
    views = [v.view_count for v in videos]
    avg_views = float(mean(views)) if views else 0.0

    dates = [parse_published_at(v.publish_date) for v in videos]
    dates = [d for d in dates if d is not None]
    upload_freq = 0.0
    if len(dates) >= 2:
        span_days = max(1.0, (max(dates) - min(dates)).total_seconds() / 86400.0)
        upload_freq = (len(dates) / span_days) * 7.0
    elif len(dates) == 1:
        upload_freq = 1.0

    subs = []
    for v in videos:
        if channel_subscribers and v.channel_id in channel_subscribers:
            subs.append(channel_subscribers[v.channel_id])
    avg_channel = float(mean(subs)) if subs else 0.0

    return TopicMarketStats(
        average_view_count=round(avg_views, 1),
        average_upload_frequency_per_week=round(upload_freq, 3),
        average_channel_size=round(avg_channel, 1),
        sample_size=len(videos),
    )


def build_unified_brief(
    topic: str,
    videos: list[VideoWatchSignal],
    market: TopicMarketStats,
    *,
    cross_reference: dict[str, Any] | None = None,
    discovery_score_hint: int | None = None,
) -> UnifiedDiscoveryBrief:
    xref = dict(cross_reference or {})
    if not videos:
        return UnifiedDiscoveryBrief(
            reasoning=f"No live YouTube watch signals for '{topic}'.",
            cross_reference=xref,
            confidence=0.2,
        )

    top = max(videos, key=lambda v: v.scores.popularity + v.scores.educational + v.scores.trend_momentum)
    s = top.scores
    avg_edu = mean(v.scores.educational for v in videos)
    avg_click = mean(v.scores.clickability for v in videos)
    avg_mom = mean(v.scores.trend_momentum for v in videos)
    avg_comp = mean(v.scores.competition for v in videos) / 100.0
    avg_ever = mean(v.scores.evergreen for v in videos)

    opportunity = _clamp(
        0.22 * s.popularity
        + 0.18 * avg_mom
        + 0.18 * avg_edu
        + 0.12 * avg_ever
        + 0.12 * avg_click
        + 0.10 * (100 - avg_comp * 100)
        + 0.08 * s.thumbnail_quality
    )

    # Cross-provider agreement lifts confidence + score
    agreeing = int(xref.get("agreeing_sources") or 0)
    conf = min(1.0, 0.55 + 0.08 * min(agreeing, 4) + 0.15 * (s.educational / 100) + 0.10 * (s.popularity / 100))
    if agreeing >= 2:
        opportunity = _clamp(opportunity + 4 * min(agreeing, 3))

    unified = opportunity
    if discovery_score_hint is not None:
        unified = _clamp(0.55 * opportunity + 0.45 * int(discovery_score_hint))

    pub = parse_published_at(top.publish_date)
    age_h = 999.0 if pub is None else (_now_utc() - pub).total_seconds() / 3600.0
    vtype = recommend_video_type(
        duration_sec=top.duration_sec,
        title=top.title,
        description=top.description,
        evergreen=int(avg_ever),
        freshness_hours=age_h,
    )
    if agreeing >= 3 and avg_edu >= 60 and avg_ever >= 55:
        vtype = "series"

    timed = [v.duration_sec for v in videos if v.duration_sec > 0]
    series_platform = "youtube_long" if timed and mean(timed) > 90 else "youtube_shorts"
    target = {
        "short": "youtube_shorts",
        "long_form": "youtube_long",
        "series": series_platform,
        "live_update": "youtube_shorts",
    }.get(vtype, "youtube_shorts")

    # Expected watch time: clamp to type norms
    if vtype == "short":
        watch = min(55, max(25, int(top.duration_sec or 40)))
    elif vtype == "live_update":
        watch = min(90, max(30, int(top.duration_sec or 45)))
    elif vtype == "series":
        watch = min(600, max(90, int(top.duration_sec or 300)))
    else:
        watch = min(720, max(240, int(top.duration_sec or 480)))

    audience = int(max(market.average_view_count, top.view_count * 0.35, 1000))

    reasons = [
        f"Top watch signal: '{top.title[:80]}' ({top.view_count:,} views on {top.channel or 'unknown'}).",
        f"Educational={int(avg_edu)} momentum={int(avg_mom)} clickability={int(avg_click)}.",
        f"Market avg views={market.average_view_count:,.0f}; uploads/week≈{market.average_upload_frequency_per_week:.2f}.",
    ]
    if agreeing:
        reasons.append(
            f"Cross-referenced with {agreeing} other source(s): "
            + ", ".join(xref.get("sources") or [])
        )
    reasons.append(f"Recommend video type: {vtype} → platform {target}.")

    return UnifiedDiscoveryBrief(
        overall_opportunity_score=opportunity,
        confidence=round(conf, 4),
        reasoning=" ".join(reasons),
        recommended_video_type=vtype,
        estimated_audience=audience,
        expected_click_through_potential=_clamp(avg_click),
        expected_watch_time_sec=watch,
        estimated_competition=round(avg_comp, 4),
        unified_discovery_score=unified,
        target_platform=target,
        cross_reference=xref,
    )


class YouTubeSearchIntelligence:
    """Discover active watch demand for a candidate topic."""

    def __init__(self, yt: YouTubeProvider | None = None) -> None:
        self._yt = yt
        self._category_cache: dict[str, str] = dict(_CATEGORY_FALLBACK)

    @property
    def yt(self) -> YouTubeProvider:
        if self._yt is None:
            self._yt = get_youtube_provider()
        return self._yt

    def is_configured(self) -> bool:
        return self.yt.is_configured()

    def _ensure_categories(self, region_code: str = "US") -> None:
        if len(self._category_cache) > len(_CATEGORY_FALLBACK):
            return
        try:
            result = self.yt.list_categories(region_code=region_code)
            if not result.get("ok"):
                return
            for item in result.get("items") or []:
                cid = str(item.get("id") or "")
                title = str((item.get("snippet") or {}).get("title") or "")
                if cid and title:
                    self._category_cache[cid] = title
        except Exception:  # noqa: BLE001
            pass

    def _extract_video_id(self, item: dict[str, Any]) -> str:
        raw = item.get("id")
        if isinstance(raw, dict):
            return str(raw.get("videoId") or "")
        return str(raw or "")

    def _to_signal(
        self,
        item: dict[str, Any],
        *,
        language: str,
        market_avg_views: float,
    ) -> VideoWatchSignal | None:
        snippet = item.get("snippet") or {}
        stats = item.get("statistics") or {}
        details = item.get("contentDetails") or {}
        video_id = self._extract_video_id(item)
        if not video_id and item.get("id"):
            video_id = str(item.get("id"))
        title = str(snippet.get("title") or "").strip()
        if not title:
            return None
        views = int(stats.get("viewCount") or 0)
        likes = int(stats.get("likeCount") or 0)
        comments = int(stats.get("commentCount") or 0)
        duration_sec = parse_iso8601_duration(str(details.get("duration") or ""))
        thumb = pick_thumbnail(snippet.get("thumbnails") if isinstance(snippet.get("thumbnails"), dict) else None)
        if not thumb and video_id:
            thumb = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
        cat_id = str(snippet.get("categoryId") or "")
        category = self._category_cache.get(cat_id, cat_id or "general")
        tags = [str(t) for t in (snippet.get("tags") or [])[:12]]
        pub = str(snippet.get("publishedAt") or "")
        lang = str(snippet.get("defaultAudioLanguage") or snippet.get("defaultLanguage") or language or "en")
        scores = score_watch_signal(
            title=title,
            description=str(snippet.get("description") or ""),
            views=views,
            likes=likes,
            comments=comments,
            duration_sec=duration_sec,
            publish_date=parse_published_at(pub),
            thumbnail=thumb,
            tags=tags,
            category=category,
            market_avg_views=market_avg_views,
        )
        return VideoWatchSignal(
            title=title[:200],
            description=str(snippet.get("description") or "")[:500],
            channel=str(snippet.get("channelTitle") or ""),
            channel_id=str(snippet.get("channelId") or ""),
            publish_date=pub,
            view_count=views,
            like_count=likes,
            comment_count=comments,
            duration_sec=duration_sec,
            thumbnail=thumb,
            category=category,
            category_id=cat_id,
            tags=tags,
            language=lang[:8],
            video_id=video_id,
            url=f"https://www.youtube.com/watch?v={video_id}" if video_id else "",
            scores=scores,
        )

    def analyze_topic(
        self,
        topic: str,
        *,
        category: str = "general",
        country: str = "US",
        language: str = "en",
        limit: int = 8,
        cross_reference: dict[str, Any] | None = None,
        discovery_score_hint: int | None = None,
    ) -> TopicIntelligenceReport:
        """Search + enrich + score → structured TopicIntelligenceReport."""
        if not self.is_configured():
            return TopicIntelligenceReport(
                topic=topic,
                live=False,
                brief=UnifiedDiscoveryBrief(
                    reasoning="YouTube API key not configured — Search Intelligence unavailable.",
                    confidence=0.0,
                    cross_reference=dict(cross_reference or {}),
                ),
            )

        self._ensure_categories(country or "US")
        search = self.yt.search_topics(
            topic, max_results=max(limit, 5), region_code=country or "US", relevance_language=language or "en"
        )
        if not search.get("ok"):
            search = self.yt.search_videos(
                topic,
                max_results=max(limit, 5),
                region_code=country or "US",
                order="viewCount",
                relevance_language=language or "en",
            )

        ids: list[str] = []
        for it in search.get("items") or []:
            vid = self._extract_video_id(it)
            if vid:
                ids.append(vid)
        ids = ids[: max(limit, 5)]

        stats = self.yt.video_statistics(ids) if ids else {"ok": False, "items": []}
        items = list(stats.get("items") or []) if stats.get("ok") else []

        # First pass views for market baseline
        prelim_views = [int((it.get("statistics") or {}).get("viewCount") or 0) for it in items]
        market_avg = float(mean(prelim_views)) if prelim_views else 1.0

        videos: list[VideoWatchSignal] = []
        for it in items:
            signal = self._to_signal(it, language=language, market_avg_views=market_avg)
            if signal:
                videos.append(signal)
        videos = videos[:limit]

        # Channel sizes
        channel_ids = list({v.channel_id for v in videos if v.channel_id})
        channel_subs: dict[str, int] = {}
        if channel_ids:
            ch = self.yt.channel_statistics(channel_ids[:10])
            if ch.get("ok"):
                for cit in ch.get("items") or []:
                    cid = str(cit.get("id") or "")
                    subs = int((cit.get("statistics") or {}).get("subscriberCount") or 0)
                    if cid:
                        channel_subs[cid] = subs

        market = compute_market_stats(videos, channel_subs)
        # Re-score with refined market average
        if market.average_view_count > 0:
            for v in videos:
                pub = parse_published_at(v.publish_date)
                v.scores = score_watch_signal(
                    title=v.title,
                    description=v.description,
                    views=v.view_count,
                    likes=v.like_count,
                    comments=v.comment_count,
                    duration_sec=v.duration_sec,
                    publish_date=pub,
                    thumbnail=v.thumbnail,
                    tags=v.tags,
                    category=v.category,
                    market_avg_views=market.average_view_count,
                )

        brief = build_unified_brief(
            topic,
            videos,
            market,
            cross_reference=cross_reference,
            discovery_score_hint=discovery_score_hint,
        )

        report = TopicIntelligenceReport(
            topic=topic,
            videos=videos,
            market=market,
            brief=brief,
            live=True,
            quota=self.yt.quota.snapshot(),
        )
        log_event(
            logger,
            "youtube_search_intelligence.analyzed",
            topic=topic,
            videos=len(videos),
            opportunity=brief.overall_opportunity_score,
            video_type=brief.recommended_video_type,
        )
        return report


def signals_to_trends(videos: list[VideoWatchSignal], *, category: str = "general", country: str = "US") -> list[Any]:
    """Convert watch signals into universal Trend objects."""
    from services.trends.models import Trend

    trends = []
    for v in videos:
        s = v.scores
        keywords = [t.lower() for t in v.tags[:5]] or [
            w.lower() for w in v.title.split()[:6] if len(w) > 2
        ]
        trends.append(
            Trend(
                topic=v.title[:120],
                keywords=keywords,
                search_volume=max(v.view_count, 1),
                growth_pct=float(min(200.0, s.trend_momentum * 1.8)),
                velocity=min(1.0, s.velocity / 100.0),
                competition=min(1.0, s.competition / 100.0),
                freshness=min(1.0, 0.4 + s.trend_momentum / 200.0),
                category=category or "general",
                country=country or "US",
                language=v.language or "en",
                platform="youtube",
                source="youtube_search_trends",
                timestamp=v.publish_date or _now_utc().isoformat(),
                confidence=min(1.0, 0.55 + s.educational / 250.0 + s.popularity / 400.0),
            )
        )
    return trends


_intel: YouTubeSearchIntelligence | None = None


def get_youtube_search_intelligence(*, refresh: bool = False) -> YouTubeSearchIntelligence:
    global _intel
    if _intel is None or refresh:
        _intel = YouTubeSearchIntelligence()
    return _intel
