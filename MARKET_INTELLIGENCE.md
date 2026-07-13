# Market Intelligence Department — Agent 11

The company's strategic planning engine. It continuously discovers,
analyzes, predicts, prioritizes, and recommends the highest-value content
opportunities — and answers one question for every other system:

> **"What should Generational create next?"**

It never generates content. It returns structured `MarketOpportunity`
objects, roadmaps, and reports — the Production Pipeline turns them into
content through the orchestrator.

---

## 1. Where it sits

```
providers/trend_sources/        18 signal providers (auto-discovered)
        ↓
services/trends/                Agent 1 — normalization + base scoring
        ↓
services/trend_intelligence/    Agent 11 v1 — signal QC, base forecasts,
        ↓                       classification, per-opportunity recommendations
services/market_intelligence/   Agent 11 v2 (THIS) — competition analysis,
        ↓                       market forecasting, ROI, strategy, roadmap,
        ↓                       reports, department query surface
engines/market_intelligence.py  thin pipeline adapter (key: market_intelligence)
```

Pipeline position (all four run inside the orchestrator's **trend** stage):

```
trend_discovery → opportunity_ranking → trend_forecasting → market_intelligence
```

All communication flows Production Pipeline → Orchestrator → Engine
Registry → context/ContentPackage. No engine imports another engine
(Architecture Directive #1, enforced by `tests/test_architecture.py`).

---

## 2. Signal architecture

Every signal source implements one contract — `TrendSourceProvider`
(`providers/trend_sources/base.py`) — and returns only normalized `Trend`
objects. Drop a module in `providers/trend_sources/` and it is
auto-registered; nothing else changes.

Current sources (18): Google Trends, YouTube, TikTok, Instagram, Facebook,
X, Reddit, News, RSS, Blog Feeds, Industry Publications, Keyword API,
Internal Analytics, and the seven added with this department:

| Provider key | Signal character |
|---|---|
| `academic_publications` | slow, low-volume, very high confidence — early evergreen indicators |
| `product_launches` | bursty, fresh — early warning for breaking product topics |
| `ai_research` | model releases/benchmarks — high-velocity tech signals |
| `github_trending` | developer adoption — leads mainstream tech content by weeks |
| `developer_communities` | forum/Q&A pain points — strong content-gap indicators |
| `podcast_rankings` | long-form audio interest — predicts durable video demand |
| `search_volume` | raw query demand — highest-volume, high confidence |

All are deterministic placeholders (`_demo.py` seeding) until live APIs
are wired; swapping in a real API changes nothing downstream.
`provider_priorities` in the config weights each source's influence.

## 3. The analysis chain

One pass per topic (`MarketIntelligence.analyze`) runs:

1. **Discovery** — every enabled provider, fault-tolerant (a failing
   provider is skipped and logged, never fatal).
2. **Signal QC** — `services/trend_intelligence/quality.py` drops
   duplicates, near-duplicates, spam, expired and low-confidence signals,
   flags conflicting sources.
3. **Learning calibration** — `learning_bridge.py` reads Agent 9's
   analytics store and produces calibration factors (see §7).
4. **Base scoring** — Agent 1's `rank_opportunities` (untouched).
5. **Competition analysis** — per-trend `COMPETITION_PROFILE_FIELDS`:
   publishing frequency, creator saturation, average views / engagement /
   retention / CTR, market difficulty, content gap score.
6. **Market forecasting** — the configured model produces
   `MARKET_FORECAST_FIELDS`: growth rate, peak date, decline date,
   lifespan, virality potential, saturation, competition level, forecast
   confidence, expected longevity, historical similarity.
7. **Evergreen engine** — one content nature per opportunity:
   `trending | seasonal | evergreen | educational | news | reference`.
8. **Strategy** — ordered strategic actions per opportunity:
   publish immediately, monitor, delay, expand into series, repurpose,
   translate, localize, long-form / short-form versions, variants.
9. **Opportunity assembly** — the `MarketOpportunity`
   (`MARKET_OPPORTUNITY_FIELDS`): ID, platform, topic, category, audience,
   language, region, difficulty, confidence, ROI estimate, competition /
   trend / forecast scores, priority, publish window, content length,
   content type.
10. **Validation** — duplicates collapsed, invalid forecasts and
    missing-signal / low-confidence opportunities dropped, conflicting
    recommendations repaired. Everything is reported, nothing raises.
11. **Roadmap + report** — see §5 and §6.

## 4. Forecast models

`services/market_intelligence/forecasting.py` keeps a model registry:

```python
from services.market_intelligence import register_forecast_model, configure

register_forecast_model("my_ml_model", my_model_fn)   # same signature as momentum
configure(forecast_model="my_ml_model")
```

`momentum` is the deterministic baseline (built on the discovery-layer
forecaster). Unknown model keys fall back to the baseline — a bad config
can degrade quality but never crash the pipeline. `validate_forecast`
rejects impossible outputs (peak after decline, out-of-range confidence,
non-positive lifespan) at the quality gate.

## 5. Roadmap generation

`build_roadmap` turns a validated batch into `ROADMAP_FIELDS`:

- **daily / weekly / monthly** slates (windowed by each opportunity's
  recommended publish window, sized by `daily_slots` etc.)
- **quarterly_strategy** — focus categories (priority × market weight),
  series candidates, evergreen investments, localization targets
- **queues** — `evergreen`, `trending`, `high_roi`, `low_competition`
- **calendar** — dated publish entries (max 2/day, spread inside windows)
  the Publishing Engine can consume

## 6. Reporting

`build_market_report` produces `MARKET_REPORT_FIELDS` per run: executive
summary (headline, counts, averages, recommended next step), opportunity
report, trend forecast report, competition report, ROI report, platform
opportunity report, plus quality findings and the learning calibration
applied. Report generation is diagnostics-only and never raises.

## 7. Learning loop

`learning_bridge.build_calibration` reads Agent 9's analytics store
(read-only — the Analytics Engine is never modified):

| Factor | Improves | Behavior |
|---|---|---|
| `historical_performance` | opportunity ranking | per-category 0-1 factor into Agent 1's scorer |
| `roi_calibration` (0.5–1.5) | ROI predictions | real outcomes scale ROI estimates |
| `confidence_calibration` | forecast confidence | evidence volume earns forecast trust |
| `competition_calibration` | competition estimates | observed results correct difficulty/gap |
| `winner_profiles` → `historical_similarity` | forecasts | matches candidates to proven winners |

With zero history every factor is neutral — behavior is identical until
evidence accumulates. The engine gets smarter with every published item.

## 8. Pipeline integration

The engine (`market_intelligence`) consumes `trend_opportunities` and
writes three **additive** context keys (DATA_CONTRACTS.md §2.3):
`market_opportunities`, `market_roadmap`, `market_intelligence_report`.

Outside the pipeline, the department singleton answers ad-hoc queries:

```python
from services.market_intelligence import get_market_intelligence

department = get_market_intelligence()
department.highest_priority_opportunity("sleep science")
department.top_opportunities("sleep science", n=10)
department.trending_opportunities("sleep science")
department.evergreen_opportunities("sleep science")
department.platform_opportunities("sleep science", "tiktok")
department.localization_opportunities("sleep science")
department.publishing_calendar("sleep science")
department.content_roadmap("sleep science")
department.market_report("sleep science")
```

Analyses are cached per topic for the discovery polling window. Every
answer is structured opportunity data — never scripts, never assets.

## 9. Configuration

`MarketIntelligenceConfig` (`services/market_intelligence/config.py`) —
overrides from `data/market_intelligence/config.json` or
`configure(**overrides)`:

provider priorities · forecast model · ranking weights · opportunity /
confidence thresholds · market weighting (per category) · platform
weighting · localization weighting (language → weight/region) · ROI
weights · roadmap slot counts / queue size.

## 10. Extension guide

- **New signal provider** — one file in `providers/trend_sources/` with a
  `TrendSourceProvider` subclass. Optionally add a priority to
  `provider_priorities`.
- **New forecast model** — `register_forecast_model(key, fn)` and select
  via config.
- **New strategic action** — add to `STRATEGIC_ACTION` and emit it from
  `strategy.strategic_actions` (additive-only).
- **New queue / report section** — append to `ROADMAP_QUEUES` /
  `MARKET_REPORT_SECTIONS` and extend the builder; existing fields are
  never removed or renamed.

## 11. Tests

`tests/test_market_intelligence.py` (42 tests): provider registration and
determinism, learning calibration (neutral / learning / broken store),
competition analysis, forecast contract + model pluggability + validation,
evergreen natures, opportunity contract and ranking, quality gates
(duplicates, invalid forecasts, missing signals, low confidence,
conflicting recommendations), roadmap and calendar, reports, config, the
department query surface, provider-failure resilience, and pipeline
integration (engine registration, contracts, workflow order, additive
context keys).
