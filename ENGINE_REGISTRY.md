# Generational — Engine Registry (v9.6)

How engines register, what exists today, and which keys are reserved for
future agents. The registry (`engines/registry.py`) is the single source of
truth at runtime; this document is its map. Agent roster: `AGENT_REGISTRY.md`;
dependency view: `SYSTEM_DEPENDENCY_MAP.md`.

## Registration model

- Importing `engines` registers every engine listed in
  `engines/__init__.py` (append-only; Agent 1 review).
- Each engine has a unique `key` — one module per key, registered once.
  Re-registering a key replaces the engine (how stubs graduate to live).
- Classic engines subclass `Engine` (`engines/base.py`). New engines
  subclass `ContractEngine` (`engines/contracts.py`) and additionally
  declare `version`, `input_contract`, `output_contract`, `dependencies`,
  `capabilities`, plus `validate_input/validate_output/health_check/
  diagnostics`.
- `is_ready()` gates execution: not-ready engines are skipped by the
  workflow with diagnostics — never a crash.
- **Directive #1:** the registry exists for registration and orchestrator
  discovery. Engines never call `get_engine()` to fetch and run another
  engine — shared logic belongs in `engines/analysis.py` /
  `engines/heuristics.py`, and coordination belongs to the orchestrator.
  Enforced by `tests/test_architecture.py`.

## Live engines (intelligence)

`trend_discovery` · `opportunity_ranking` · `trend_forecasting` ·
`market_intelligence` · `research` · `ideation` ·
`psychology` · `script_generation` · `visual_intelligence` · `voice_audio` ·
`attention_graph` · `ranking` · `script` · `critic` · `revision` ·
`citation` · `seo` · `threat_detection` · `quality`

## Live engine (trend intelligence — Agent 11)

`trend_forecasting` — the Trend Discovery & Forecasting Engine
(`engines/trend_forecasting.py`, logic in `services/trend_intelligence/`).
Subclasses `ContractEngine`, runs deterministically in Demo Mode inside
the trend stage right after `opportunity_ranking`, and produces
`trend_forecasts`, `trend_classifications`, `opportunity_recommendations`,
and `trend_intelligence_report` (see `DATA_CONTRACTS.md` §2.2 and
`TREND_INTELLIGENCE.md`). New trend sources auto-discover from
`providers/trend_sources/`; the on-demand query surface is the
`OpportunityFeed` (`services/trend_intelligence/feed.py`).

## Live engine (market intelligence — Agent 11)

`market_intelligence` — the Market Intelligence Department
(`engines/market_intelligence.py`, logic in
`services/market_intelligence/`). Subclasses `ContractEngine`, runs
deterministically inside the trend stage right after `trend_forecasting`,
and produces `market_opportunities`, `market_roadmap`, and
`market_intelligence_report` (see `DATA_CONTRACTS.md` §2.3 and
`MARKET_INTELLIGENCE.md`). It layers competition analysis, pluggable
market forecast models, ROI estimation, an evergreen engine, strategic
actions, roadmap/queue/calendar generation, and executive reporting on
top of the ranked opportunities — calibrated by Agent 9's analytics
history via the learning bridge. The on-demand query surface is
`get_market_intelligence()` (`services/market_intelligence/department.py`).

## Live engines (media production)

`scene_planning` · `narration` · `visual_planning` · `asset_manager` ·
`subtitle` · `timeline` · `render_package` · `publishing_queue`

## Live engines (render — Agent 6)

`image` (asset resolution) · `video` (package assembly) · `render`
(the unified Render & Video Production façade). All three subclass
`ContractEngine`, run in Demo Mode via mock providers, and produce the
Agent 6 render package (see `DATA_CONTRACTS.md` §render_package and
`engines/render/README.md`). Real backends swap in behind `providers/`
(`set_image_provider` / `set_video_provider` / `set_music_provider`) and
`engines.render.assets.register_fulfiller()`.

## Live engine (seo — Agent 8)

`seo_optimization` — the Global Content Optimization Engine
(`engines/seo_optimization.py`, logic in `services/seo/`). Subclasses
`ContractEngine`, runs deterministically in Demo Mode, and produces
ranked titles, keyword/hashtag/description packages, thumbnail
recommendations, localization plans, publish windows, the ten-metric
Optimization Report, and standardized PublishingPackages (see
`DATA_CONTRACTS.md` §6 and `engines/seo/README.md`). SEO signal providers
auto-discover from `providers/seo_sources/` — live APIs swap in per file.

## Live engines (publish — Agent 7)

`scheduler` (timezone-aware publish-time planning) · `publishing` (the
Publishing & Distribution Engine façade). Both live in
`engines/publishing/` (logic in `services/publishing/`), subclass
`ContractEngine`, and run deterministically in Demo Mode via mock provider
adapters — YouTube Shorts, Instagram Reels, Facebook Reels, TikTok, X,
LinkedIn, Pinterest (`providers/publishing/`). The `scheduler` contract
stub graduated from `engines/future_stubs.py` (same key, same input
contract); the `publishing` planned stub graduated from the former
`engines/publishing.py`. Output: `publish_schedule` +
`publishing_result` / per-item `publishing_package` slots (see
`DATA_CONTRACTS.md` §7 and `engines/publishing/README.md`). Real platform
APIs swap in via `register_publishing_provider()` — one adapter per file.

## Live engines (analytics + learning — Agent 10)

