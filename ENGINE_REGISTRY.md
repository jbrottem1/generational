# Generational — Engine Registry (v8.1)

How engines register, what exists today, and which keys are reserved for
Agents 6-10. The registry (`engines/registry.py`) is the single source of
truth at runtime; this document is its map.

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

## Reserved keys (planned / contract stubs — do NOT reuse)

| Key | Stub type | Future owner | Stage |
|---|---|---|---|
| `voice` | planned | Voice Pipeline agent | audio (real TTS) |
| `analytics` | planned | **Agent 9** | analytics |
| `learning` | planned | **Agent 9** | learning |
| `brand_management` | contract stub | **Agent 10** | brand_management |

Contract stubs live in `engines/future_stubs.py` and already declare their
input/output contracts — inspect them with
`registry.get_engine(key).diagnostics()`.

## Adding an engine (checklist)

1. Reserve/confirm the key here and in `AGENT_WORKFLOW.md`.
2. Subclass `ContractEngine` in your landing zone; declare contracts.
3. Append the registration in `engines/__init__.py` (Agent 1 review).
4. Map the key to a stage in `services/orchestrator/stages.py`
   (`STAGE_OF_ENGINE` / `STAGE_GROUPS`) if it is a new stage — Agent 1 review.
5. Add a dedicated test file proving registration, contracts, and behavior.
