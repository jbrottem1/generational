# Generational — Analytics & Continuous Learning Engine (Agent 9)

The layer that makes every other engine smarter over time. It generates no
content: it observes performance, attributes outcomes to the upstream
decisions that produced them, and feeds confidence-scored recommendations
back into the system — so every published video makes the next one more
intelligent.

```
Publishing (Agent 7)
    │  publishing_package.jobs[].analytics_ref
    ▼
Analytics Collection  (engines/analytics.py · services/analytics/)
    │  one AnalyticsRecord per item × platform → append-only store
    ▼
Learning Feedback     (engines/learning.py · services/learning/)
    │  insights → recommendations → memory → reports
    ▼
Next run              (learning_recommendations / guidance adapters /
                       Knowledge Base performance → internal_analytics trends)
```

---

## 1. The closed loop in one call

```python
from services.analytics.integration import enable_continuous_learning
from services.orchestrator import run_full_pipeline

enable_continuous_learning()          # idempotent — attaches hooks + listener

result = run_full_pipeline("Create 3 science shorts about black holes")

result.context["analytics_summary"]         # what was measured this run
result.context["learning_report"]           # insights + recommendations
result.context["learning_recommendations"]  # routed per target engine
```

`enable_continuous_learning()` arms three seams (none modify the
orchestrator or any other engine):

1. **`AnalyticsHook` / `LearningHook`** — `OrchestratorHook`s (kinds
   `analytics` / `learning`) that run `run_analytics_stage()` and
   `run_learning_stage()` after every completed pipeline run.
2. **`AnalyticsPublishListener`** — a `PublishListener` that measures
   publishes executed from the scheduled queue outside pipeline runs.
3. **`learning_context_extra()`** — the recommendations payload to merge
   into the next run: `run_full_pipeline(..., context_extra=learning_context_extra())`.

The stages also run standalone:

```python
orch = get_orchestrator()
orch.run_analytics_stage(context)   # StageReport — fills analytics_package slots
orch.run_learning_stage(context)    # StageReport — fills learning_metadata slots
```

Both are safe with empty context (zero items / `insufficient_data`) — they
never fail a run.

---

## 2. Analytics Engine (`key: analytics`)

`engines/analytics.py` (thin `ContractEngine`) + `services/analytics/`
(the logic).

- **Input**: `unified_packages` (canonical ContentPackage dicts; `ideas`
  fallback). Each item's `publishing_package.jobs` carry the
  `analytics_ref` correlation ids Agent 7 issued.
- **Per published item × platform**: one **AnalyticsRecord**
  (`ANALYTICS_RECORD_FIELDS`) —
  - **Metrics** (`ANALYTICS_METRIC_FIELDS`): views, watch time, average
    view duration, audience retention, CTR, likes, comments, shares,
    saves, subscriber growth, followers gained, RPM/CPM placeholders.
  - **Attribution**: posting time, platform, topic, niche, title, hook,
    keywords, psychology strategy + scores, and stable fingerprints for
    the script, thumbnail, voice, and render versions used.
  - **Experiment linkage**: `experiment_id` / `variant_id`.
- **Output**: `analytics_summary` + `analytics_records` context keys; each
  ContentPackage `analytics_package` slot filled (aggregate metrics +
  0-100 composite `performance_score`).
- **Persistence**: `AnalyticsStore` (`data/analytics/records.json`) —
  append-only, deduplicated on `analytics_ref`. Proven outcomes also
  mirror into the Knowledge Base `performance` category, which the
  existing `internal_analytics` trend source mines — so trend discovery
  automatically re-weights proven winners.
- **Providers** (`providers/analytics/`): per-platform
  `AnalyticsProvider` registry. `MockAnalyticsProvider` serves every
  platform deterministically (hash-seeded, `mock: true`) until real APIs
  register via `register_analytics_provider(platform, provider)`.

Scheduled-but-unpublished content yields `pending` records (not persisted)
so the store contains real outcomes only.

## 3. Learning Engine (`key: learning`)

`engines/learning.py` (thin `ContractEngine`) + `services/learning/`.

### Pattern mining (`patterns.py`)

Pure statistics over the cumulative store, across eleven attribution
dimensions (`PATTERN_DIMENSIONS`): hook, psychology strategy, thumbnail
version, voice version, posting hour, platform, topic, niche, video-length
bucket, title, keyword. Every insight (`INSIGHT_FIELDS`) carries samples,
average vs baseline composite score, lift, and a **confidence score**
(sample size × score consistency — one lucky video never rewrites
strategy). Helpers: `best_performers(records, dimension)`,
`worst_performers(...)`, `platform_breakdown(records)`.

### Recommendations + feedback loop (`recommendations.py`)

