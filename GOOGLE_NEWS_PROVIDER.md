# Google News RSS Provider

**Status:** Production  
**Provider key:** `google_news`  
**Module:** `providers/news/google_news_provider.py`  
**Trend adapter:** `providers/trend_sources/google_news.py`

Google News is a primary discovery intelligence source for Agent 0. It feeds SEO, Psychology, Research, and Video Production via the universal `Trend` contract — not raw headlines dumps.

---

## Architecture

```
Google News RSS (public)
        │
        ▼
providers/news/google_news_provider.py
  • fetch + disk cache (TTL)
  • safe XML parse (ElementTree)
  • filter (dupes / spam / authority / age / language)
  • score → ArticleScores
  • emit DiscoveryItem (provider="Google News")
        │
        ▼
providers/trend_sources/google_news.py
  DiscoveryItem → Trend (source=google_news)
        │
        ▼
TrendDiscoveryManager → Discovery Engine
  + cross_reference.boost_multi_source_confidence
  + breaking_news gate (class: news)
        │
        ▼
QueueItem / PRODUCTION_QUEUE
```

**Rules**

- Never expose raw XML to UI, logs, or reports.
- No API key required (public RSS).
- Failures are isolated — other providers continue.
- Demo fallback only if the live pull returns nothing / errors.

---

## RSS sources

| Feed key | Google News section |
|----------|---------------------|
| `top_stories` | Homepage Top Stories |
| `world` | World |
| `us` | Nation / US |
| `business` | Business |
| `technology` | Technology |
| `science` | Science |
| `health` | Health |
| `entertainment` | Entertainment |
| `sports` | Sports |

Plus topic search:

`https://news.google.com/rss/search?q=…&hl=…&gl=…&ceid=…`

Locale params default to `hl=en-US`, `gl=US`, `ceid=US:en`.

---

## Refresh timing & caching

| Setting | Env | Default |
|---------|-----|---------|
| Feed TTL | `GOOGLE_NEWS_REFRESH_SEC` | `900` (15 min) |
| Max article age | `GOOGLE_NEWS_MAX_AGE_HOURS` | `48` |
| English-only filter | `GOOGLE_NEWS_ENGLISH_ONLY` | `1` |

Cache location: `data/provider_runtime/cache/google_news/`  
Identical feed URLs are not re-downloaded inside the TTL window.

---

## DiscoveryItem

| Field | Description |
|-------|-------------|
| `title` | Normalized headline |
| `summary` | HTML-stripped description |
| `url` | Article / Google News link |
| `publisher` | Source name |
| `publish_time` | ISO-8601 UTC when available |
| `category` | Feed / inferred category |
| `region` | Detected region / country |
| `language` | Estimated language |
| `scores` | See below |
| `provider` | Always `"Google News"` |

---

## Scoring

Each article receives 0–100 scores:

| Score | Signal |
|-------|--------|
| Breaking News | Urgency cues + recency |
| Educational Potential | Explainers / science / how-why |
| Virality | Viral / record / celebrity cues |
| Evergreen | Guides / history / “what is” |
| SEO Opportunity | Blend of edu + evergreen + freshness |
| Competition Estimate | Higher for breaking/viral topics |
| Psychology | Emotion / controversy cues |
| Freshness | Age decay from `publish_time` |
| Confidence | Blend + publisher + language |

These map into `Trend` fields (`freshness`, `competition`, `confidence`, `growth_pct`, `velocity`, `search_volume`) for Discovery Engine scoring.

---

## Filtering

Removed automatically:

- Duplicate headlines (normalized)
- Spam / clickbait patterns
- Low-authority domains
- Empty feeds (yield `[]`, not crash)
- Malformed XML (`GoogleNewsProviderError`, no raw dump)
- Non-English (when `GOOGLE_NEWS_ENGLISH_ONLY=1`)
- Articles older than `GOOGLE_NEWS_MAX_AGE_HOURS`

---

## Trend Engine cross-reference

`services/discovery/cross_reference.py` boosts `Trend.confidence` when multiple providers (Google News, YouTube, Reddit, Wikipedia, …) discuss the same topic cluster.

`google_news` is registered as a reputable **news** class in `breaking_news.py` for multi-source verification.

Future: Google Trends (when approved) plugs in the same boost path without changing DiscoveryItem.

---

## Usage

```python
from providers.news import get_google_news_provider

gn = get_google_news_provider()
items = gn.pull_latest(feeds=["science", "technology"], query="black holes", limit=10)
# items are DiscoveryItem — never XML
```

CLI validation:

```bash
./venv/bin/python scripts/verify_google_news_e2e.py
```

Unit tests:

```bash
./venv/bin/python -m pytest tests/test_google_news_provider.py -q
```

---

## Future expansion

- Google Trends correlation when approved
- Publisher authority scoring via domain graph
- Per-region feed packs (GB, CA, AU, …)
- Streaming refresh worker for continuous Agent 0 loops
- Stronger language ID (optional langdetect) without new deps by default