`analytics` (post-publish performance ingestion, retention curves,
attribution) · `learning` (pattern mining, weight recommendations,
long-term memory). Logic in `services/analytics/` and `services/learning/`;
see `ANALYTICS_LEARNING.md`.

## Live engine (creative — Agent 12)

`creative_studio` — the Creative Studio (`engines/creative_studio.py`,
logic in `services/creative_studio/`). Subclasses `ContractEngine`, runs
as the first distribution stage after packaging, and fills
`creative_package` (storyboards, shot lists, style libraries, character
consistency, environments). Asset backends swap in via
`register_creative_provider()` (`providers/creative/`). See
`CREATIVE_STUDIO.md`.

## Live engine (asset generation — Agent 14)

`asset_generation` — the Universal Asset Generation Engine
(`engines/asset_generation.py`, logic in `services/asset_generation/`,
providers in `providers/asset_generation/`). Transforms structured creative
requests into production-ready visual assets through swappable AI provider
adapters. Writes `asset_package` on each ContentPackage; context keys
`asset_generation_summary` + `asset_packages`. Runs in the distribution
pipeline after Creative / Character Universe, before Animation / Render.
Phase 2 (v1.1): provider catalog, latency-aware selection, batch
generation, job-queue interfaces, usage tracking, asset metadata, and
prepared media classes for animation / audio / motion graphics. See
`ASSET_GENERATION_ENGINE.md`.

## Live engine (ai director — Agent 18)

`ai_director` — the AI Director & Executive Creative Decision Engine
(`engines/ai_director.py`, logic in `services/ai_director/`). Consumes
intelligence from Psychology, Script, Visual, Voice, Trend, Market, and
Analytics packages and determines the optimal production strategy before
assets are generated. Writes `director_package` on each ContentPackage;
context keys `ai_director_summary` + `ai_director_packages`. Runs in the
distribution pipeline after packaging, before Creative Studio. Configurable
decision policies with a reinforcement-learning feedback hook. See
`AI_DIRECTOR.md`.

## Live engine (post-production — Agent 17)

`post_production` — the Post-Production & Intelligent Editing Engine
(`engines/post_production.py`, logic in `services/post_production/`,
providers in `providers/post_production/`). Consumes completed render
packages and produces polished publication-ready productions: master edit
timeline, intelligent scene cuts, finalized audio mix, styled captions,
color grading, motion graphics, platform exports, and QC validation.
Writes `post_production_package` on each ContentPackage; context keys
`post_production_summary` + `post_production_packages`. Runs in the
distribution pipeline after render, before seo. See
`POST_PRODUCTION_ENGINE.md`.

## Reserved keys (planned / contract stubs — do NOT reuse)

| Key | Status | Future owner |
|---|---|---|
| `voice` | planned stub | Voice Pipeline (real TTS / voice clone) |
| `brand_management` | contract stub | Multi-Brand OS |
| `optimization_lab` | contract stub (wired in `optimization` stage) | **Agent 13** — merge worktree |
| `character_universe` | contract stub (wired in `character_universe` stage) | **Agent 15** — merge worktree |
| `animation` | contract stub (wired in `animation` stage) | **Agent 16** — merge worktree |
| `business_intelligence` | name reserved | Future BI & Monetization |
| `provider_runtime` | service (Agent 19) | Provider Integration & Runtime — see `PROVIDER_INTEGRATION.md` |
| `workflow_executor` | service (Agent 21) | End-to-End Workflow Executor — see `WORKFLOW_EXECUTOR.md` |
| `autonomous_production` | service (Agent 23) | Autonomous Production Executor — see `AUTONOMOUS_PRODUCTION_EXECUTOR.md` |
| `autonomous_executive` | name reserved | Agent 22 — Autonomous Executive |

## Studio service (Agent 20 — LIVE)

Not an engine — a **service + UI layer** (`services/studio/`, `ui/tabs/studio.py`).
Integrates via `ideation.run_command()` (Orchestrator) and `ProviderRuntime`.
No engine key; listed here for discoverability. See `STUDIO_UI.md`.

> Note: the earlier reserved name `ip_management` is **retired** in favor
> of `character_universe` (Agent 15's actual engine key).

Contract stubs live in `engines/future_stubs.py` and already declare their
input/output contracts — inspect any engine with
`registry.get_engine(key).diagnostics()`.

## Capability index & dependency graph (machine-readable)

- `registry.describe_all()` — uniform self-description of every registered
  engine (id, name, version, ready, contracts, dependencies, capabilities).
- `registry.capability_index()` — capability tag → engine keys.
- `registry.dependency_graph()` — declared upstream dependencies per engine.

`tests/test_architecture.py` keeps the index and graph consistent with the
registry (no unregistered keys, no dangling dependencies). Human-readable
view: `SYSTEM_DEPENDENCY_MAP.md`.

## Adding an engine (checklist)

1. Reserve/confirm the key here and in `AGENT_WORKFLOW.md`.
2. Subclass `ContractEngine` in your landing zone; declare contracts.
3. Append the registration in `engines/__init__.py` (Agent 1 review).
4. Map the key to a stage in `services/orchestrator/stages.py`
   (`STAGE_OF_ENGINE` / `STAGE_GROUPS` / `DISTRIBUTION_STAGES`) — Agent 1 review.
5. Add a dedicated test file proving registration, contracts, and behavior.