Insights with enough evidence (`MIN_SAMPLES_FOR_RECOMMENDATION`) become
recommendations (`RECOMMENDATION_FIELDS`) routed to the engines that own
each decision (`DIMENSION_TARGETS` → `TARGET_ENGINES`: psychology,
script_generation, visual_intelligence, voice_audio, seo_optimization,
publishing, trend_discovery). The per-engine **guidance adapters** are the
stable feedback interfaces:

```python
from services.learning import (
    psychology_guidance, script_guidance, visual_guidance,
    voice_guidance, seo_guidance, guidance_for_engine,
)

psychology_guidance(recs)  # {"preferred_strategies": [...], "avoided_strategies": [...], ...}
seo_guidance(recs)         # {"winning_keywords": [...], "best_posting_hours": [...], ...}
```

Per Architecture Directive #1, this module never imports or calls an
engine — upstream engines (or the orchestrator context) consume the
guidance.

### Long-term memory (`memory.py`)

`HistoricalMemory` (`data/analytics/memory.json`) — **append-only**
cumulative knowledge, never overwritten: `successful_strategies`,
`failed_strategies`, `platform_trends`, `evergreen_content`,
`seasonal_content`, `audience_preferences`, `experiment_outcomes`.
`remember()` / `recall()` / `search()`; the learning loop deduplicates
observations it already knows so memory grows signal, not noise.

### Experimentation (`experiments.py`)

`ExperimentManager` (`data/analytics/experiments.json`) supports
`EXPERIMENT_KINDS`: ab, thumbnail, hook, script, posting_time, caption,
voice.

```python
manager = get_experiment_manager()
exp = manager.create_experiment("thumbnail", "Bold vs subtle",
                                [{"label": "bold"}, {"label": "subtle"}], min_samples=3)
variant = manager.assign_variant(exp["experiment_id"], content_id)   # sticky round-robin
manager.record_result(exp["experiment_id"], variant["variant_id"], metrics)
```

Content tagged with `services.analytics.attach_experiment(item, exp_id,
variant_id)` carries the linkage on its analytics records;
`ingest_records()` pulls outcomes straight from the store. Winners are
determined statistically (Welch's z-test over composite scores; the
experiment auto-completes at ≥90% confidence) and concluded experiments
become long-term memory.

### Reporting (`reports.py`)

`build_performance_report(records, period)` — `daily` / `weekly` /
`monthly` (`PERFORMANCE_REPORT_FIELDS`): totals, top and worst content,
per-engine recommendations, trending opportunities (promising
low-sample signals), optimization priorities (confirmed losers), and an
overall confidence score. `render_report_text(report)` renders the
human-readable view; `AnalyticsStore.save_report()` archives to
`data/analytics/reports/`.

---

## 4. Data contracts

See `DATA_CONTRACTS.md` §8. Field tuples in `services/analytics/models.py`
and `services/learning/models.py` are the testable contracts; everything
is a JSON-safe dict, additive-only from 1.0. Agent 9 writes ONLY the
ContentPackage `analytics_package` / `learning_metadata` slots and its own
context keys (`analytics_summary`, `analytics_records`, `learning_report`,
`learning_recommendations`).

## 5. File map

```
engines/analytics.py               # AnalyticsEngine (ContractEngine, key: analytics)
engines/learning.py                # LearningEngine  (ContractEngine, key: learning)
services/analytics/
├── models.py                      # record/package/summary contracts + composite score
├── store.py                       # AnalyticsStore — append-only records + report archive
├── collector.py                   # attribution + records + analytics_package builder
└── integration.py                 # hooks, publish listener, enable_continuous_learning()
services/learning/
├── models.py                      # insight/recommendation/memory/report contracts
├── patterns.py                    # pattern miner (pure statistics)
├── recommendations.py             # recommendation engine + per-engine guidance adapters
├── experiments.py                 # ExperimentManager (A/B + statistical winners)
├── memory.py                      # HistoricalMemory — cumulative, append-only
├── reports.py                     # daily/weekly/monthly performance reports
└── loop.py                        # run_learning() — the full cycle
providers/analytics/               # AnalyticsProvider registry + deterministic mock
data/analytics/                    # records.json, memory.json, experiments.json, reports/
tests/test_analytics_engine.py     # 17 tests
tests/test_learning_engine.py      # 18 tests
```

## 6. Swapping in real platform APIs

Implement `AnalyticsProvider.fetch_metrics(content_id, platform)` returning
an `ANALYTICS_METRIC_FIELDS`-shaped dict and register it:

```python
from providers.analytics import register_analytics_provider

register_analytics_provider("youtube_shorts", YouTubeAnalyticsProvider())
```

Nothing else changes — the engine, records, learning loop, experiments,
and reports all consume the same metric shape.
