# 🚀 Generational

**AI Content Operating System**

Generational is an AI-powered faceless content operating system designed to help creators generate, produce, and distribute content at scale.

## Version 9.12 — Creative Studio UI (Agent 20)

Primary interface for the Generational platform — project workspace, creative
prompt panel, pipeline visualization, live previews, provider status, output
library, and executive dashboard.

```bash
streamlit run app.py
# Open the 🎬 Studio tab
```

Service layer: `services/studio/` (UI adapter over Orchestrator + ProviderRuntime).
UI: `ui/tabs/studio.py`, `ui/studio/components.py`.

See [`STUDIO_UI.md`](STUDIO_UI.md).

## Version 9.11 — End-to-End Workflow Executor (Agent 21)

One user prompt becomes a managed production run — durable `ProjectRun` state,
stage-by-stage Orchestrator execution, checkpoints, retries, resume, and
Studio UI status.

```python
from services.workflow_executor import get_workflow_executor

executor = get_workflow_executor()
run = executor.execute("Create a 45-second YouTube Short about black holes.")
status = executor.get_status(run.run_id)
```

See [`WORKFLOW_EXECUTOR.md`](WORKFLOW_EXECUTOR.md).

## Version 9.10 — Provider Integration & Runtime Engine (Agent 19)

Unified provider abstraction layer — every engine can call real AI services
without knowing which vendor serves the request.

```python
from services.provider_runtime import get_provider_runtime

runtime = get_provider_runtime()
result = runtime.generate_image({"prompt": "cinematic sunset"})
result = runtime.generate_script({"prompt": "Write a 60-second psychology short"})
```

See [`PROVIDER_INTEGRATION.md`](PROVIDER_INTEGRATION.md).

## Version 9.9 — Architecture Review after Agents 12–17 (Agent 1)

Post-integration architecture audit. Full report:
[`ARCHITECTURE_REVIEW.md`](ARCHITECTURE_REVIEW.md) (Architecture Score
**90/100**, Future Readiness **91/100**).

### Preferred distribution pipeline wired

```
packaging → ai_director → creative → character_universe → asset_generation → animation
         → render → post_production → seo → optimization → publish
```

AI Director (18), Creative Studio (12), Asset Generation (14), and Post-Production (17) are
**LIVE**. Optimization Lab (13), Character/Universe (15), and Animation (16)
are registered as `FutureEngine` stubs so their stages exist and skip
cleanly until their feature worktrees merge. Package slots reserved:
`character_universe_package`, `animation_package`, `optimization_package`.

### Governance updates

[`PIPELINE_SPEC.md`](PIPELINE_SPEC.md) · [`AGENT_REGISTRY.md`](AGENT_REGISTRY.md)
· [`SYSTEM_DEPENDENCY_MAP.md`](SYSTEM_DEPENDENCY_MAP.md) ·
[`ENGINE_REGISTRY.md`](ENGINE_REGISTRY.md) · [`ORCHESTRATOR.md`](ORCHESTRATOR.md)
· [`CAPABILITY_MATRIX.md`](CAPABILITY_MATRIX.md) · [`DATA_CONTRACTS.md`](DATA_CONTRACTS.md)
reconciled. Roadmap for Agents 18–30 prioritized in the architecture review.

## Version 9.9 — AI Director (Agent 18)

Every packaged content item now receives executive creative direction before
production begins. The `ai_director` engine consumes upstream intelligence
(psychology, script, visual, audio, trend, market, analytics) and produces
a structured `director_package` — production strategy, platform targets,
creative/visual/animation style, camera plan, pacing, shot plan, character
plan, music/narration/editing direction, optimization hints, asset
requirements, quality targets, and per-agent orchestration notes for Agents
12–17.

```python
from services.orchestrator import Orchestrator

orch = Orchestrator()
report = orch.run_ai_director_stage(context)
# context["ai_director_packages"] — one per item
# context["unified_packages"][i]["director_package"]
```

Pipeline order: `ai_director → creative → asset_generation → render → post_production → seo → publish`

See `AI_DIRECTOR.md`.

## Version 9.8 — Post-Production & Intelligent Editing Engine (Agent 17)

Completed render packages now flow through intelligent post-production
before SEO and publishing. The `post_production` engine consumes render,
audio, creative, and asset packages and produces publication-ready
`post_production_package` deliverables — master edit timelines, scene cuts,
finalized audio mix, styled captions, color grading, motion graphics,
platform-optimized exports, and QC validation.

```python
from services.orchestrator import Orchestrator

orch = Orchestrator()
report = orch.run_post_production_stage(context)
# context["post_production_packages"] — one per item
# context["unified_packages"][i]["post_production_package"]
```

Pipeline order: `asset_generation → render → post_production → seo → publish`

See `POST_PRODUCTION_ENGINE.md`.

## Version 9.7.1 — Asset Generation Production Hardening (Agent 14 Phase 2)

Production-ready extensions on the Universal Asset Generation Engine —
no redesign. Provider registry catalog, latency-aware selection, batch
generation, job-queue interfaces, usage tracking, and structured asset
metadata. Media classes prepared for animation, audio (SFX / music /
voice), and motion graphics. Fourteen adapter stubs (OpenAI Images,
Runway, Flux, Kling, Pika, Luma, Veo, Stable Diffusion, Midjourney
placeholder, …) — still no live API calls.

```python
from services.asset_generation import batch_generate, run_generate
from providers.asset_generation import provider_catalog

batch_generate([request_a, request_b])   # coordinated multi-asset run
run_generate(request)                    # job-queue submit + sync run
provider_catalog()                       # [{name, available, latency_ms, ...}]
```

See `ASSET_GENERATION_ENGINE.md` § Phase 2.

## Version 9.7 — Universal Asset Generation Engine (Agent 14)

Every visual asset the platform uses now flows through one generation
department. The `asset_generation` engine consumes Creative Studio asset
requirements (or fallback scene plans), compiles provider-optimized prompts,
selects the best AI backend, generates with retries and fallback, caches
identical requests, validates quality, and writes production-ready
`asset_package` deliverables — images, thumbnails, video clips, textures,
icons, 3D prep assets, and more.

```python
from services.orchestrator import Orchestrator

context = {"unified_packages": [item_with_creative_package]}
Orchestrator().run_asset_generation_stage(context)
# context["unified_packages"][0]["asset_package"]["assets"]
```

40+ asset types · 12 provider adapters (OpenAI, Google, Runway, Flux, …) ·
deterministic mock fallback · content-address cache · character consistency ·
15 style packs. See `ASSET_GENERATION_ENGINE.md`.

Distribution pipeline: **packaging → asset generation → render → seo → publish**.

## Version 9.6 — Architecture Review & Platform Governance (Agent 1)

A comprehensive architecture audit covering Agents 1-11 (shipped) and
preparing the platform for Agents 12-30. Full report:
[`ARCHITECTURE_REVIEW.md`](ARCHITECTURE_REVIEW.md) (Architecture Score
**88/100**, Future Readiness **90/100**).

### Machine-readable architecture registries

`engines/registry.py` gained read-only introspection: `describe_all()`
(uniform engine self-descriptions), `capability_index()` (49 capability
tags → engine keys), and `dependency_graph()` (declared upstream
dependencies). Four new consistency tests keep stages, workflows,
dependencies, and the index aligned with the registry — dangling keys now
fail the build.

### New governance documents

[`AGENT_REGISTRY.md`](AGENT_REGISTRY.md) (Agents 1-20, departments, future
expansion registry) · [`SYSTEM_DEPENDENCY_MAP.md`](SYSTEM_DEPENDENCY_MAP.md)
(layer diagram, pipeline data flow, live dependency graph, module boundary
rules) · [`CAPABILITY_MATRIX.md`](CAPABILITY_MATRIX.md) ·
[`ENGINE_CAPABILITY_INDEX.md`](ENGINE_CAPABILITY_INDEX.md) ·
[`ARCHITECTURE_REVIEW.md`](ARCHITECTURE_REVIEW.md) (audit, debt, risks,
refactor plan, Agents 16-30 recommendations) · rewritten
[`INTEGRATION_CHECKLIST.md`](INTEGRATION_CHECKLIST.md) (the 14-step
checklist every new engine follows).

### Creative Studio integration (pending)

Agent 12's Creative Studio engine is built on `feature/creative-studio` but
not yet merged here. The `creative` stage slot and `creative_package`
ContentPackage field are reserved; merge Agent 12's branch then follow
`INTEGRATION_CHECKLIST.md` steps 8-9 to register and stage it.

## Version 9.5 — Market Intelligence Department (Agent 11)

The company's strategic planning engine is live. Everything Generational
creates now begins with the Market Intelligence Department: 18 signal
providers (7 new: academic publications, product launches, AI research,
GitHub, developer communities, podcast rankings, search volume) feed a
full market-analysis chain — competition analysis, pluggable market
forecast models, ROI estimation, an evergreen engine, and strategic
actions — producing priority-ranked `MarketOpportunity` objects, a
content roadmap (daily/weekly/monthly, quarterly strategy, four queues,
a dated publishing calendar), and an executive report suite. Analytics
history calibrates every prediction through a learning bridge, so the
department gets smarter with every published item. Structured
opportunities only — never scripts, never creative assets.

```python
from services.market_intelligence import get_market_intelligence

department = get_market_intelligence()
department.highest_priority_opportunity("sleep science")   # what to create next
department.top_opportunities("sleep science", n=10)
department.evergreen_opportunities("sleep science")
department.publishing_calendar("sleep science")
department.market_report("sleep science")                  # executive summary
```

In the pipeline, the `market_intelligence` engine runs inside the trend
stage after `trend_forecasting` and writes `market_opportunities`,
`market_roadmap`, and `market_intelligence_report` to the shared context
(additive only). See `MARKET_INTELLIGENCE.md`.

## Version 9.2 — Analytics & Continuous Learning Engine (Agent 9)

The system now observes its own performance and gets smarter with every
published video. The `analytics` and `learning` stages are live: post-publish
metrics collection, pattern mining, confidence-scored recommendations back to
every upstream engine, an experimentation framework, cumulative long-term
memory, and daily/weekly/monthly performance reports.

