"""Google News RSS — production discovery intelligence source.

Pulls topic/section RSS feeds, parses XML safely, filters spam/duplicates,
scores articles for SEO / psychology / production potential, and emits
unified DiscoveryItem objects (provider="Google News").

No API key required. Respects configurable refresh TTL via disk cache.
Never exposes raw XML to callers — only structured DiscoveryItem results.
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote_plus, urlparse

from core.log import get_logger, log_event
from services.provider_runtime.http_client import HttpRequest, get_default_transport

logger = get_logger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CACHE_DIR = _PROJECT_ROOT / "data" / "provider_runtime" / "cache" / "google_news"

PROVIDER_NAME = "Google News"
PROVIDER_KEY = "google_news"

# Google News public RSS endpoints (no auth).
FEED_CATALOG: dict[str, str] = {
    "top_stories": "https://news.google.com/rss?hl={hl}&gl={gl}&ceid={ceid}",
    "world": "https://news.google.com/rss/headlines/section/topic/WORLD?hl={hl}&gl={gl}&ceid={ceid}",
    "us": "https://news.google.com/rss/headlines/section/topic/NATION?hl={hl}&gl={gl}&ceid={ceid}",
    "business": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl={hl}&gl={gl}&ceid={ceid}",
    "technology": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl={hl}&gl={gl}&ceid={ceid}",
    "science": "https://news.google.com/rss/headlines/section/topic/SCIENCE?hl={hl}&gl={gl}&ceid={ceid}",
    "health": "https://news.google.com/rss/headlines/section/topic/HEALTH?hl={hl}&gl={gl}&ceid={ceid}",
    "entertainment": "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl={hl}&gl={gl}&ceid={ceid}",
    "sports": "https://news.google.com/rss/headlines/section/topic/SPORTS?hl={hl}&gl={gl}&ceid={ceid}",
}

SEARCH_FEED = "https://news.google.com/rss/search?q={query}&hl={hl}&gl={gl}&ceid={ceid}"

DEFAULT_REFRESH_SEC = 900  # 15 minutes
DEFAULT_MAX_AGE_HOURS = 48

# Domains that routinely fail educational / authority bars.
LOW_AUTHORITY_DOMAINS = frozenset(
    {
        "beforeitsnews.com",
        "infowars.com",
        "naturalnews.com",
        "theonion.com",
        "clickhole.com",
        "worldnewsdailyreport.com",
        "yournewswire.com",
        "newsbreak.com",
    }
)

SPAM_PATTERNS = re.compile(
    r"(click here|you won'?t believe|one weird trick|shocking|must see|"
    r"doctors hate|gone viral!!!|free iPhone|crypto giveaway)",
    re.I,
)

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_NON_LATIN_RE = re.compile(r"[^\x00-\x7F\u00C0-\u024F]")

_ENGLISH_MARKERS = frozenset(
    "the a an and or of to in for on with by from that this is are was were "
    "be been being have has had will would can could should about into over "
    "after before during new how what when why who which".split()
)

_EDU_CUES = re.compile(
    r"\b(how|why|explained|science|research|study|discover|history|"
    r"what is|guide|facts|climate|space|biology|physics|health)\b",
    re.I,
)
_BREAKING_CUES = re.compile(
    r"\b(breaking|just in|urgent|developing|live updates|announces|"
    r"announced|explosion|crash|attack|earthquake|alert)\b",
    re.I,
)
_VIRAL_CUES = re.compile(
    r"\b(viral|shock|amazing|record|historic|unprecedented|goes viral|"
    r"millions|celebrity|scandal)\b",
    re.I,
)
_EVERGREEN_CUES = re.compile(
    r"\b(how to|guide|explained|history of|beginner|basics|what is|"
    r"ultimate|complete|encyclopedia)\b",
    re.I,
)
_PSYCH_CUES = re.compile(
    r"\b(fear|hope|anger|surprise|awe|controversy|secret|hidden|"
    r"threat|crisis|miracle|inspire|outrage)\b",
    re.I,
)

FetchFn = Callable[[str], bytes]


class GoogleNewsProviderError(RuntimeError):
    """Safe error for Google News RSS failures (never includes raw XML)."""


@dataclass
class ArticleScores:
    breaking_news: int = 0
    educational_potential: int = 0
    virality: int = 0
    evergreen: int = 0
    seo_opportunity: int = 0
    competition_estimate: int = 50
    psychology: int = 0
    freshness: int = 0
    confidence: int = 0

    def to_dict(self) -> dict[str, int]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ArticleScores":
        return cls(
            breaking_news=int(data.get("breaking_news", 0)),
            educational_potential=int(data.get("educational_potential", 0)),
            virality=int(data.get("virality", 0)),
            evergreen=int(data.get("evergreen", 0)),
            seo_opportunity=int(data.get("seo_opportunity", 0)),
            competition_estimate=int(data.get("competition_estimate", 50)),
            psychology=int(data.get("psychology", 0)),
            freshness=int(data.get("freshness", 0)),
            confidence=int(data.get("confidence", 0)),
        )


@dataclass
class DiscoveryItem:
    """Unified Google News discovery result for the Generational pipeline."""

    title: str
    summary: str = ""
    url: str = ""
    publisher: str = ""
    publish_time: str = ""
    category: str = "general"
    region: str = "US"
    language: str = "en"
    scores: ArticleScores = field(default_factory=ArticleScores)
    provider: str = PROVIDER_NAME
    feed: str = ""
    article_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "summary": self.summary,
            "url": self.url,
            "publisher": self.publisher,
            "publish_time": self.publish_time,
            "category": self.category,
            "region": self.region,
            "language": self.language,
            "scores": self.scores.to_dict(),
            "provider": self.provider,
            "feed": self.feed,
            "article_id": self.article_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DiscoveryItem":
        scores_raw = data.get("scores") or {}
        scores = (
            scores_raw
            if isinstance(scores_raw, ArticleScores)
            else ArticleScores.from_dict(dict(scores_raw))
        )
        return cls(
            title=str(data.get("title") or ""),
            summary=str(data.get("summary") or ""),
            url=str(data.get("url") or ""),
            publisher=str(data.get("publisher") or ""),
            publish_time=str(data.get("publish_time") or ""),
            category=str(data.get("category") or "general"),
            region=str(data.get("region") or "US"),
            language=str(data.get("language") or "en"),
            scores=scores,
            provider=str(data.get("provider") or PROVIDER_NAME),
            feed=str(data.get("feed") or ""),
            article_id=str(data.get("article_id") or ""),
        )


def _clamp(value: float, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, int(round(value))))


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _strip_html(text: str) -> str:
    cleaned = _TAG_RE.sub(" ", html.unescape(text or ""))
    return _WS_RE.sub(" ", cleaned).strip()


def normalize_headline(title: str) -> str:
    """Normalize for duplicate detection."""
    text = _strip_html(title).lower()
    # Drop trailing " - Publisher"
    if " - " in text:
        text = text.rsplit(" - ", 1)[0]
    if " | " in text:
        text = text.rsplit(" | ", 1)[0]
    text = _PUNCT_RE.sub(" ", text)
    return _WS_RE.sub(" ", text).strip()


def estimate_language(text: str) -> str:
    """Lightweight language estimate — en vs other."""
    blob = _strip_html(text).lower()
    if not blob:
        return "und"
    non_latin = len(_NON_LATIN_RE.findall(blob))
    if non_latin > max(3, len(blob) // 8):
        return "other"
    tokens = [t for t in _PUNCT_RE.sub(" ", blob).split() if t]
    if not tokens:
        return "und"
    hits = sum(1 for t in tokens if t in _ENGLISH_MARKERS)
    ratio = hits / max(1, min(len(tokens), 40))
    return "en" if ratio >= 0.12 or (hits >= 2 and non_latin == 0) else "other"


def detect_region(*, country: str = "US", publisher: str = "", url: str = "") -> str:
    country = (country or "US").upper()
    host = ""
    try:
        host = (urlparse(url).netloc or "").lower()
    except Exception:  # noqa: BLE001
        host = ""
    if host.endswith(".uk") or host.endswith(".co.uk"):
        return "GB"
    if host.endswith(".ca"):
        return "CA"
    if host.endswith(".au"):
        return "AU"
    pub = (publisher or "").lower()
    if "bbc" in pub or "guardian" in pub:
        return "GB"
    if "reuters" in pub or "associated press" in pub or "ap news" in pub:
        return "WORLD"
    return country


def parse_pub_date(value: str) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError, IndexError, OverflowError):
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(raw.replace("Z", "+0000") if "%z" in fmt else raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def split_title_publisher(title: str, source_text: str = "") -> tuple[str, str]:
    headline = _strip_html(title)
    publisher = _strip_html(source_text)
    if publisher and " - " in headline:
        suffix = f" - {publisher}"
        if headline.endswith(suffix):
            headline = headline[: -len(suffix)].strip()
        else:
            # Case-insensitive publisher suffix
            low = headline.lower()
            needle = f" - {publisher.lower()}"
            if low.endswith(needle):
                headline = headline[: -len(needle)].strip()
    elif not publisher and " - " in headline:
        left, right = headline.rsplit(" - ", 1)
        if 1 < len(right) <= 60:
            headline, publisher = left.strip(), right.strip()
    return headline.strip(), publisher.strip()


def domain_from_url(url: str) -> str:
    try:
        host = (urlparse(url).netloc or "").lower()
    except Exception:  # noqa: BLE001
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host


def is_low_authority(publisher: str, url: str) -> bool:
    domain = domain_from_url(url)
    if domain in LOW_AUTHORITY_DOMAINS:
        return True
    # Google News redirect hosts are fine; check nested publisher hints in path rarely.
    pub = (publisher or "").lower()
    for bad in LOW_AUTHORITY_DOMAINS:
        stem = bad.split(".")[0]
        if stem and stem in pub.replace(" ", ""):
            return True
    return False


def is_spam_headline(title: str, summary: str = "") -> bool:
    blob = f"{title} {summary}"
    if SPAM_PATTERNS.search(blob):
        return True
    letters = [c for c in title if c.isalpha()]
    if letters and sum(1 for c in letters if c.isupper()) / len(letters) > 0.72 and len(letters) > 12:
        return True
    if title.count("!") >= 3:
        return True
    return False


def score_article(
    *,
    title: str,
    summary: str,
    publisher: str,
    publish_time: datetime | None,
    category: str,
    language: str,
) -> ArticleScores:
    blob = f"{title} {summary}"
    age_hours = 999.0
    if publish_time is not None:
        age_hours = max(0.0, (_now_utc() - publish_time).total_seconds() / 3600.0)

    freshness = 95 if age_hours <= 2 else 85 if age_hours <= 6 else 70 if age_hours <= 24 else 45 if age_hours <= 48 else 20
    breaking = 75 if _BREAKING_CUES.search(blob) else 35
    if age_hours <= 3 and category in ("top_stories", "world", "us", "news"):
        breaking = max(breaking, 60)
    if age_hours > 24:
        breaking = min(breaking, 40)

    educational = 70 if _EDU_CUES.search(blob) else 40
    if category in ("science", "health", "technology"):
        educational = max(educational, 65)
    if category in ("entertainment", "sports"):
        educational = min(educational, 45)

    virality = 70 if _VIRAL_CUES.search(blob) else 40
    if breaking >= 70:
        virality = max(virality, 55)
    evergreen = 75 if _EVERGREEN_CUES.search(blob) else 30
    if educational >= 65 and breaking < 50:
        evergreen = max(evergreen, 55)

    psychology = 65 if _PSYCH_CUES.search(blob) else 40
    if breaking >= 70:
        psychology = max(psychology, 55)

    # SEO: educational + searchable phrasing; competition higher for breaking/viral.
    seo = _clamp(0.45 * educational + 0.25 * evergreen + 0.20 * freshness + 0.10 * virality)
    competition = _clamp(35 + 0.35 * virality + 0.25 * breaking - 0.15 * evergreen)

    authority_bonus = 8 if publisher and len(publisher) > 2 else 0
    confidence = _clamp(
        0.30 * freshness
        + 0.20 * educational
        + 0.15 * seo
        + 0.15 * (100 - competition)
        + 0.10 * psychology
        + 0.10 * (90 if language == "en" else 40)
        + authority_bonus
    )

    return ArticleScores(
        breaking_news=_clamp(breaking),
        educational_potential=_clamp(educational),
        virality=_clamp(virality),
        evergreen=_clamp(evergreen),
        seo_opportunity=_clamp(seo),
        competition_estimate=_clamp(competition),
        psychology=_clamp(psychology),
        freshness=_clamp(freshness),
        confidence=_clamp(confidence),
    )


class FeedCache:
    """Disk cache for raw RSS bytes — respects refresh TTL."""

    def __init__(self, cache_dir: Path | str | None = None, ttl_sec: float = DEFAULT_REFRESH_SEC) -> None:
        self._dir = Path(cache_dir) if cache_dir else _DEFAULT_CACHE_DIR
        self._ttl = float(ttl_sec)
        self._hits = 0
        self._misses = 0
        self._dir.mkdir(parents=True, exist_ok=True)

    @property
    def ttl_sec(self) -> float:
        return self._ttl

    def stats(self) -> dict[str, Any]:
        return {"hits": self._hits, "misses": self._misses, "ttl_sec": self._ttl, "dir": str(self._dir)}

    def _path(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self._dir / f"{digest}.json"

    def get(self, url: str) -> bytes | None:
        path = self._path(url)
        if not path.exists():
            self._misses += 1
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if time.time() - float(data.get("cached_at", 0)) > self._ttl:
                path.unlink(missing_ok=True)
                self._misses += 1
                return None
            raw_b64 = data.get("body")
            if not isinstance(raw_b64, str):
                self._misses += 1
                return None
            import base64

            self._hits += 1
            return base64.b64decode(raw_b64.encode("ascii"))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            self._misses += 1
            return None

    def put(self, url: str, body: bytes) -> None:
        import base64

        path = self._path(url)
        try:
            path.write_text(
                json.dumps(
                    {
                        "cached_at": time.time(),
                        "url_hash": hashlib.sha256(url.encode("utf-8")).hexdigest()[:16],
                        "body": base64.b64encode(body).decode("ascii"),
                        "bytes": len(body),
                    }
                ),
                encoding="utf-8",
            )
        except OSError:
            pass


def parse_rss_items(xml_bytes: bytes, *, feed_key: str = "", region: str = "US") -> list[dict[str, Any]]:
    """Parse RSS/Atom XML into structured dicts. Raises on malformed XML."""
    if not xml_bytes or not xml_bytes.strip():
        raise GoogleNewsProviderError("empty feed body")
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise GoogleNewsProviderError(f"malformed XML: {exc}") from None

    # Strip namespaces for simpler traversal
    for el in root.iter():
        if "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]

    channel = root.find("channel")
    items = channel.findall("item") if channel is not None else root.findall("item")
    if not items:
        # Atom fallback
        items = root.findall("entry")

    parsed: list[dict[str, Any]] = []
    for item in items:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if not link:
            link_el = item.find("link")
            if link_el is not None:
                link = (link_el.get("href") or link_el.text or "").strip()
        description = item.findtext("description") or item.findtext("summary") or ""
        pub = item.findtext("pubDate") or item.findtext("published") or item.findtext("updated") or ""
        source_el = item.find("source")
        source_text = ""
        if source_el is not None:
            source_text = (source_el.text or "").strip()
            if not link and source_el.get("url"):
                pass  # keep article link, not source homepage

        if not title:
            continue
        headline, publisher = split_title_publisher(title, source_text)
        parsed.append(
            {
                "title": headline,
                "summary": _strip_html(description)[:500],
                "url": link,
                "publisher": publisher,
                "publish_time_raw": pub,
                "feed": feed_key,
                "region": region,
            }
        )
    return parsed


def _locale_params(country: str = "US", language: str = "en") -> dict[str, str]:
    gl = (country or "US").upper()
    lang = (language or "en").split("-")[0].lower()
    hl = f"{lang}-{gl}" if lang == "en" else lang
    ceid = f"{gl}:{lang}"
    return {"hl": hl, "gl": gl, "ceid": ceid}


class GoogleNewsProvider:
    """Live Google News RSS client for Agent 0 discovery."""

    def __init__(
        self,
        *,
        refresh_sec: float | None = None,
        max_age_hours: float | None = None,
        english_only: bool | None = None,
        cache_dir: Path | str | None = None,
        fetch_fn: FetchFn | None = None,
        cache: FeedCache | None = None,
    ) -> None:
        env_refresh = os.getenv("GOOGLE_NEWS_REFRESH_SEC", "")
        env_age = os.getenv("GOOGLE_NEWS_MAX_AGE_HOURS", "")
        env_en = os.getenv("GOOGLE_NEWS_ENGLISH_ONLY", "1")

        self.refresh_sec = float(
            refresh_sec if refresh_sec is not None else (env_refresh or DEFAULT_REFRESH_SEC)
        )
        self.max_age_hours = float(
            max_age_hours if max_age_hours is not None else (env_age or DEFAULT_MAX_AGE_HOURS)
        )
        self.english_only = (
            english_only if english_only is not None else str(env_en).strip().lower() not in ("0", "false", "no")
        )
        self._fetch_fn = fetch_fn
        self.cache = cache or FeedCache(cache_dir=cache_dir, ttl_sec=self.refresh_sec)
        self._last_pull: dict[str, Any] = {}

    def is_configured(self) -> bool:
        """RSS requires no credentials — always configured."""
        return True

    def validate(self) -> dict[str, Any]:
        return {
            "ok": True,
            "provider": PROVIDER_NAME,
            "key": PROVIDER_KEY,
            "feeds": list(FEED_CATALOG.keys()),
            "refresh_sec": self.refresh_sec,
            "max_age_hours": self.max_age_hours,
            "english_only": self.english_only,
            "cache": self.cache.stats(),
        }

    def feed_url(self, feed_key: str, *, country: str = "US", language: str = "en") -> str:
        template = FEED_CATALOG.get(feed_key)
        if not template:
            raise GoogleNewsProviderError(f"unknown feed: {feed_key}")
        return template.format(**_locale_params(country, language))

    def search_url(self, query: str, *, country: str = "US", language: str = "en") -> str:
        params = _locale_params(country, language)
        params["query"] = quote_plus((query or "").strip())
        return SEARCH_FEED.format(**params)

    def _fetch_bytes(self, url: str) -> bytes:
        if self._fetch_fn is not None:
            return self._fetch_fn(url)
        transport = get_default_transport()
        resp = transport(
            HttpRequest(
                method="GET",
                url=url,
                headers={
                    "User-Agent": "GenerationalDiscoveryBot/1.0 (+local; Google News RSS)",
                    "Accept": "application/rss+xml, application/xml, text/xml, */*",
                },
                timeout_sec=30.0,
            )
        )
        if not resp.ok:
            raise GoogleNewsProviderError(f"network failure status={resp.status}")
        raw = resp.raw
        if not raw and isinstance(resp.body, (bytes, bytearray)):
            raw = bytes(resp.body)
        if not raw and isinstance(resp.body, str):
            raw = resp.body.encode("utf-8", errors="replace")
        if not raw:
            raise GoogleNewsProviderError("empty network response")
        return raw

    def fetch_feed_xml(self, url: str, *, use_cache: bool = True) -> tuple[bytes, bool]:
        if use_cache:
            cached = self.cache.get(url)
            if cached is not None:
                return cached, True
        body = self._fetch_bytes(url)
        if use_cache:
            self.cache.put(url, body)
        return body, False

    def pull_feed(
        self,
        feed_key: str = "top_stories",
        *,
        country: str = "US",
        language: str = "en",
        use_cache: bool = True,
    ) -> list[DiscoveryItem]:
        url = self.feed_url(feed_key, country=country, language=language)
        return self._pull_url(url, feed_key=feed_key, country=country, language=language, use_cache=use_cache)

    def search(
        self,
        query: str,
        *,
        country: str = "US",
        language: str = "en",
        use_cache: bool = True,
    ) -> list[DiscoveryItem]:
        url = self.search_url(query, country=country, language=language)
        return self._pull_url(url, feed_key="search", country=country, language=language, use_cache=use_cache)

    def pull_latest(
        self,
        *,
        feeds: list[str] | None = None,
        country: str = "US",
        language: str = "en",
        query: str | None = None,
        limit: int | None = None,
        use_cache: bool = True,
    ) -> list[DiscoveryItem]:
        """Pull one or more section feeds (+ optional search) and dedupe."""
        keys = list(feeds) if feeds is not None else list(FEED_CATALOG.keys())
        items: list[DiscoveryItem] = []
        errors: list[str] = []
        cache_hits = 0
        for key in keys:
            try:
                url = self.feed_url(key, country=country, language=language)
                if use_cache and self.cache.get(url) is not None:
                    cache_hits += 1
                items.extend(
                    self.pull_feed(key, country=country, language=language, use_cache=use_cache)
                )
            except GoogleNewsProviderError as exc:
                errors.append(f"{key}: {exc}")
                log_event(logger, "google_news.feed_failed", level=30, feed=key, error=str(exc)[:200])
        if query:
            try:
                items.extend(self.search(query, country=country, language=language, use_cache=use_cache))
            except GoogleNewsProviderError as exc:
                errors.append(f"search: {exc}")

        items = dedupe_items(items)
        items.sort(key=lambda i: (i.scores.confidence, i.scores.freshness, i.scores.seo_opportunity), reverse=True)
        if limit is not None:
            items = items[: max(0, int(limit))]

        self._last_pull = {
            "count": len(items),
            "feeds": keys,
            "query": query or "",
            "errors": errors,
            "cache_hits": cache_hits,
            "cache": self.cache.stats(),
        }
        log_event(
            logger,
            "google_news.pull_latest",
            count=len(items),
            feeds=len(keys),
            errors=len(errors),
            cache_hits=cache_hits,
        )
        return items

    def discover_for_topic(
        self,
        topic: str,
        *,
        category: str = "general",
        country: str = "US",
        language: str = "en",
        limit: int = 5,
    ) -> list[DiscoveryItem]:
        """Topic-oriented pull used by the trend-source adapter."""
        feed_hint = _category_to_feed(category)
        feeds = [feed_hint, "top_stories", "science", "technology"]
        # Preserve order, unique
        seen: set[str] = set()
        ordered: list[str] = []
        for f in feeds:
            if f not in seen and f in FEED_CATALOG:
                seen.add(f)
                ordered.append(f)
        items = self.pull_latest(
            feeds=ordered,
            country=country,
            language=language,
            query=topic,
            limit=max(limit * 3, 12),
        )
        # Prefer topical relevance
        topic_tokens = {t for t in normalize_headline(topic).split() if len(t) > 2}
        if topic_tokens:
            scored: list[tuple[int, DiscoveryItem]] = []
            for item in items:
                blob = normalize_headline(f"{item.title} {item.summary}")
                overlap = sum(1 for t in topic_tokens if t in blob)
                scored.append((overlap, item))
            scored.sort(key=lambda p: (p[0], p[1].scores.confidence), reverse=True)
            # Keep some high-confidence general news if overlap is weak
            picked = [it for ov, it in scored if ov > 0][:limit]
            if len(picked) < limit:
                for _, it in scored:
                    if it not in picked:
                        picked.append(it)
                    if len(picked) >= limit:
                        break
            return picked[:limit]
        return items[:limit]

    def _pull_url(
        self,
        url: str,
        *,
        feed_key: str,
        country: str,
        language: str,
        use_cache: bool,
    ) -> list[DiscoveryItem]:
        try:
            xml_bytes, _hit = self.fetch_feed_xml(url, use_cache=use_cache)
        except GoogleNewsProviderError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise GoogleNewsProviderError(f"network failure: {type(exc).__name__}") from None

        try:
            raw_items = parse_rss_items(xml_bytes, feed_key=feed_key, region=country)
        except GoogleNewsProviderError:
            raise

        if not raw_items:
            # Empty but valid feed — not an error; filter returns [].
            return []

        cutoff = _now_utc() - timedelta(hours=self.max_age_hours)
        out: list[DiscoveryItem] = []
        for raw in raw_items:
            title = raw["title"]
            summary = raw.get("summary") or ""
            publisher = raw.get("publisher") or ""
            url_s = raw.get("url") or ""
            pub_dt = parse_pub_date(str(raw.get("publish_time_raw") or ""))

            if not title.strip():
                continue
            if is_spam_headline(title, summary):
                continue
            if is_low_authority(publisher, url_s):
                continue
            if pub_dt is not None and pub_dt < cutoff:
                continue

            lang = estimate_language(f"{title} {summary}")
            if self.english_only and lang not in ("en", "und"):
                continue
            if lang == "und":
                lang = language or "en"

            region = detect_region(country=country, publisher=publisher, url=url_s)
            category = feed_key if feed_key != "search" else _infer_category(title, summary)
            scores = score_article(
                title=title,
                summary=summary,
                publisher=publisher,
                publish_time=pub_dt,
                category=category,
                language=lang,
            )
            article_id = hashlib.sha1(
                f"{normalize_headline(title)}|{publisher}|{url_s}".encode("utf-8")
            ).hexdigest()[:16]
            out.append(
                DiscoveryItem(
                    title=title[:240],
                    summary=summary[:500],
                    url=url_s,
                    publisher=publisher,
                    publish_time=pub_dt.isoformat() if pub_dt else "",
                    category=category,
                    region=region,
                    language=lang,
                    scores=scores,
                    provider=PROVIDER_NAME,
                    feed=feed_key,
                    article_id=article_id,
                )
            )
        return dedupe_items(out)

    @property
    def last_pull_meta(self) -> dict[str, Any]:
        return dict(self._last_pull)


def dedupe_items(items: list[DiscoveryItem]) -> list[DiscoveryItem]:
    """Remove duplicate headlines (keep highest confidence)."""
    best: dict[str, DiscoveryItem] = {}
    for item in items:
        key = normalize_headline(item.title)
        if not key:
            continue
        prev = best.get(key)
        if prev is None or item.scores.confidence > prev.scores.confidence:
            best[key] = item
    return list(best.values())


def _category_to_feed(category: str) -> str:
    c = (category or "general").lower()
    mapping = {
        "science": "science",
        "tech": "technology",
        "technology": "technology",
        "health": "health",
        "business": "business",
        "world": "world",
        "news": "top_stories",
        "entertainment": "entertainment",
        "sports": "sports",
        "us": "us",
        "education": "science",
        "space": "science",
    }
    return mapping.get(c, "top_stories")


def _infer_category(title: str, summary: str) -> str:
    blob = f"{title} {summary}".lower()
    for key, cues in (
        ("science", ("science", "nasa", "climate", "space", "physics", "biology")),
        ("technology", ("tech", "ai", "software", "apple", "google", "chip")),
        ("health", ("health", "vaccine", "hospital", "disease", "fda")),
        ("business", ("market", "stock", "economy", "bank", "inflation")),
        ("sports", ("nba", "nfl", "soccer", "olympics", "match")),
        ("entertainment", ("movie", "hollywood", "celebrity", "netflix")),
    ):
        if any(c in blob for c in cues):
            return key
    return "top_stories"


def discovery_items_to_trends(items: list[DiscoveryItem], *, platform: str = "news") -> list[Any]:
    """Convert DiscoveryItems into universal Trend objects for the Discovery Engine."""
    from services.trends.models import Trend

    trends: list[Trend] = []
    for item in items:
        s = item.scores
        keywords = [w.lower() for w in normalize_headline(item.title).split() if len(w) > 2][:6]
        if item.publisher:
            keywords.append(item.publisher.lower().split()[0])
        trends.append(
            Trend(
                topic=item.title[:120],
                keywords=keywords or [item.category],
                search_volume=max(1, s.seo_opportunity * 800 + s.virality * 200),
                growth_pct=float(min(200.0, s.virality * 1.5 + s.breaking_news * 0.5)),
                velocity=min(1.0, s.breaking_news / 100.0),
                competition=min(1.0, s.competition_estimate / 100.0),
                freshness=min(1.0, s.freshness / 100.0),
                category=item.category if item.category != "top_stories" else "news",
                country=item.region if len(item.region) == 2 else "US",
                language=item.language if item.language != "other" else "en",
                platform=platform,
                source=PROVIDER_KEY,
                timestamp=item.publish_time or _now_utc().isoformat(),
                confidence=min(1.0, s.confidence / 100.0),
            )
        )
    return trends


_provider: GoogleNewsProvider | None = None


def get_google_news_provider(*, refresh: bool = False) -> GoogleNewsProvider:
    global _provider
    if _provider is None or refresh:
        _provider = GoogleNewsProvider()
    return _provider
