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

`trend_discovery` · `opportunity_ranking` · `research` · `ideation` ·
`psychology` · `script_generation` · `visual_intelligence` · `voice_audio` ·
`attention_graph` · `ranking` · `script` · `critic` · `revision` ·
`citation` · `seo` · `threat_detection` · `quality`

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