```python
from services.orchestrator import get_orchestrator
from services.analytics.integration import enable_continuous_learning

enable_continuous_learning()   # one call arms the closed loop

result = get_orchestrator().run_full_pipeline("Create 3 science shorts...")
result.context["analytics_summary"]        # what was measured
result.context["learning_report"]          # what was learned
result.context["learning_recommendations"] # per-engine feedback for the next run
```

### What's new

- **Analytics Engine** (`engines/analytics.py` + `services/analytics/`) —
  one structured analytics record per published item × platform: views,
  watch time, retention, CTR, average view duration, likes/comments/
  shares/saves, subscriber growth, followers gained, RPM/CPM placeholders —
  plus full attribution (posting time, platform, topic, hook, psychology
  strategy, and script/thumbnail/voice/render version fingerprints).
  Records persist to the append-only store (`data/analytics/records.json`),
  deduplicated on the `analytics_ref` Agent 7 issues, and proven winners
  mirror into the Knowledge Base `performance` category — which the
  `internal_analytics` trend source already mines.
- **Metrics providers** (`providers/analytics/`) — per-platform
  `AnalyticsProvider` registry; a deterministic mock serves every platform
  until real APIs (YouTube Analytics, TikTok Business, Meta Insights) swap
  in with `register_analytics_provider()` — zero engine changes.
- **Learning Engine** (`engines/learning.py` + `services/learning/`) —
  mines the cumulative store across eleven attribution dimensions
  (highest-retention hooks, best psychological triggers, thumbnail styles,
  narration/voice styles, posting times, categories, video lengths,
  titles, keywords, platform-specific performance), each insight carrying
  a confidence score from sample size × consistency.
- **Recommendation Engine + feedback loop** — insights become
  recommendations routed to the engine that owns each decision
  (psychology, script, visual, voice, SEO, publishing, trend discovery)
  via the `learning_recommendations` context key and per-engine guidance
  adapters (`psychology_guidance()`, `script_guidance()`, ...). Every
  ContentPackage gets its `learning_metadata` slot filled.
- **Experimentation framework** (`services/learning/experiments.py`) —
  A/B, thumbnail, hook, script, posting-time, caption, and voice
  experiments with deterministic variant assignment, tracked experiment
  IDs on analytics records, and statistical winners via Welch's z-test.
- **Long-term memory** (`services/learning/memory.py`) — append-only
  cumulative knowledge: successful/failed strategies, platform trends,
  evergreen and seasonal content, audience preferences, experiment
  outcomes. Historical knowledge is never overwritten.
- **Reporting Engine** (`services/learning/reports.py`) — daily / weekly /
  monthly reports: totals, top and worst content, engine recommendations,
  trending opportunities, optimization priorities, confidence — machine-
  readable dicts plus `render_report_text()` for humans.
- **Integration** — the orchestrator's `run_analytics_stage()` /
  `run_learning_stage()` are live; `enable_continuous_learning()` attaches
  `OrchestratorHook`s (kinds `analytics` / `learning`) so every full run
  measures and learns automatically, plus a `PublishListener` that measures
  scheduled-queue publishes outside pipeline runs. No other engine and no
  orchestrator code was modified.
- **35 tests** in `tests/test_analytics_engine.py` +
  `tests/test_learning_engine.py`; full suite passes (504).

Docs: [`ANALYTICS_LEARNING.md`](ANALYTICS_LEARNING.md), plus updates to
`DATA_CONTRACTS.md` §8, `PIPELINE_SPEC.md`, and `ORCHESTRATOR.md`.

## Version 9.1 — Trend Discovery & Forecasting Engine (Agent 11)

The intelligence division: the system now predicts **what to create next**
before any content is generated. A new `trend_forecasting` engine runs
inside the trend stage right after Opportunity Ranking, and a query-able
`OpportunityFeed` serves the same intelligence on demand.

```python
from services.trend_intelligence import get_opportunity_feed

feed = get_opportunity_feed()
feed.top_opportunity("sleep science", category="science")  # the single best bet
feed.top("sleep science", n=10)                            # top 10
feed.emerging("sleep science")                             # breaking / emerging / exploding
feed.evergreen("sleep science")                            # long-tail earners
feed.for_platform("sleep science", "tiktok")               # platform-specific
feed.highest_roi("sleep science")                          # ranked by estimated ROI
feed.highest_confidence("sleep science")                   # ranked by confidence
```

Every result is a structured opportunity — the scored trend plus its
forecast, classification, and recommendation. Never a script.

### What's new

- **Forecast Engine** (`services/trend_intelligence/forecaster.py`) —
  deterministic predictions per opportunity: days to peak, expected
  lifespan, growth trajectory (explosive → declining), saturation risk,
  recommended publishing window and weekly cadence, projected future
  opportunity score, and forecast confidence.
- **Opportunity classification** (`classifier.py`) — three axes:
  lifecycle (breaking · exploding · emerging · growing · peak ·
  declining), content type (evergreen · seasonal · recurring · topical),
  market reach (niche · mid_market · mass_market).
- **Recommendation Engine** (`recommender.py`) — one structured
  recommendation per opportunity: platform, hook direction, psychology
  strategy, duration, format, thumbnail/title direction, SEO guidance,
  publishing window, estimated ROI, confidence, risk, and a single
  priority score. Strategy only; generation stays with the Script,
  Visual, and SEO engines.
- **Quality control** (`quality.py`) — duplicates collapse to the
  strongest copy, near-duplicates drop on token similarity, expired /
  stale / spam / low-confidence signals are filtered, and conflicting
  sources are flagged with confidence discounted. Fully reported in
  `trend_intelligence_report`.
- **Learning integration** (`history.py`) — Knowledge-Base performance
  history becomes the `historical_performance` ranking factor on every
  run, and the new `internal_analytics` provider re-enters proven
  winners as high-confidence signals. Weights retune via
  `configure(...)` — data, not code.
- **Six new provider adapters** (drop-in, auto-discovered):
  `instagram_trends`, `facebook_trends`, `x_trends`, `blog_feeds`,
  `industry_publications`, `internal_analytics` — thirteen sources total,
  all behind the same `TrendSourceProvider` contract.
- **Configuration** (`config.py`) — one dataclass for regions, languages,
  platforms, provider enablement, polling interval, forecast horizons,
  classification thresholds, QC gates, and ROI/priority weights;
  overridable via `data/trend_intelligence/config.json` or
  `configure(**overrides)`.
- **Pipeline integration** — new additive context keys
  (`trend_forecasts`, `trend_classifications`,
  `opportunity_recommendations`, `trend_intelligence_report`); existing
  trend keys untouched. The engine is a `ContractEngine` with declared
  contracts, validated on every run.
- **41 tests** in `tests/test_trend_forecasting.py`; full suite passes.

Docs: `TREND_INTELLIGENCE.md` (architecture, contracts, extension guide),
plus updates to `DATA_CONTRACTS.md` §2.2, `PIPELINE_SPEC.md`,
`ENGINE_REGISTRY.md`, `MASTER_ARCHITECTURE.md`, `AGENT_WORKFLOW.md`.

## Version 9.0 — Complete Integrated Production Pipeline (Agent 9)

Every completed engine now runs inside **one unified production workflow**
behind **one public entry point**. No stage is invoked "on demand" anymore —
one command executes the whole system:

```python
from services.orchestrator import run_full_pipeline

result = run_full_pipeline("Create 3 science shorts about black holes")

result.packages           # list[ProductionPackage] — render + seo + publishing slots filled
result.production_report  # ONE unified Production Report for the entire run
```

### The integrated flow

```
Trend Discovery → Psychology → Script → Visual Intelligence → Voice & Audio
   → refinement + quality gate → media production → packaging
   → Render Engine → Global Content Optimization (SEO) → Publishing
```

The distribution stages (render → seo → publish) execute automatically after
packaging, in the contract order from `PIPELINE_SPEC.md`. Their output is
folded back into the final `ProductionPackage` objects: `render_package`
(Agent 6), enriched `seo_package` + `publishing_packages` handover (Agent 8),
and the `publishing_package` slot with status advanced to
`rendered` / `scheduled` / `published` (Agent 7).

### One Production Report

`build_production_report()` (`services/orchestrator/report.py`) produces a
single JSON-safe report per run, attached to
`PipelineResult.production_report` and `context["production_report"]`:

- **workflow** — the eight production areas (trend discovery, psychology,
  script, visual, voice/audio, render, seo, publishing) each resolved to a
  SUCCESS / WARNING / FAILED outcome with confidence and diagnostics.
- **stages** — every stage report: status, timing, confidence, warnings,
  errors, per-engine steps.
- **engines** — availability/readiness inventory of every engine the run
  touched, with declared input/output contracts.
- **content** — packages produced, publish-ready count, render readiness,
  optimization scores, publishing jobs and platforms.
- **warnings / errors** — the full rollup, one place.

### Validation and graceful degradation

- The workflow engine now runs each `ContractEngine`'s `validate_input` /
  `validate_output` around every step; findings surface as stage warnings
  and `contract_validation` diagnostics — never failures.
- An **unavailable engine** (not registered or `is_ready() == False`) skips
  with a meaningful warning; the pipeline continues.
- A **crashing distribution engine** degrades the run to WARNING with the
  error preserved in the report — finished content is never discarded and
  the pipeline never crashes.
- `publish_mode` defaults to `"scheduled"`, so a full run queues
  timezone-optimized publish jobs without posting anything immediately;
  pass `publish_mode="immediate"` to execute (mock) publishes.

Integration proof: `tests/test_production_pipeline.py` (16 tests) plus the
updated `tests/test_orchestrator.py` / `tests/test_architecture.py`.

## Version 8.5 — Architecture Directive #1: Orchestrator-Only Communication

Engine-to-engine communication is now formally prohibited and automatically
enforced. Full directive: [`ARCHITECTURE_DIRECTIVES.md`](ARCHITECTURE_DIRECTIVES.md).

### The rule

No engine calls another engine — ever. All coordination flows
Orchestrator → ContentPackage/shared context → next engine. Every engine
knows only its declared `input_contract` and `output_contract`.

### Shared analysis library

