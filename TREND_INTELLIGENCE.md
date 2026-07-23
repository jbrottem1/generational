# Generational — Trend Intelligence (Agent 11, v1.0)

The Trend Discovery & Forecasting subsystem: it decides **what the system
should create next** — before any content is generated. It discovers
signals across platforms, cleans them, scores them, predicts where each
one is going, classifies it, and hands the Production Pipeline structured
recommendations. It never writes scripts and never modifies production
engines.

```
providers (13+)          Agent 1 (existing)              Agent 11 (this subsystem)
──────────────           ──────────────────              ─────────────────────────
YouTube, Google          trend_discovery                 trend_forecasting engine
TikTok, Reddit,     →    (normalize → Trend)        →    quality control
RSS, News, Keyword,      opportunity_ranking             forecasting
Instagram, Facebook,     (score 0-100 → rank)            classification
X, Blogs, Industry,                                      recommendation
Internal Analytics                                       OpportunityFeed (query API)
```

---

## 1. Provider architecture

Every trend source implements `TrendSourceProvider`
(`providers/trend_sources/base.py`) and returns only the universal `Trend`
model (`services/trends/models.py`) — topic, keywords, growth, volume,
velocity, competition, freshness, category, country, language, platform,
source, timestamp, confidence. Nothing downstream ever sees a
vendor-specific payload.

**Adding a provider is one step:** drop a module in
`providers/trend_sources/` containing a concrete subclass — the registry
auto-discovers it. No registration code, no engine changes.

Providers (all deterministic placeholders until live APIs swap in):

| Provider key | Platform | Added by |
|---|---|---|
| `google_trends` · `youtube_trending` · `tiktok_trends` · `reddit_trends` · `rss_feeds` · `news_api` · `keyword_api` | various | Agent 1 (v7.0) |
| `instagram_trends` | instagram | **Agent 11** |
| `facebook_trends` | facebook | **Agent 11** |
| `x_trends` | x | **Agent 11** |
| `blog_feeds` | blogs | **Agent 11** |
| `industry_publications` | industry | **Agent 11** |
| `internal_analytics` | internal | **Agent 11** — mines the Knowledge Base `performance` category; proven winners become high-confidence (0.85) signals; deterministic fallback until history accumulates |

A provider that raises is skipped and logged (`TrendDiscoveryManager`);
a provider whose `is_available()` is False is not queried. The pipeline
never crashes on a bad source.

---

## 2. Quality control — `services/trend_intelligence/quality.py`

`review_trends(trends, config)` filters the raw signal batch before
anything is scored or forecast, and returns `(kept, QualityReport)`:

| Check | Handling |
|---|---|
| Low confidence (`< min_confidence`) | dropped |
| Spam (marker phrases, shouting, junk punctuation) | dropped |
| Expired (older than `max_signal_age_hours`, unparseable timestamp) | dropped |
| Stale (freshness `< min_freshness`) | dropped |
| Conflicting signals (same topic, growth spread `> conflict_growth_spread_pct` across sources) | kept, flagged in the report, confidence discounted ×0.7 |
| Exact duplicates (same normalized topic) | collapsed — strongest copy survives |
| Near duplicates (token-overlap similarity `≥ near_duplicate_similarity`) | dropped |

The `QualityReport` (totals, per-reason drop counts, conflict list) is
surfaced in `trend_intelligence_report` so every run is auditable. QC
never raises — a malformed trend is dropped, not fatal.

---

## 3. Forecast Engine — `services/trend_intelligence/forecaster.py`

`forecast_opportunity(opportunity, config)` → `TrendForecast`
(contract: `FORECAST_FIELDS` in `services/trend_intelligence/models.py`):

| Field | Meaning |
|---|---|
| `days_to_peak` | 1–`max_days_to_peak`; fast movers (velocity+growth momentum) peak sooner |
| `expected_lifespan_days` | evergreen categories earn for months, news burns out in days |
| `trajectory` | explosive · rising · steady · flattening · declining |
| `saturation_risk` | 0–1 — competition + staleness + exhausted growth headroom |
| `publishing_window` | `{start, end, start_in_days, end_in_days}` — publish before the peak; evergreen tails extend the close |
| `recommended_posts_per_week` | 1–7 cadence from momentum + evergreen strength |
| `future_opportunity_score` | 0–100 projected score at the window midpoint |
| `forecast_confidence` | 0–1 — provider confidence discounted by signal completeness |

All math is pure and deterministic — same input, same forecast. Real
time-series models can replace individual functions later without touching
the `TrendForecast` contract.

---

## 4. Opportunity classification — `services/trend_intelligence/classifier.py`

Three independent, threshold-driven axes (contract:
`CLASSIFICATION_FIELDS`):

- **lifecycle** — `breaking` · `exploding` · `emerging` · `growing` ·
  `peak` · `declining` (growth/velocity/freshness/competition thresholds)
- **content_type** — `evergreen` · `seasonal` (marker keywords: holidays,
  events) · `recurring` (routine/habit/cadence markers) · `topical`
- **market_reach** — `niche` · `mid_market` · `mass_market`
  (search-volume thresholds)

---

## 5. Recommendation Engine — `services/trend_intelligence/recommender.py`