The two remaining engine-to-engine imports were refactored away into
`engines/analysis.py`, the new shared pure-function library beside
`engines/heuristics.py`: the 18-dimension psychology scorer (previously
imported by the Attention Graph from the Psychology engine) and the script
critique (previously imported by the Revision engine and citation service
from the Critic engine). The Psychology and Critic engines re-export both,
so every existing import path still works.

### Automated enforcement

`tests/test_architecture.py` statically scans every engine module's imports
and fails the suite on any prohibited dependency, verifies engines don't
drive each other through the registry, verifies the orchestrator itself
stays engine-agnostic, and proves at runtime that one command flows through
every stage into `ContentPackage` objects with missing engines degrading
gracefully.

## Version 8.4 — Publishing & Distribution Engine (Agent 7)

The publish stage is live. `engines/publishing/` + `services/publishing/`
prepare completed content — RenderPackage (Agent 6) plus optimization
PublishingPackage (Agent 8) — for every supported publishing provider. No
real platform APIs are called yet: this release ships the complete
publishing architecture with **mock provider adapters**, ready for real
integrations to swap in one file at a time.

### Provider-based, never hardcoded

Seven platform adapters — YouTube Shorts, Instagram Reels, Facebook Reels,
TikTok, X, LinkedIn, Pinterest — implement one `PublishingProvider`
interface (`providers/publishing_provider.py`): per-platform metadata
constraints (title/description/hashtag/duration limits), metadata fitting
with truncation warnings, package validation, provider-specific retry
rules, and a mock `publish()`. Adapters resolve through a registry
(`providers/publishing/`) with platform aliases (`youtube` →
`youtube_shorts`); a future platform is one
`register_publishing_provider()` call — zero engine changes.

### Queue, jobs, retries, history

- **PublishingQueue** — durable JSON-persisted job queue
  (`data/publishing_queue/jobs.json`) with due-job selection.
- **PublishingJob** — one item × one platform, carrying the platform-ready
  publish package, schedule, attempts, and full attempt history
  (`JobStatus`: queued → scheduled → publishing → published / failed /
  cancelled).
- **RetryManager** — configurable policies (retry count, exponential
  backoff, max delay) with provider-specific overrides (TikTok backs off
  harder); exhausted jobs fail safely with their error history intact.
- **PublishingHistory** — append-only attempt log
  (`data/publishing_queue/history.json`), every record carrying an
  `analytics_ref` for the future Analytics Engine.
- **PublishingManager** — coordinates packages, scheduling, queueing,
  provider execution, gates, and listeners behind one interface.

### Timezone-aware scheduling

The `scheduler` engine graduated from its contract stub into
`engines/publishing/scheduler_engine.py`. `PublishingScheduler` supports
immediate publish, explicit publish times, and optimal-window scheduling
from the Optimization Engine's ranked `publish_windows`, resolving each
country's local window hours to concrete UTC timestamps — multiple brands,
channels, and countries schedule independently. Decisions land in the
`publish_schedule` context key (the stub's promised contract).

### The platform publish package

Each job's package (`PLATFORM_PUBLISH_PACKAGE_FIELDS`, v1.0) carries:
video, thumbnail, title, description, hashtags, keywords, captions,
language, country, platform, provider, account reference, publish_time,
timezone, visibility, playlist placeholder, category placeholder, status,
and diagnostics.

### Accounts + future roadmap (interfaces only)

`services/publishing/accounts.py` defines placeholder PublishingAccounts
(multi-brand, multi-channel; credentials/permissions/token slots are
explicit placeholders — **no real credentials are ever stored**) and the
`CredentialProvider` contract. `services/publishing/extensions.py` ships
the extension seams the manager already calls: `PrePublishGate` (approval
workflows / human review), `PublishListener` (analytics callbacks),
`RollbackHandler`, and `RegionalScheduleRule`.

### Orchestrator integration

The `publishing` and `scheduler` engines graduated to live
`ContractEngine`s. `run_publish_stage(context)` schedules then publishes
every publish-eligible item, writes each ContentPackage
`publishing_package` slot (status → `scheduled` / `published`), and
returns a standardized **PublishingResult** (`PUBLISHING_RESULT_FIELDS`)
— with zero items it reports SKIPPED, never crashing the pipeline. Docs:
[`engines/publishing/README.md`](engines/publishing/README.md) and
[`DATA_CONTRACTS.md`](DATA_CONTRACTS.md) §7. Tests: 30 new in
`tests/test_publishing_engine.py` (402 total, all passing).

## Version 8.3 — Global Content Optimization Engine (Agent 8)

The seo stage is live. `engines/seo_optimization.py` + `services/seo/`
transform completed production content into fully optimized, publish-ready
packages — maximizing discoverability, search performance, click-through
rate, localization readiness, and long-term audience growth. It runs
between the Render Engine and the Publishing Engine and never generates
scripts or video.

### What every content item receives

- **Title Optimization** — ten archetype titles (curiosity, authority,
  educational, question, shock, list, contrarian, story, breaking news,
  scientific), each ranked with a CTR prediction, SEO score, psychology
  score, and confidence. The refinement-stage title is scored alongside —
  never overwritten.
- **Description Engine** — long + short descriptions, per-platform
  variants (YouTube, TikTok, Instagram, Facebook, X, LinkedIn, Pinterest),
  call-to-action, first-comment and pinned-comment suggestions.
- **Keyword Engine** — primary, secondary, semantic, long-tail, entity,
  and question keywords with four-way search-intent classification
  (informational / navigational / commercial / transactional), fed by the
  auto-discovered SEO signal provider registry.
- **Hashtag Engine** — platform-specific ranked hashtags with estimated
  usefulness (reach × specificity, weighted per platform's discovery model)
  and per-platform tag limits.
- **Thumbnail Optimization** — consumes Visual Intelligence thumbnail
  concepts and re-evaluates each on curiosity, contrast, text density,
  facial emotion, object emphasis, and color psychology, returning ranked
  recommendations with click probability.
- **Global Localization (architecture)** — per-locale plans for 10
  country/language targets with keyword-replacement slots, regional
  hashtags, regional posting strategy, and readiness scores. Translation is
  intentionally NOT performed yet; the `LocalizationAdapter` interface lets
  human/MT/provider backends fill the slots later with zero contract
  changes.
- **Posting Strategy** — ranked publish windows per platform and country,
  scored from platform engagement tables, audience strength, competition,
  and trend velocity, each with a confidence score.
- **Optimization Report** — ten headline metrics: SEO score, CTR
  prediction, retention prediction, competition score, trend strength,
  evergreen score, localization readiness, publishing readiness,
  confidence, and the overall optimization score.

### Standardized PublishingPackage

Each optimized item yields a versioned **PublishingPackage v1.0**
(`PUBLISHING_PACKAGE_FIELDS` in `services/seo/models.py`) handed to the
Publishing Engine via the `publishing_packages` context key — the
ContentPackage `publishing_package` slot stays Agent 7's to write.

### Future providers (`providers/seo_sources/`)

Nothing is hardcoded: Google Search, Google Trends, YouTube Search, TikTok
Search, Reddit, News APIs, and Keyword APIs ship as deterministic
placeholder providers behind one `SeoSourceProvider` interface with an
auto-discovered registry (mirrors `providers/trend_sources/`). Live API
wiring is a per-file swap; proprietary providers drop in as new modules.

### Orchestrator integration

The `seo_optimization` engine graduated from its contract stub to a live
`ContractEngine`. `run_seo_stage(context)` optimizes every publish-ready
item (canonical `unified_packages` preferred, pipeline `ideas` fallback),
enriches each `seo_package` additively, and emits `seo_optimization_report`
+ `publishing_packages` — with zero items it still reports cleanly, never
crashing the pipeline. Docs: [`engines/seo/README.md`](engines/seo/README.md)
and [`DATA_CONTRACTS.md`](DATA_CONTRACTS.md) §6. Tests: 19 new in
`tests/test_seo_optimization.py` (371 total, all passing).

## Version 8.2 — Render & Video Production Engine (Agent 6)

The render stage is live. `engines/render/` converts a complete
ProductionPackage — structured script, scene breakdown, visual package,
audio package, captions, thumbnail plan, quality score — into a
render-ready **9:16 vertical short-form video package** (1080x1920 MP4 for
YouTube Shorts, TikTok, Instagram Reels, and Facebook Reels). No real MP4
is produced yet: this release ships the complete render architecture with
a **mock renderer**, ready for real providers to swap in.

### The render package (`render_package` v2.0)

Each idea gets a complete, JSON-safe render plan written to
`ContentPackage.render_package` (additive over the media-production seed):

- **Timeline** (`TimelineBuilder`) — contiguous, gap-free segments carrying
  scene_id, start/end/duration, narration/visual/caption/audio references,
  normalized transitions, motion effect, overlay text, and render status.
- **Scene render plans** (`SceneRenderer`) — per scene: visual asset type,
  image/video prompts, stock footage query, reserved user/avatar/reaction
  footage slots, camera movement, zoom/pan/ken-burns effect parameters,
  text overlays, caption placement, and sound cue timing.
- **Caption render plan** (`CaptionRenderer`) — word-by-word or sentence
  mode with a per-word timing map, bold emphasis words, safe-area
  positioning that clears every platform's UI chrome, per-platform vertical
  layouts, and four style presets.
- **Audio mix plan** (`AudioMixer`) — narration, music, SFX, and transition
  tracks with per-track levels, music ducking under narration, silence
  drops before payoff beats, and a platform-safe loudness placeholder
  (-14 LUFS / -1 dBTP).
- **Transitions + motion** (`TransitionPlanner` / `MotionPlanner`) — the
  Director's free-form language normalized to a closed vocabulary (cut,
  fade, push, zoom, whip pan, glitch, flash, documentary slow zoom,
  cinematic push-in, quick cut) as structured render instructions.
- **Validation** (`RenderValidator`) — pre-flight checks (visuals,
  narration, captions, audio, runtime, format, missing assets) returning
  SUCCESS / WARNING / FAILED / SKIPPED with diagnostics and a 0-100
  **production readiness score** — the number Publishing gates on.
- **Mock render** (`MockRenderer` + `RenderJob`) — simulates the full pass
  and returns render status, a reserved mock output path, duration,
  warnings, missing assets, and a step-by-step render log.

### Swappable providers (no paid APIs required)

Asset requests resolve through `AssetResolver` fulfillers — AI image, AI
video, stock footage, brand assets today (mock placeholders via
`providers/image_provider.py` / `video_provider.py` / `music_provider.py`);
user uploads, AI avatars, and AI reaction footage are reserved interfaces
that degrade to placeholders reported in `missing_assets`. Real backends
plug in via `set_image_provider()` / `set_video_provider()` /
`set_music_provider()` and `register_fulfiller()` — zero contract changes.

### Orchestrator integration

The `image` (asset resolution) and `video` (assembly) engines graduated
from planned stubs to live `ContractEngine`s, joined by the unified
`render` façade engine. `run_render_stage(context)` now renders every idea
in the context, mirrors results into `unified_packages` (status →
`rendered`), and returns a safe SKIPPED summary when there is nothing to
render — the render stage never crashes the pipeline. Docs:
[`engines/render/README.md`](engines/render/README.md) and
[`DATA_CONTRACTS.md`](DATA_CONTRACTS.md) §5. Tests: 34 new in
`tests/test_render_engine.py` (351 total, all passing).

## Version 8.1 — Shared Contracts for Agents 6-10

The integration foundation for the next five subsystems — Render & Video
Production (Agent 6), Publishing & Scheduler (Agent 7), SEO & Global Trend
Optimization (Agent 8), Analytics & Learning (Agent 9), and the Multi-Brand
Operating System (Agent 10) — is now in place. No future behavior is built
yet; the contracts, folders, stages, and rules are.

### Engine contracts

`engines/contracts.py` introduces `ContractEngine`: every future engine
declares `engine_id`, `name`, `version`, `input_contract`,
`output_contract`, `dependencies`, and `capabilities`, and gets
`validate_input()` / `validate_output()` (problem lists, never crashes),
`health_check()`, and `diagnostics()` for free. `FutureEngine` stubs for
`seo_optimization`, `scheduler`, and `brand_management` are registered now
(`engines/future_stubs.py`) and return `NOT_IMPLEMENTED` until their owners
arrive.

### Canonical ContentPackage

The `ProductionPackage` is now also exported as **`ContentPackage`** and
gained the Agents 6-10 fields (additive only): `brand_id`, `channel_id`,
`target_platforms`, `target_language`, `topic`, `keywords`,
`opportunity_score`, `virality_score`, `script_package`, `visual_package`,
`audio_package`, `render_package`, `publishing_package`,
`analytics_package`, `learning_metadata`, `status`, `diagnostics`.

### Landing zones + future stages

Ownership READMEs live in `engines/render/`, `engines/publishing/`,
`engines/seo/`, `engines/analytics/`, `engines/brands/`. The orchestrator
now knows six future stages — `render`, `seo`, `publish`, `analytics`,
`learning`, `brand_management` — each with a named runner; all skip cleanly
with diagnostics until their engines report ready.

### New documentation

[`OPERATING_SYSTEM.md`](OPERATING_SYSTEM.md) ·
[`PIPELINE_SPEC.md`](PIPELINE_SPEC.md) ·
[`DATA_CONTRACTS.md`](DATA_CONTRACTS.md) ·
[`ENGINE_REGISTRY.md`](ENGINE_REGISTRY.md) — plus updated merge-safety and
ownership rules in [`AGENT_WORKFLOW.md`](AGENT_WORKFLOW.md).

## Version 8.0 — Unified Orchestration Layer

Generational's engines are now coordinated by **one orchestration layer**
(`services/orchestrator/`) — the single interface that turns the collection
of engines into an autonomous AI Content Operating System. Full reference:
[`ORCHESTRATOR.md`](ORCHESTRATOR.md).

### One interface

`get_orchestrator().run_full_pipeline(command)` drives every subsystem —
trend discovery → opportunity ranking → research → psychology → script
generation → attention graph → visual intelligence → voice & audio →
refinement (ranking/critic/revision/citation/SEO/threats) → quality gate →
media production → packaging — and returns a `PipelineResult`. Per-stage
runners (`run_trend_stage`, `run_script_stage`, `run_visual_stage`,
`run_audio_stage`, `run_quality_stage`, plus future `run_render_stage` /
`run_publish_stage`) execute any stage on its own.

### Standardized ProductionPackage

Every run emits one `ProductionPackage` per idea: project_id, brand,
language, target_country, platforms, trend/competition/psychology/attention
scores, hook, script, scene breakdown, visual/voice/music assets, captions,
thumbnail plan, SEO package, quality score, publish_ready, and an analytics
placeholder. **Future engines only add fields** — unknown fields survive
round-trips via `extras`.

### Stage status + centralized logging

Every stage returns `SUCCESS` / `WARNING` / `FAILED` with start/finish
times, duration, confidence, and diagnostics; failures stop the pipeline
gracefully with partial results preserved. All lifecycle events flow
through the structured logger.

### Plugin architecture + autonomy prep

Stage order derives from `WORKFLOWS["intelligence"]` (one source of truth);
new engines plug in via `register_stage()` with zero orchestrator changes.
Future autonomous agents (Scheduler, Publisher, Analytics, Learning) attach
through `OrchestratorHook` — interfaces only, no scheduling built yet.

## Version 7.9 — Structured Cinematic Storytelling (Script Engine 2.0)

The Script Generation Engine is upgraded from a text generator into a
professional content writing system for high-retention short-form video.

### Section architecture (`services/scripts/sections.py`)

Every script is now built section-first. Each variant carries an ordered
list of annotated narrative sections — **Primary Hook (0–3s), Pattern
Interrupt, Curiosity Hook, Context, Escalation, Evidence / Explanation,
Emotional Peak, Resolution, Call To Action** — and every section includes
narration, estimated duration, emotional intensity, attention score,
visual intent, recommended B-roll type, and caption emphasis. The legacy
flat fields (`hook`, `curiosity_loop`, `core_story`, ...) are derived
views, so every downstream engine keeps working unchanged.

### Hook Engine (`services/scripts/hooks.py`)

Ten hook styles — Curiosity, Shock, Question, FOMO, Statistics,
Contrarian, Story, Mystery, Authority, Urgency — each write a candidate
opening line per idea. Candidates are scored 0–100 (with a psychology
bonus mapped from the idea's ViralScore dimensions, so a controversial
concept favors contrarian hooks while an emotional one favors story
hooks) and ranked. The best hook becomes the variant's Primary Hook; the
runners-up travel with the script as `alternate_hooks`.

### Retention model (`services/scripts/retention.py`)

Every variant estimates **viewer drop-off risk, engagement score,
retention score, rewatch probability, curiosity strength, and emotional
pacing** (label + intensity curve) from its section-level attention and
intensity curves, its text, and the idea's psychology. Predicted
retention feeds back into variant scoring.

### Director-ready scene breakdown

Every script converts into scenes: scene number, start/end time,
narration, visual description, camera style, motion recommendation,
caption text, sound cue, and transition recommendation — one scene per
section, timed contiguously to the estimated runtime.

### Structured output 2.0 (`services/scripts/structure.py`)

`structured_script` now returns the full production brief: title, hook,
alternate hooks, annotated sections, scene list, full narration,
estimated runtime, **emotion timeline**, **attention timeline**, visual
prompts, **voice instructions** (pace, tone, per-section delivery
direction), **caption plan**, retention model, CTA, platform format, and
locale.

### Multi-language ready

Every variant and structured script carries a `Locale`
(language / region / dialect, default `en-US`). A future Translation
Engine can rewrite narration per market without touching any engine
contract.

### Psychology integration

Generation consumes the candidate's ViralScore dimensions end to end:
hook ranking adapts to the idea's psychological strengths, section
intensity/attention curves shift with its emotional profile, and the
retention model blends first-3-second hook, curiosity gap, and
share/comment likelihood signals.

Platform coverage is unchanged (YouTube Shorts, TikTok, Instagram Reels,
Facebook Reels, X video, long-form YouTube), with per-platform pacing and
CTA styles.

## Version 7.8 — Cinematic AI Director (Visual Intelligence 2.0)

The Visual Intelligence Engine is upgraded from a visual planner into a
professional **AI Film Director**. It no longer just selects imagery — it
directs every second of visual attention, consuming structured output from
Trend Discovery, the Psychology Engine, the Script Engine (canonical
`structured_script`), and the Attention Graph (which now runs *before* it
in the pipeline).

### What every directed scene now carries

Scene number · duration · purpose · emotion · **attention level** ·
**visual style** · camera movement · **lens recommendation** · composition ·
lighting · color palette · **depth of field** · **motion recommendation** ·
transition · **recommended asset type** · **AI image prompt** ·
**AI video prompt** · **stock footage query** · overlay recommendations ·
**caption placement** · **sound effect timing** · B-roll suggestions ·
**thumbnail candidate flag** · 12-trigger visual psychology scores ·
**predicted viewer retention**.

### New visual psychology model (`services/visual/psychology.py`)

Twelve perceptual attention triggers: Curiosity, Pattern Interrupts,
Contrast, Novelty, Human Faces, Eye Contact, Motion, Scale, Speed,
Emotional Color Theory, Negative Space, Visual Hierarchy — plus
`predict_scene_retention()`, which blends visual pull, scene position,
length, and Attention Graph hook/rewatch signals into a per-scene
retention prediction and a package-level retention curve.

### Style presets (`services/visual/styles.py`)

15 built-in art directions — Documentary, Luxury, Minimal, Dark History,
Cyberpunk, Corporate, Nature, Science, Psychology, Finance, Horror,
Conspiracy, Modern Tech, Motivational, Cinematic. Each preset carries
palette, lighting bias, art style, grade, overlay/caption treatment, and
mood. Future engines register new styles via `register_style()` without
touching the engine; the operator can override per run via
`context["visual_style"]`.

### Professional shot list (`services/visual/shots.py`)

14 shot types with real cinematography metadata (lens, depth of field,
motion): Wide, Medium, Close-up, Extreme Close-up, Drone, POV, Tracking,
Orbit, Push-in, Pull-out, Static, Macro, Slow Motion, Hyperlapse. Every
script becomes a professional shot list; story beats rotate setups so no
two consecutive beats repeat a shot.

### Multi-source asset adapters (`services/visual/sources.py`)

No provider is ever hardcoded. Six registered adapters produce
provider-agnostic asset requests per scene: AI Image Generation, AI Video
Generation, Licensed Stock Footage, User Uploaded Assets, Brand Assets, and
a reserved (future) AI Avatar adapter. New sources register at runtime via
`register_source()`.

### Thumbnail system upgrade

Each of the five concepts now carries title overlay, emotion, color
strategy, focal subject, **eye direction**, contrast score, and **click
probability** (calibrated 1.5–14%).

### Render Package (`services/visual/render_prep.py`)

The Director does not render. Every Visual Production Package now includes
a versioned, machine-consumable **Render Package**: a contiguous clip
timeline with asset requests, transitions, overlays, captions, SFX cues,
and the retention curve — ready for the future Render Engine to execute
directly. Full contract documented in `VISUAL_PRODUCTION_PACKAGE.md`.

### Pipeline change

`script_generation → attention_graph → visual_intelligence → voice_audio`
— the Attention Graph moved ahead of Visual Intelligence so the Director
consumes its hook/retention scores when predicting per-scene retention.

## Version 7.7 — Behavioral Intelligence API

The Psychology & Virality Engine evolves from three separate scoring outputs
into one reusable **Behavioral Intelligence API**. Instead of every
downstream engine reaching into `candidate["psychology"]["curiosity_gap"]`,
`candidate["attention_graph"]["scores"]["shareability"]`, and
`candidate["threat_report"]["flagged_threats"]` separately, they can consume
one typed, documented report.

### `BehavioralIntelligenceReport` (`services/behavioral_intelligence/`)

A single dataclass with 13 behavioral scores plus a confidence score and a
capped list of recommendations:

`viral_score` · `attention_score` · `curiosity_score` · `emotional_intensity`
· `novelty_score` · `shareability_score` · `replay_probability` ·
`comment_probability` · `retention_prediction` · `hook_strength` ·
`identity_resonance` · `visual_interest_score` · `narrative_tension` ·
`confidence` · `recommendations`

```python
from services.behavioral_intelligence import build_report

report = build_report(candidate)
if report.hook_strength < 60:
    ...  # typed attribute access — no dict parsing required
```

Every field's meaning, source dimension(s), and fallback rule is documented
in `FIELD_DESCRIPTIONS` (`services/behavioral_intelligence/models.py`), and
`to_dict()` / `from_dict()` round-trip the report through the JSON-safe
workflow context.

### Graceful degradation, not a new pipeline stage

`build_report()` reads whatever of `psychology`, `attention_graph`, and
`threat_report` a candidate currently carries — it never requires all three.
`engines/psychology.py` attaches the report immediately after scoring
(the earliest point in the pipeline it can exist), and
`engines/attention_graph.py` / `engines/threat_detection.py` each refresh it
with richer data as their own scores land. This means Script Generation,
Visual Intelligence, and Voice & Audio — all three of which run *before* the
Attention Graph and Threat Detection — already see a fully-populated,
correctly-typed report the moment Psychology finishes; `confidence` simply
starts lower and climbs as more signal arrives later in the pipeline.

### Reference adapters (`services/behavioral_intelligence/adapters.py`)

Three small, tested functions show each named consumer reading the report
purely through typed attributes: `script_generation_guidance()`,
`visual_guidance()`, `audio_guidance()`. They are not wired into the live
engines (retrofitting calls into actively-developed modules was out of scope
for this API) — they are the documented, integration-tested seam those
engines call into when ready.

### Shared refactor

The weighted-blend formula (`clamp(sum(dimensions[k] * weight))`) that
`viral_score()`, `attention_score()`, and `overall_threat_score()` each
duplicated now lives once as `weighted_blend()` in `engines/heuristics.py`.

## Version 7.6 — Voice & Audio Engine

The sound brain of the pipeline. Every scripted candidate now receives a
complete **Audio Production Package** — the canonical sound plan that the
future audio renderers (TTS, music, sound design) and the video renderer
will consume. No audio files are generated yet; this is the planning
system that makes generation possible, exactly as the Visual Production
Package is for images and video.

### Audio Production Package (`services/audio/` + `engines/voice_audio.py`)

Each package contains:

- **Voice style** — a niche-matched narrator persona (tone, pitch,
  character) with an energy level derived from the storyboard's motion
  intensity and delivery notes tied to the emotional arc and the target
  platform's narration tone.
- **Narration plan** — per-scene delivery direction (urgent hook open,
  conspiratorial curiosity tease, slow-breathing payoff, warm CTA…), a
  target words-per-minute per scene (platform base modulated by scene
  purpose), scripted **pauses** (dramatic silence before the reveal,
  beats after questions and ellipses), and the **emphasis** words to
  stress (numbers first, then curiosity/surprise/emotion trigger words),
  plus a global pacing verdict and fitness score.
- **Sound effect recommendations** per scene — the storyboard's primary
  effect plus purpose-specific support layers (transition whooshes,
  tension drones, UI pops) with timing, intensity, and a mix note.
- **Background music direction** — style, BPM range (from average motion
  intensity), major/minor key from the emotional arc, a per-scene energy
  curve, named sections mapped to scene purposes (cold-open sting →
  driving groove → full swell → stripped-back outro), sidechain ducking
  guidance, and a seamless-loop note.
- **Audio mood** — the overall mood plus a scene-by-scene mood
  progression (the sonic complement of the visual `EMOTION_LOOKS`).
- **Scene-by-scene audio cues** — one merged cue per scene combining
  narration delivery, pauses, emphasis, SFX, music section/energy, mood,
  and a retention reminder, timed to the visual package's caption plan.
- **Retention pacing notes** — an audit of planned audio events (SFX +
  music changes + pauses) against the short-form ideal of a sonic change
  every 3-6 seconds, with concrete scene-anchored fixes: sound inside the
  first 0.5s, silence before the payoff, a mid-video texture reset, and a
  thinned mix under the CTA.
- One weighted **Overall Audio Score (0-100)** via `AUDIO_SCORE_WEIGHTS`
  (narration 30%, retention audio 20%, SFX coverage 20%, music dynamics
  20%, mood variety 10%).

### Pipeline integration

Runs immediately after Visual Intelligence — consuming its storyboard,
caption timings, motion intensities, and per-scene SFX/music hints — and
before every rendering stage (voice synthesis, image, video), so all
renderers execute one canonical sound plan:

```
... → Script Generation → Visual Intelligence
    → Voice & Audio (narration plan + voice style + SFX + music + cues + retention notes)
    → Attention Graph → Ranking → ... → Quality Gate → [voice → image → video]
```

Everything is deterministic — the full engine runs in Demo Mode with no
API key, and it degrades gracefully: ideas without a visual package get a
standalone storyboard planned on the fly. The `voice` render stub stays
planned; when real TTS lands, it will execute this package rather than
invent its own direction.

## Version 7.5 — Visual Intelligence Engine

The visual brain of the pipeline. Every scripted candidate now receives a
complete **Visual Production Package** — the canonical visual plan that
every downstream renderer (voice, audio, image, video) will consume. No
final videos are generated yet; this is the planning system that makes
generation possible.

### Visual Production Package (`services/visual/` + `engines/visual_intelligence.py`)

Each package contains:

- **Scene-by-scene storyboard** — hook, pattern interrupt, curiosity loop,
  story beats sized to runtime (~one visual change every 7s), payoff, CTA.
  Every scene carries the full visual grammar: purpose, emotion, length,
  camera angle + motion, shot composition, subject placement, lighting,
  environment, color palette, transitions in/out, motion intensity, zoom,
  background, overlay, text overlay, caption timing, sound effect, music
  style, and B-roll.
- **12-dimension visual psychology scores per scene** — Curiosity ·
  Mystery · Wonder · Fear · Beauty · Novelty · Scale · Contrast · Motion ·
  Satisfaction · Humor · Identity — blended into a per-scene Visual Score
  via `VISUAL_SCORE_WEIGHTS` (deterministic word-bank + structure analysis,
  same approach as the psychology/threat engines).
- **AI image prompts** for Midjourney, Flux, Stable Diffusion, DALL-E, and
  OpenAI Images — each carrying lighting, composition, lens, mood, art
  style, color palette, quality tags, and aspect ratio, formatted in each
  model's dialect (e.g. `--ar 9:16 --style raw --v 6` for Midjourney,
  negative prompts for Stable Diffusion).