`recommend_opportunity(opportunity, forecast, classification, config)` →
`OpportunityRecommendation` (contract: `RECOMMENDATION_FIELDS`):
recommended platform, hook direction (by lifecycle), psychology strategy
(by category — maps onto the Psychology Engine's dimensions), duration
range (platform-native), format, thumbnail direction, title direction,
SEO recommendations (primary/secondary keywords, placement, hashtag
count), publishing window, and four numbers:

- `estimated_roi` (0–100) — weighted: opportunity score, category
  monetization, competition headroom, projected future score
- `confidence_score` (0–1) — min(signal confidence, forecast confidence)
- `risk_score` (0–100) — saturation + low confidence + competition
- `priority_score` (0–100) — the "act on this now" number: opportunity
  score, ROI, urgency (time to peak), confidence, risk penalty

Recommendations are **strategy, never content** — Script, Visual, and SEO
engines own actual generation. ROI/priority weights are configuration.

---

## 6. Pipeline integration

### 6.1 The `trend_forecasting` engine (in-pipeline)

`engines/trend_forecasting.py` — a `ContractEngine` that runs inside the
orchestrator's existing **trend** stage, right after `opportunity_ranking`
(`WORKFLOWS["intelligence"]`, `services/orchestrator/stages.py`):

```
trend_discovery → opportunity_ranking → trend_forecasting → research → ...
```

- **input_contract:** `trend_opportunities`
- **output_contract (all additive context keys):** `trend_forecasts`,
  `trend_classifications`, `opportunity_recommendations` (sorted by
  priority), `trend_intelligence_report` (QC results, classification
  histograms, historical-performance factor, top recommendation)
- Existing keys (`trends`, `trend_opportunities`, `top_opportunity`,
  `trend_keywords`, `trend_dashboard`) are never modified.
- Per Architecture Directive #1 it imports no other engine; all logic
  lives in `services/trend_intelligence/`.

### 6.2 The OpportunityFeed (on-demand query surface)

`services/trend_intelligence/feed.py` — what the Production Pipeline (or
any autonomy agent) calls to ask "what should we create?":

```python
from services.trend_intelligence import get_opportunity_feed

feed = get_opportunity_feed()
feed.top_opportunity("sleep science", category="science")   # the single best bet
feed.top("sleep science", n=10)                             # top 10
feed.emerging("sleep science")                              # breaking/emerging/exploding
feed.evergreen("sleep science")                             # long-tail earners
feed.for_platform("sleep science", "tiktok")                # platform-specific
feed.highest_roi("sleep science")                           # ranked by estimated ROI
feed.highest_confidence("sleep science")                    # ranked by confidence
```

Every result is one enriched dict: the scored opportunity **plus** its
`forecast`, `classification`, and `recommendation`. Structured
opportunities only — never scripts. Discovery passes are cached per topic
for `poll_interval_minutes` (`needs_refresh()` / `refresh()` expose the
polling loop for a future scheduler agent).

---

## 7. Learning integration

`services/trend_intelligence/history.py` reads the Knowledge Base
`performance` category (written by Agent 9's Analytics & Learning engines)
and distills it into the 0–1 `historical_performance` factor that
`services/trends/scorer.py` already accepts. The feed and forecasting
engine pass it into every ranking run — so rankings automatically improve
as real performance data accumulates. With no history the factor is the
neutral 0.5 (identical behavior to pre-learning).

The `internal_analytics` provider closes the loop from the other side:
topics that historically performed re-enter discovery as high-confidence
signals.

The Learning Engine can also retune Agent 11's weights at runtime via
`configure(priority_weights=..., roi_weights=...)` — weights are data,
not code.

---

## 8. Configuration — `services/trend_intelligence/config.py`

Everything is configurable through one `TrendIntelligenceConfig`
dataclass: regions, languages, platforms, topic watchlist,
enabled/disabled providers, polling interval, per-provider limits,
forecast horizons, all classification thresholds, all QC gates
(confidence, age, freshness, similarity, conflict spread), and the
ROI/priority weight tables.

Sources of configuration, in precedence order:

1. `configure(**overrides)` — programmatic (Learning Engine, tests)
2. `data/trend_intelligence/config.json` — optional file, loaded on first use
3. Dataclass defaults

Unknown keys in the file are ignored (forward-compatible);
`configure()` rejects unknown keys (typo safety). Agent 1's base scorer
weights (`FACTOR_WEIGHTS`) are intentionally NOT touched by this config.

---

## 9. Extension guide

| To add… | Do this |
|---|---|
| A new trend source | Drop one `TrendSourceProvider` subclass file in `providers/trend_sources/` — auto-discovered |
| A live API behind an existing placeholder | Replace that provider's `discover()` body; keep returning `Trend` objects — nothing else changes |
| A new classification label | Extend the rule + threshold in `classifier.py` and the label tuple in `models.py` (additive) |
| A new recommendation field | Append to `OpportunityRecommendation` + `RECOMMENDATION_FIELDS` (additive-only) |
| A real forecasting model | Replace individual functions in `forecaster.py`; the `TrendForecast` contract is stable |
| A new feed query | Add a method to `OpportunityFeed` that filters/sorts the enriched dicts |
| Tuned weights from learning | `configure(priority_weights=..., roi_weights=...)` or ship `data/trend_intelligence/config.json` |

## 10. Testing

`tests/test_trend_forecasting.py` — provider auto-discovery and
normalization, internal-analytics KB mining, forecast contract/ranges/
determinism/orderings, all classification rules, recommendation contract
and orderings, every QC path (duplicates, near-duplicates, expiry,
staleness, spam, low confidence, conflicts, malformed timestamps),
configuration behavior and validation, learning integration (neutral →
history-driven), the full feed query surface, provider-failure recovery,
engine contract validation, and pipeline/orchestrator integration.

*Maintained by Agent 11 (Trend Discovery & Forecasting). Contracts are
additive-only; changes to shared files listed in `AGENT_WORKFLOW.md` §2.3
require Agent 1 review.*