- **AI video prompts** for Runway, Veo, Pika, Luma, Kling, and Sora
  (future-ready) — each describing the scene, camera movement, character
  actions, lighting, physics, mood, and duration.
- **5 scored thumbnail concepts** — Shock Face Close-Up, Mystery Object
  Macro, Before/After Split, Extreme Scale Contrast, Bold Text Tease —
  each scored on curiosity, readability, contrast, facial focus, object
  focus, color, and emotion, with an **expected CTR %**.
- **Hook Visualizer** — the strongest five-frame first-3-second sequence
  (abrupt motion → novel detail → curiosity gap → direct address → open
  loop) plus a plain-English scroll-stop rationale.
- **Caption plan, visual pacing report, camera plan, transitions, and
  motion report** — cut rhythm vs. the 3-8s retention ideal, camera
  variety score, and a per-scene motion intensity curve.
- One weighted **Overall Visual Score (0-100)** via
  `PACKAGE_SCORE_WEIGHTS` (scene craft 35%, hook 25%, thumbnail 20%,
  pacing 12%, camera variety 8%).

### Pipeline integration

Runs immediately after Script Generation and before the Attention Graph,
so ranking can weigh visual craft and every asset planner downstream shares
one visual source of truth:

```
... → Psychology → Script Generation
    → Visual Intelligence (storyboard + prompts + thumbnails + Visual Score)
    → Attention Graph → Ranking → ... → Quality Gate
```

Everything is deterministic — the full engine runs in Demo Mode with no API
key, and adding a new AI image/video model is one formatter function in
`services/visual/prompts.py`. Every idea card gets a compact "🎥 Visual
Production Package" expander with the storyboard, thumbnail scores, and
hook sequence.

## Version 7.4 — Threat Intelligence (Psychology Threat Detection)

Phase 3 of the attention-engineering stack. Every fully-packaged idea now
gets screened for **10 production failure modes** — the things that quietly
kill watch time, trust, or platform standing even when the underlying
psychology looks strong.

### 10 threats detected (`engines/threat_detection.py`)

Clickbait Without Payoff · Low Dopamine Pacing · Weak Hooks · Viewer
Fatigue · Thumbnail Mismatch · Predictable Scripting · Retention Cliff
Risk · Platform Policy Risk · Manipulative Language · Repetitive Content.

Each is scored 0-100 (higher = riskier) from the same deterministic
text-feature analysis used throughout the pipeline, reusing the already-
computed Psychology dimensions, script/thumbnail package, and retention
checkpoints — plus new dedicated word banks in `engines/heuristics.py` for
policy-risk and manipulative-pressure language. **Repetitive Content**
additionally compares an idea against every other idea in the same batch
to catch near-duplicate hooks/topics.

### Threat Level, Confidence, and fixes

The 10 scores blend into one weighted **Threat Score** (0-100) via
`THREAT_WEIGHTS`, mapped to a **Threat Level** (`Low` / `Medium` / `High`)
plus a **Confidence %** reflecting how much of the packaged idea (script,
thumbnail concept, retention checkpoints, CTA) was available to analyze.
Every idea card gets a compact "🚨 Threat Report" expander listing any
flagged threats with a concrete, dimension-specific fix — recommendations
are always available for all 10 dimensions, not just the flagged ones.

### Pipeline integration

Runs after SEO packaging (so the thumbnail concept and full script exist)
and before the final Quality Gate — a purely additive diagnostic layer that
doesn't change the publish-gate math:

```
... → Ranking → Script → Critic → Revision → Citation → SEO
    → Threat Detection (10 failure modes → Threat Level + Confidence + fixes)
    → Quality Gate
```

## Version 7.3 — Attention Intelligence (Attention Graph)

Phase 2 of the attention-engineering stack. Every idea now gets an
**Attention Graph** — a 12-dimension radar-chart-ready score, a single
weighted 0-100 Attention Score, and a concrete recommendation for raising
every dimension (not just the weak ones).

### 12 dimensions (`engines/attention_graph.py`)

First 3-Second Hook · Curiosity Gap · Dopenness · Emotional Intensity ·
Story Tension · Surprise · Visual Novelty · Shareability · Rewatch
Probability · Comment Likelihood · Identity Signaling · Tribal Engagement.

Nine of the twelve reuse the already-tested Phase 1 psychology dimension
scorer so the two phases stay consistent. Three are new to this phase:

- **Dopenness** — how quickly and openly the concept opens an anticipatory
  dopamine/reward loop for a broad, low-jargon audience
- **Story Tension** — turning-point language and setup/twist structure
- **Visual Novelty** — concrete, filmable transformation and reveal cues

### Attention Score + radar chart

The 12 dimensions blend into one weighted **Attention Score** (0-100) via
`ATTENTION_GRAPH_WEIGHTS`. Every idea card in the Ideas tab gets a compact
"🕸️ Attention Graph" expander with a Plotly radar chart of all 12
dimensions (falls back to a plain score list if `plotly` isn't installed)
plus a recommendation for increasing every score, sorted weakest-first.

### Pipeline integration

```
Trend Discovery → Opportunity Ranking → Research → Ideation
    → Psychology & Virality (18 dimensions → ViralScore)
    → Script Generation (multi-variant, multi-style, scored)
    → Attention Graph (12 dimensions → radar chart + recommendations)
    → Ranking → Critic → Revision → Citation → SEO → Quality Gate
```

## Version 7.2 — Script Generation Engine

v7.2 rebuilds scriptwriting into a modular **Script Generation Engine** that
runs immediately after the Psychology & Virality Engine. Instead of one
script per winning idea, every psychology-scored candidate receives multiple
stylistically distinct, platform-aware script variants — each scored 0-100 —
and the best telling wins before ranking even happens.

### Supported platforms (`services/scripts/platforms.py`)

YouTube Shorts · TikTok · Instagram Reels · Facebook Reels · X (Twitter)
video · Long-form YouTube. Each platform is a data-driven `PlatformSpec`
(runtime window, narration pacing, tone, hook window, CTA style) — adding or
tuning a platform never touches generation or scoring logic.

### Every script is a complete storytelling package

Each variant carries all thirteen components:

Hook · Pattern Interrupt · Curiosity Loop · Core Story · Emotional
Progression · Retention Checkpoints (re-hooks at the 25/50/75% drop-off
points) · Call To Action · SEO Keywords · Suggested B-roll · Suggested AI
Visual Prompts · Suggested Sound Effects · Suggested Background Music Style ·
Estimated Runtime.

### Multiple variants, scored and ranked

Four narrative archetypes compete per idea — **Authority Reveal**, **Story
First**, **Myth Bust**, **Countdown Payoff** — plus an **AI Enhanced**
variant for the strongest candidates when an OpenAI key is present. Every
variant is scored deterministically across six weighted factors (hook power,
retention engineering, emotional arc, story substance, platform fit, CTA
strength — `VARIANT_SCORE_WEIGHTS` in `services/scripts/scorer.py`), and the
winner becomes the candidate's script.

### Pipeline integration

The new `script_generation` stage runs **immediately after Psychology**, so
the Ranking engine now weighs script quality (20%) alongside psychology
(50%) and trend opportunity (30%) when selecting what gets produced:

```
Trend Discovery → Opportunity Ranking → Research → Ideation
    → Psychology & Virality (18 dimensions → ViralScore)
    → Script Generation (multi-variant, multi-style, scored)
    → Ranking → Critic → Revision → Citation → SEO → Quality Gate
```

The previous `script` stage remains as a safety-net fallback for custom
workflows — it never overwrites generated variants. As with every stage,
Demo Mode runs the entire engine deterministically without an API key.

## Version 7.1 — Psychology & Virality Engine

v7.1 turns the psychology stage into a full **attention-engineering system**.
Every candidate idea is no longer just "scored" — it is measured against 18
behavioral-science dimensions of what makes short-form content get watched,
rewatched, commented on, and shared, and it receives a plain-English report
explaining exactly why.

### 18 psychology dimensions (`engines/psychology.py`)

Curiosity Gap · Emotional Intensity · Surprise · Novelty · Fear · Humor ·
Satisfaction · Retention Potential · Replay Value · Comment Likelihood ·
Share Likelihood · Controversy (bounded by platform safety) · Visual Hook
Strength · First 3-Second Hook · Dopamine Curve · Information Density ·
Audience Identity · Community Appeal.

Each dimension is scored 0-100 with deterministic text-feature analysis
(word-bank hits, punctuation, structure, digits, hook length) — fast, free,
reproducible with or without an API key, and fully unit-tested.

### ViralScore (0-100)

The 18 dimensions blend into one weighted **ViralScore** (`VIRAL_SCORE_WEIGHTS`
in `engines/psychology.py`) — data, not code, ready for the future Learning
Engine to tune from real performance results.

### Psychology Report

Every candidate gets a `psychology_report`: a viral tier (e.g. *Strong Viral
Potential*), its top 3 strengths, its 3 weakest levers, a per-dimension note
explaining why it scored that way, and a one-line plain-English summary. The
Ideas tab shows it as a compact expander on every idea card — no new pages.

### Pipeline integration

The Psychology engine runs immediately after Ideation (which itself runs
after Trend Discovery) and before Ranking and Script Generation, so nothing
is scripted, produced, or published without first passing through the
attention model:

```
Trend Discovery → Opportunity Ranking → Research → Ideation
    → Psychology & Virality (18 dimensions → ViralScore + report)
    → Ranking → Script → Critic → Revision → Citation → SEO → Quality Gate
```

The Quality Gate now also computes a dedicated **virality** score (share,
comment, identity, community, bounded controversy) alongside publish, SEO,
psychology, retention, and CTR — so the publish gate rewards concepts built
to spread, not just to be watched once.

## Version 7.0 — Trend Discovery Engine

v7.0 makes Trend Discovery the **front door** of the operating system. Instead
of the user guessing what content to make, the system discovers opportunities
automatically before any research or generation begins.

### Trend provider layer (`providers/trend_sources/`)

Plug-and-play providers behind one interface (`TrendSourceProvider`):
Google Trends, YouTube Trending, TikTok Trends, Reddit Rising, RSS Feeds,
News APIs, and Keyword APIs (all deterministic placeholders today, live API
wiring is a per-file swap). The registry **auto-discovers** providers — adding
a source means dropping a single module into the package. No registration code.

### Universal Trend Model (`services/trends/models.py`)

Every provider normalizes into one `Trend` dataclass: topic, keywords,
growth %, search volume, velocity, competition, freshness, category, country,
language, platform, source, timestamp, and confidence. Downstream systems
consume only this model.

### Opportunity Scoring (`services/trends/scorer.py`)

Every trend receives a 0-100 **Opportunity Score** blended from eleven factors:
search demand, growth velocity, competition, historical performance, content
difficulty, monetization potential, virality potential, evergreen potential,
freshness, audience size, and international potential. Factor weights are data,
ready for the future Learning Engine to tune.

### Pipeline integration

Two new stages open the intelligence pipeline — `trend_discovery` and
`opportunity_ranking` — so the flow is now:

```
Trend Discovery → Opportunity Ranking → Research → Ideation → Psychology
    → Ranking → Script → Critic → Revision → Citation → SEO → Quality Gate
```

Only the top 5 opportunities move forward; their keywords feed the ideation
prompt so generated concepts ride real trend signals.

### Trend Dashboard

The Ideas tab now shows a compact Trend Discovery panel (no redesign): top
opportunity score, average growth, velocity, trending countries / platforms /
languages, discovery timestamp, and a ranked list of the top opportunities.

## Version 6.0 — Real Research + Citation Engine

v6.0 turns Generational into a **source-backed research system** for autonomous
faceless short-form content. Every idea and script is grounded in a structured
**Research Brief** with full citation traceability.

### Live research connectors

| Provider | Status |
|---|---|
| Wikipedia | Live (MediaWiki API) |
| PubMed | Live (NCBI E-utilities) |
| arXiv | Live (Atom API) |
| Crossref | Live (REST API) |
| Google Trends, YouTube Trends, Reddit, News, TikTok | Placeholders (demo data) |

All live connectors fall back to demo data if APIs fail — the app never crashes.

### Research Brief

Every result stores: title, source name, URL, date, summary, credibility score,
relevance score, confidence score, and topic tags.

### Citation Engine (new pipeline stage)

After revision, every script receives:
- Supporting sources
- Claim confidence score
- Unsupported claim warnings
- Fact-check notes
- Citation list

### Multi-factor Quality Gate

Content is **not publishable** unless ALL pass:
- Publish score ≥ threshold
- Research confidence ≥ threshold
- Unsupported claims ≤ max allowed
- Claim confidence ≥ minimum (when citations required)

### Settings → Research (v6)

Research depth · Source confidence threshold · Science/medical strict mode ·
Maximum sources · Citation requirement · Research confidence gate ·
Unsupported claims limit · Claim confidence minimum · Quality gate threshold

## Version 5.0 — Knowledge Engine & Research Platform

v5.0 transforms Generational from an AI content generator into a **research-first
content platform**. Every video now begins with multi-source research — ideas are
grounded in vetted documents, not model imagination alone.

### Research flow

```
Run Command
    │
    ▼
Parse Intent (topic, niche, audience, intent, educational vs entertainment)
    │
    ▼
Query Enabled Providers (Wikipedia, PubMed, arXiv, Crossref, News, Trends, YouTube, Reddit)
    │
    ▼
Normalize → Score → Filter weak sources
    │
    ▼
Generate Research Summary (facts, stats, myths, trends, takeaways)
    │
    ▼
Intelligence Pipeline (ideas grounded in research)
    │
    ▼
Media Production Pipeline (for publish-ready scripts)
```

### Knowledge Engine (`services/research/`)

| Module | Role |
|---|---|
| `manager.py` | Orchestrates the full research flow |
| `models.py` | `ResearchDocument`, `ResearchIntent`, `ResearchSummary`, `ResearchSettings` |
| `cache.py` | Topic-level cache with TTL — reuse research, refresh stale sources |
| `scorer.py` | Authority, freshness, popularity, scientific reliability, citations, relevance |
| `summarizer.py` | Executive summary, facts, stats, contrarian ideas, myths, Q&A, trends |

### Research source providers (`providers/`)

Every provider exposes the same interface: `search(topic) → list[ResearchDocument]`.

The UI never knows which provider supplied the data. Adding a provider = drop a
new file in `providers/` and register it in the factory.

Demo providers return deterministic synthetic data today; swap internals for real
API calls without changing pipeline logic.

### Traceability

Every generated script stores `references`: sources used, facts cited, and URLs
for future publishing attribution.

### Settings → Research

- Enable/disable individual providers
- Cache expiration (hours)
- Maximum sources
- Minimum confidence threshold

### Fail-safe

If every provider fails, the system falls back to the heuristic demo pipeline —
never crashes.

## Version 4.0 — Autonomous Media Production Engine

v4.0 adds a **Media Production Pipeline** that runs automatically after the
Intelligence Pipeline completes. Every script that passes the quality gate
becomes a complete, production-ready media package — without touching the
intelligence workflow or redesigning the UI.

**Intelligence Pipeline** (unchanged structure, +Citation): Research → Ideas → Psychology → Ranking → Scripts → Critic → Revision → **Citation** → SEO → Quality Gate

**Media Production Pipeline** (new): Scene Planning → Narration → Visual Planning → Asset Management → Subtitles → Timeline → Render Package → Publishing Queue

Each approved script automatically receives:
- **Structured scenes** (duration, narration, visual description, emotion, camera, transitions, on-screen text, keywords, timing)
- **Narration tracks** via the Voice Provider abstraction (AI, recorded, or clone-ready)
- **Visual prompts** for future image/video providers (subject, environment, mood, lighting, cinematic direction)
- **Registered assets** (narration, visuals, thumbnails, music) in the Asset Manager
- **Subtitle tracks** with sentence + word-level timing and SRT output
- **Production timeline** (narration, visual, subtitle, music, transitions)
- **Render Package** — every asset bundled for a future renderer (no rendering yet)
- **Publishing queue entry** — ready for auto-posting when connected

The **Production Dashboard** (compact panel in the Ideas tab) shows all 18
pipeline stages with status: Waiting, Running, Completed, Retrying, Failed.

### Voice architecture
Three narration modes via `providers/voice/`:
1. **AI Voice** — Demo provider today; swap for ElevenLabs/OpenAI TTS without engine changes
2. **User Recorded Voice** — profiles + recordings stored under `data/voice_recordings/`
3. **Voice Clone** — architecture stub only; plug in a clone provider later

Voice profiles support styles (Documentary, Educational, Storytelling, Science, Finance, High Energy, Calm) and settings (speed, energy, emotion, pitch, pause style, pronunciation overrides). Configure mode in **Settings → Voice**.

### Provider system (`providers/`)
Swappable interfaces — no business logic depends on a single vendor:
LLM, Research, SEO, Voice, Image, Video, Music, Publishing, Analytics, Trend.

## Version 2.0 — Intelligence Pipeline

v2.0 replaces single-shot generation with a 9-stage AI reasoning pipeline.
Every command now flows through:

1. **Research** — Knowledge Engine gathers multi-source documents, scores them, and produces a structured research summary
2. **Ideation** — 20 candidate concepts (title + hook + angle)
3. **Psychology** — every candidate scored for curiosity, emotional impact, surprise, authority, retention potential, and shareability
4. **Ranking** — weighted scoring; only the top concepts advance
5. **Script** — scripts written only for the winners
6. **Internal Critic** — flags weak hooks, repetition, low retention, boring phrasing, unsupported claims, poor pacing
7. **Revision** — automatically rewrites the flagged sections and re-scores
8. **SEO** — optimized title, hashtags, keywords, description, thumbnail concept
9. **Final Quality** — per-video Opportunity, SEO, Psychology, Retention, CTR, and overall Publish scores

A configurable quality gate (Settings → Quality Gate) holds back anything
scoring below the publish threshold — it will never be auto-published.
With an OpenAI key, the generative stages (research, ideation, scripts, SEO)
use the model; without one, deterministic heuristics keep the full pipeline
running in Demo Mode. Scoring stages are deterministic in every mode, so
results are reproducible and testable.

## Version 1.1 — Autonomous OS Foundation

v1.1 keeps the interface identical but rebuilds the internals for scale: a
central **job queue**, a **plugin engine registry** (9 pipeline engines
registered, ideation live), a **workflow engine** that executes configurable
pipelines, a **channel manager** for multiple brands/accounts, a
**knowledge base** that remembers every hook/title/script generated,
**structured logging + diagnostics**, and a **unit-test suite** covering
every core service. See [Architecture](#architecture).

## Version 1.0 — AI Command Center

v1.0 upgrades the original idea generator into a full AI Command Center workspace:

- **Real AI generation** — when an `OPENAI_API_KEY` is available, Generational calls OpenAI to generate real viral hooks, titles, 15-30s scripts, CTAs, hashtags, and thumbnail concepts. Without a key, it automatically falls back to **Demo Mode** with clean placeholder content — the app never crashes.
- **Workspace tabs** — Ideas, Scripts, Projects, Publishing, Analytics, and Settings.
- **Project saving** — Create, Save, Open, and Delete projects, persisted locally as JSON files under `data/projects/`.
- **AI sidebar** — always-visible API status, active model, app version, ideas generated, projects saved, and token usage.
- **Polished dark UI** — custom theme, cards, spacing, loading spinners, and success/error notifications.

## Features

### 💡 Ideas
Type a natural language command (e.g. *"Create 10 psychology shorts about procrastination"* or *"Create 5 science shorts about black holes"*), or click an example to auto-fill the command box. Running the command executes the full intelligence pipeline and shows:
- Detected niche, videos requested, audience, search intent, and trend strength
- The research summary and content goal
- The top-ranked ideas (of 20 candidates), each with hook, script, CTA, hashtags, keywords, description, thumbnail concept, critic notes, all six quality scores, and a **production package** (scenes, duration, assets, queue status) for publish-ready scripts
- The **Production Dashboard** showing all intelligence + media stages
- The publish gate verdict per video, and the remaining render steps: Voice → Image → Video → Publish

### 📝 Scripts
A focused, copy-friendly view of the full scripts for the current batch of ideas.

### 📁 Projects
Create, save, open, and delete projects. Everything is stored as local JSON — no database required for this MVP.

### 📤 Publishing
Placeholder platform connection cards (YouTube Shorts, TikTok, Instagram Reels, Facebook Reels, X, YouTube Long-form) plus a roadmap for Auto Posting, AI Voice Generation, and AI Video Creation.

### 📊 Analytics
Session-level placeholder metrics and a roadmap for the full Analytics Dashboard and SEO Optimizer.

### ⚙️ Settings
- View API key status, or paste a session-only key override (never written to disk)
- Choose the OpenAI model (`gpt-4o-mini`, `gpt-4o`, `gpt-3.5-turbo`)
- **Quality Gate** — minimum publish score threshold
- **Voice** — narration mode (AI / Recorded / Clone) and default voice style
- **Research** — enable/disable providers, cache TTL, max sources, confidence threshold
- System diagnostics across all services
- Reset session stats

## Getting Started

### 1. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure your OpenAI API key (optional)

Copy `.env.example` to `.env` and add your key to enable real AI generation:

```bash
cp .env.example .env
```

```
OPENAI_API_KEY=sk-...
```

Without a key, Generational runs fully in **Demo Mode** with placeholder content — no crashes, no setup required. You can also paste a key directly in the **Settings** tab for the current session only.

### 4. Run the app

```bash
streamlit run app.py
```

## Tech Stack

- [Streamlit](https://streamlit.io/) — UI framework
- [OpenAI](https://openai.com/) — real AI content generation
- [python-dotenv](https://pypi.org/project/python-dotenv/) — environment variable management
- [Plotly](https://plotly.com/python/) — Attention Graph radar chart (optional; falls back to a plain score list if absent)

## Architecture

Generational v5.0 is an autonomous content operating system. The Streamlit UI
is a thin shell over five layers:

```
        UI (Streamlit tabs + sidebar)
                    │
        services/  (research, ideation, production, assets, voice profiles, channels, knowledge, behavioral intelligence)
                    │
   Job Queue ──► Workflow Manager ──► Engine Registry (23 live plugins)
                    │
        providers/ (research sources, LLM, Voice, Image, Video, Music, Publishing, Analytics, Trend)
                    │
        core/  (models, storage, logging, diagnostics, production_models)
```

### Knowledge Engine (`services/research/`)
Runs as stage 1 of every command. Parses intent, queries all enabled research
providers, normalizes results into `ResearchDocument` objects, scores and
filters weak sources, generates a structured summary, caches by topic, and
stores research in project Knowledge folders. Downstream ideation uses facts
from the summary — not raw model imagination.

### How to add a research provider

1. Create `providers/my_source.py` implementing `ResearchSourceProvider.search(topic)`
2. Return `list[ResearchDocument]` with normalized fields
3. Register in `providers/__init__.py` → `_load_research_sources()`
4. Add the key to `RESEARCH_PROVIDERS` in `core/constants.py`

No pipeline or UI changes required.

### Media Production Pipeline (`services/production.py`)
Runs **after** intelligence completes. Only `publishable` scripts enter the
`media_production` workflow. Each engine accepts structured input and returns
structured output — no engine calls another directly. Results attach to idea
cards and persist in projects.

### Production data models (`core/production_models.py`)
Strongly typed structures: **Scene**, **VisualPrompt**, **NarrationTrack**,
**Asset**, **SubtitleTrack**, **Timeline**, **RenderPackage**,
**ProductionPackage**, **VoiceProfile**, **StageStatus**.

### Asset Manager (`services/assets.py`)
Tracks generated images, videos, uploaded/stock footage, narration, music,
sound effects, subtitles, and thumbnails. Assets register during production
and are reusable across projects under `data/assets/`.

### Voice profiles (`services/voice_profiles.py`)
Create profiles, attach to projects, store recording metadata. Recordings
live under `data/voice_recordings/`. Clone mode is wired but not implemented.

### Engine plugins (`engines/`)
**25 live engines** across two pipelines. Intelligence (17): Trend Discovery,
Opportunity Ranking, Research, Ideation, Psychology, Script Generation,
Attention Graph, Visual Intelligence, Voice & Audio, Ranking, Script
(fallback), Critic, Revision, Citation, SEO, Threat Detection, Quality.
Production (8): Scene
Planning, Narration, Visual Planning, Asset Manager, Subtitle, Timeline,
Render Package, Publishing Queue. Future render engines (Voice/Image/Video
generation) remain as planned stubs.

The **Behavioral Intelligence API** (`services/behavioral_intelligence/`,
v7.7) is not a 26th pipeline stage — it's a reusable service Psychology,
the Attention Graph, and Threat Detection each call into, so it has no
`WORKFLOWS` entry of its own.

### Workflow Engine (`core/workflows.py`)
Pipelines are data, not code: a workflow is an ordered list of engine keys
(see `WORKFLOWS`, e.g. `full_content`). The engine executes each step,
merges outputs into the context, skips engines that aren't ready, and
records per-step status/duration. Workflows run as jobs via the queue.

### Channel Manager (`services/channels.py`)
Multi-brand/account support: each channel stores its name, niche, brand
voice, platform targets, posting schedule, API credentials, status
(active/paused/archived), and performance metrics. Persisted under
`data/channels/`. Backend-only for now — a Channels UI comes later.

### Knowledge Base (`services/knowledge.py`)
The system's memory: winning hooks, titles, scripts, thumbnail concepts,
SEO keywords, publishing history, and performance data, stored per category
under `data/knowledge/`. The ideation engine writes every generation into
it (tagged with its source); the future Learning engine will mine it to
improve prompts and strategy.

### Logging & diagnostics
All services log structured `event | key=value` lines (console +
`data/logs/generational.log`) via `core/log.py`. `core/diagnostics.py` runs
health checks across the AI provider, storage, engines, job queue, channels,
and knowledge base — visible in **Settings → System Diagnostics**.

### Other extension points
- **New LLM / Voice / Image provider**: implement the interface in
  `providers/` and register in the matching factory.
- **New production stage**: add an engine module, register in `engines/__init__.py`,
  append its key to `WORKFLOWS["media_production"]`.
- **New storage backend**: implement `core/storage/base.py`'s `ProjectStore`.
- **Real renderer**: implement `MockRenderer.render()`'s signature (ffmpeg /
  cloud) and register asset fulfillers via
  `engines.render.assets.register_fulfiller()` — see `engines/render/README.md`.

## Testing

Every core service has unit tests under `tests/`:

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Tests run against isolated temp directories and never touch your `data/`
folder.

## Project Structure

```
generational/
├── app.py                    # Main entry point — wires sidebar + tabs together
├── requirements.txt          # Runtime dependencies
├── requirements-dev.txt      # Dev dependencies (pytest)
├── .env.example              # Template for your OpenAI API key
├── .streamlit/
│   └── config.toml           # Dark theme configuration
├── core/                     # Foundations (no UI code)
│   ├── constants.py          # App config: niches, models, example commands
│   ├── models.py             # Canonical result/project data shapes
│   ├── parsing.py            # Command parsing (niche/count/subject detection)
│   ├── state.py              # Streamlit session state helpers
│   ├── log.py                # Structured logging (console + data/logs/)
│   ├── diagnostics.py        # Health checks across all services
│   ├── jobs.py               # Central job queue (async task management)
│   ├── workflows.py          # Workflow engine (configurable pipelines)
│   ├── production_models.py  # Scene, Timeline, RenderPackage, VoiceProfile, ...
│   ├── ai/                   # LLM provider (implements providers/llm interface)
│   └── storage/              # Storage abstraction
├── providers/                # Swappable provider interfaces
│   ├── wikipedia.py, pubmed.py, arxiv.py, crossref.py  # Research sources
│   ├── news.py, trends.py, youtube.py, reddit.py
│   ├── research_source.py    # Unified search() interface
│   ├── trend_sources/        # Trend providers (auto-discovered registry)
│   ├── seo_sources/          # v8.3 SEO signal providers (auto-discovered registry)
│   ├── llm.py, voice/, image_provider.py, video_provider.py, music_provider.py
│   └── publishing_provider.py, analytics_provider.py, trend_provider.py
├── engines/                  # Engine plugins (intelligence + production)
│   ├── trend_discovery.py, opportunity_ranking.py  # v7.0 front door
│   ├── script_generation.py  # v7.2 multi-variant Script Generation Engine
│   ├── attention_graph.py    # v7.3 12-dimension Attention Graph
│   ├── threat_detection.py   # v7.4 10-threat Psychology Threat Detection
│   ├── visual_intelligence.py # v7.5 Visual Production Package planner
│   ├── voice_audio.py        # v7.6 Audio Production Package planner
│   ├── research … quality.py # Intelligence pipeline (17 live)
│   ├── scene_planning … publishing_queue.py  # Media production (8 live)
│   ├── render/               # v8.2 Render & Video Production Engine (Agent 6)
│   ├── image.py, video.py    # v8.2 live render stage engines (assets + assembly)
│   ├── seo_optimization.py   # v8.3 Global Content Optimization Engine (Agent 8)
│   ├── analytics.py, learning.py  # v9.2 Analytics & Continuous Learning (Agent 9)
│   └── voice.py              # future stub
├── services/
│   ├── research/             # Knowledge Engine (manager, cache, scorer, summarizer)
│   ├── trends/               # Trend Discovery (models, scorer, manager)
│   ├── scripts/              # Script Generation (models, sections, hooks, retention, platforms, generator, scorer, structure)
│   ├── visual/               # Visual Intelligence (models, psychology, scenes, prompts, thumbnails, hooks, package)
│   ├── audio/                # Voice & Audio (models, voice, narration, sfx, music, retention, package)
│   ├── seo/                  # v8.3 Global Content Optimization (titles, keywords, hashtags, descriptions, thumbnails, localization, windows, report, package)
│   ├── analytics/            # v9.2 performance collection (models, store, collector, integration)
│   ├── learning/             # v9.2 continuous learning (patterns, recommendations, experiments, memory, reports, loop)
│   ├── behavioral_intelligence/ # v7.7 unified report API (models, builder, adapters)
│   ├── ideation.py           # Intelligence pipeline orchestrator
│   ├── production.py         # Media production orchestrator
│   ├── assets.py             # Asset Manager + Publishing Queue
│   ├── voice_profiles.py     # Voice profile + recording metadata
│   ├── channels.py, knowledge.py, pipeline.py
├── ui/                       # Presentation layer (Streamlit only)
│   ├── styles.py, notify.py, components.py, sidebar.py
│   └── tabs/                 # ideas, scripts, projects, publishing, analytics, settings
├── tests/                    # Unit tests (intelligence + production + providers)
└── data/
    ├── projects/, channels/, knowledge/, logs/
    ├── assets/               # Asset registry index
    ├── voice_profiles/, voice_recordings/
    ├── research_cache/       # Topic-level research cache
    ├── publishing_queue/     # Queued render packages
    └── analytics/            # v9.2 analytics records, memory, experiments, reports
```

## Roadmap

- 📡 Live trend APIs (Google Trends, YouTube Data, TikTok, Reddit) behind the trend provider interface
- 🎬 Real video/image generation + encoding behind the Render Engine's provider seams (architecture + mock render shipped in v8.2)
- 🎙️ Real TTS providers (ElevenLabs, OpenAI) behind VoiceProvider
- 🧬 Voice cloning provider
- 📤 Auto Posting from publishing queue
- 📊 Live platform analytics APIs (YouTube Analytics, TikTok Business, Meta Insights) behind the `AnalyticsProvider` interface (architecture + learning loop shipped in v9.2)
