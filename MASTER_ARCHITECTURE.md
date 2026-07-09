# Generational — Master Architecture

**Document status:** Canonical architecture reference. Every agent (human or AI) working on this codebase reads this first.
**Entry point:** `app.py` (Streamlit shell only — no business logic).

**Companion documents:** [`ARCHITECTURE_DIRECTIVES.md`](ARCHITECTURE_DIRECTIVES.md) (mandatory rules — read Directive #1 first) · [`OPERATING_SYSTEM.md`](OPERATING_SYSTEM.md) (how the pieces form one OS) · [`AGENT_REGISTRY.md`](AGENT_REGISTRY.md) (agent roster, departments, future expansion) · [`SYSTEM_DEPENDENCY_MAP.md`](SYSTEM_DEPENDENCY_MAP.md) (layer diagram, data flow, dependency graph) · [`CAPABILITY_MATRIX.md`](CAPABILITY_MATRIX.md) · [`ENGINE_CAPABILITY_INDEX.md`](ENGINE_CAPABILITY_INDEX.md) · [`PIPELINE_SPEC.md`](PIPELINE_SPEC.md) (complete stage flow, live + future) · [`DATA_CONTRACTS.md`](DATA_CONTRACTS.md) (ContentPackage, context keys, engine contracts) · [`ENGINE_REGISTRY.md`](ENGINE_REGISTRY.md) (registered + reserved engine keys) · [`ORCHESTRATOR.md`](ORCHESTRATOR.md) (kernel API) · [`AGENT_WORKFLOW.md`](AGENT_WORKFLOW.md) (ownership + merge safety) · [`ARCHITECTURE_REVIEW.md`](ARCHITECTURE_REVIEW.md) (latest architecture audit + scores).

---

## Table of Contents

1. [Mission](#1-mission)
2. [Current Pipeline](#2-current-pipeline)
3. [Agent Responsibilities](#3-agent-responsibilities)
4. [Data Flow](#4-data-flow)
5. [Core Data Objects](#5-core-data-objects)
6. [Folder Structure](#6-folder-structure)
7. [MVP Goal](#7-mvp-goal)
8. [Roadmap](#8-roadmap)
9. [Non-Negotiable Rules](#9-non-negotiable-rules)
10. [Next Immediate Step](#10-next-immediate-step)

---

## 1. Mission

Generational is an **autonomous AI media operating system**.

It is not a content generator, a script writer, or a single-channel automation tool. It is software for **building and operating multiple faceless short-form content brands** across TikTok, YouTube Shorts, Instagram Reels, and future platforms — with minimal human intervention.

The system as a whole must be able to:

- Discover profitable content opportunities before they saturate
- Understand human psychology, attention, and virality mechanics
- Write scripts, plan visuals, plan audio, and render professional short-form video
- Publish automatically to the right platform, at the right time, in the right format
- Measure performance, learn from it, and make every future piece of content better
- Run many brands (channels) in parallel, each with its own niche, voice, and strategy

The end state is a **portfolio operator**: one system, many self-improving media brands.

---

## 2. Current Pipeline

Content flows through eleven stages. Each stage is owned by exactly one agent (Section 3) and communicates only through structured data objects (Section 5).

```
Trend Discovery
    → Psychology & Virality
    → Ranking
    → Script Generation
    → Visual Intelligence
    → Voice & Audio
    → Video Rendering
    → Quality Control
    → Publishing
    → Analytics
    → Learning Engine
```

Rules of the pipeline:

- **Stages are sequential and gated.** A candidate that fails a stage's quality threshold does not advance.
- **Stages never call each other directly.** This is **Architecture Directive #1 — Orchestrator-Only Communication** (see [`ARCHITECTURE_DIRECTIVES.md`](ARCHITECTURE_DIRECTIVES.md)), enforced by `tests/test_architecture.py`. Engines consume the previous stage's output object and emit their own; shared analysis logic lives in `engines/analysis.py` / `engines/heuristics.py`, never in engine-to-engine imports. Orchestration lives in `services/orchestrator/` (see [`ORCHESTRATOR.md`](ORCHESTRATOR.md)) — the single interface every consumer (UI, future scheduler, automation) uses; nothing invokes engines directly.
- **Every stage is independently runnable and testable** with a fixture input, without running the stages before it.
- **The Learning Engine closes the loop.** Its outputs feed back into Trend Discovery, Psychology scoring, Script Generation, and scheduling decisions.

---

## 3. Agent Responsibilities

Each agent owns one pipeline stage end to end: its logic, its output contract, and its tests. Current module homes in this repo are noted so future agents know where to work.

### Agent 1: Trend Discovery & Opportunity Engine

Finds what to make before anyone asks. Pulls signals from trend providers, normalizes them into a universal trend model, and scores each opportunity 0–100 for timing, saturation, monetization potential, and niche fit. Only opportunities above the gate enter the pipeline.

- **Owns:** trend ingestion, opportunity scoring, idea candidate creation
- **Modules:** `engines/trend_discovery.py`, `engines/opportunity_ranking.py`, `services/trends/`

### Agent 11: Trend Forecasting & Intelligence Engine — LANDED

The prediction layer on top of Agent 1's discovery. Quality-controls the raw signal batch (duplicates, near-duplicates, expired/stale signals, spam, low-confidence and conflicting sources), forecasts each ranked opportunity (time to peak, expected lifespan, growth trajectory, saturation risk, publishing window and cadence, projected future score, forecast confidence), classifies it on three axes (lifecycle: breaking→declining; content type: evergreen/seasonal/recurring/topical; market reach: niche→mass market), and emits one structured recommendation per opportunity — platform, hook direction, psychology strategy, duration, format, thumbnail/title direction, SEO guidance, ROI, risk, and priority. The `OpportunityFeed` answers the pipeline's queries on demand (top / top-10 / emerging / evergreen / per-platform / highest-ROI / highest-confidence), and Knowledge-Base performance history feeds every ranking (learning loop). Recommendations are strategy only — this agent never generates content. Six additional provider adapters (Instagram, Facebook, X, blogs, industry publications, internal historical analytics) extend discovery coverage. See `TREND_INTELLIGENCE.md`.

- **Owns:** trend quality control, forecasting, opportunity classification, structured recommendations, the opportunity feed, trend-intelligence configuration
- **Modules:** `engines/trend_forecasting.py`, `services/trend_intelligence/`, new drop-in providers under `providers/trend_sources/`

### Agent 11 (Phase 2): Market Intelligence Department — LANDED

The company's strategic planning engine, layered on the forecasting layer above. Everything the company creates begins here: seven more signal providers (academic publications, product launches, AI research, GitHub, developer communities, podcast rankings, search volume — 18 sources total) feed a full market-analysis chain per topic — competition analysis (publishing frequency, creator saturation, average views/engagement/retention/CTR, market difficulty, content-gap score), pluggable market forecast models (growth rate, peak/decline dates, lifespan, virality potential, saturation, competition level, expected longevity, historical similarity), an evergreen engine (trending/seasonal/evergreen/educational/news/reference), ROI estimation, and strategic actions (publish immediately, monitor, delay, expand into series, repurpose, translate, localize, long/short-form versions, variants). The result is priority-ranked `MarketOpportunity` objects, a content roadmap (daily/weekly/monthly, quarterly strategy, evergreen/trending/high-ROI/low-competition queues, a dated publishing calendar), and a full report suite with an executive summary. Agent 9's analytics history calibrates ROI, confidence, competition, and rankings through a learning bridge — the department gets smarter with every published item. The pipeline queries it through the `market_intelligence` engine or the department singleton (highest priority / top-10 / trending / evergreen / per-platform / localization / calendar). Structured opportunities only — never scripts, never creative assets. See `MARKET_INTELLIGENCE.md`.

- **Owns:** market signal architecture, competition analysis, market forecast models, ROI estimation, strategic recommendations, content roadmap, market reporting, market-intelligence configuration
- **Modules:** `engines/market_intelligence.py`, `services/market_intelligence/`, seven drop-in providers under `providers/trend_sources/`

### Agent 2: Psychology & Virality Engine

The attention scientist. Scores every candidate idea across psychological dimensions (curiosity, emotional charge, identity relevance, novelty, controversy, and more), blends them into a weighted ViralScore, and explains the score in plain English. Also screens for psychological failure modes (clickbait without payoff, weak hooks, policy risk). Exposes its three scoring modules through one standardized **Behavioral Intelligence API** (Section 5.1) so any other agent's engine can consume a single typed report instead of three separately-shaped dicts.

- **Owns:** psychology scoring, attention profiling, threat detection, the Behavioral Intelligence report contract
- **Modules:** `engines/psychology.py`, `engines/attention_graph.py`, `engines/threat_detection.py`, `services/behavioral_intelligence/`

### Agent 3: Script Generation & Storytelling Engine

Turns a scored idea into a production-ready cinematic script. Every variant is built section-first — Primary Hook, Pattern Interrupt, Curiosity Hook, Context, Escalation, Evidence, Emotional Peak, Resolution, CTA — with per-section narration, duration, emotional intensity, attention score, visual intent, B-roll type, and caption emphasis. A Hook Engine writes ten styled hook candidates (curiosity, shock, question, FOMO, statistics, contrarian, story, mystery, authority, urgency) and ranks them with the idea's psychology dimensions; a retention model estimates drop-off risk, engagement, retention, rewatch probability, curiosity strength, and emotional pacing per variant. The winning variant ships as a `structured_script`: director-ready scene breakdown (camera, motion, captions, sound cues, transitions), emotion/attention timelines, voice instructions, caption plan, alternate hooks, retention model, and locale (language/region/dialect — translation-ready).

- **Owns:** script sections, hook engine, retention model, script variants, storytelling structure, script scoring, structured script contract
- **Modules:** `engines/script_generation.py`, `engines/script.py`, `services/scripts/`

### Agent 4: Visual Intelligence Engine (Cinematic AI Director)

The Cinematic AI Director. Consumes structured output from Trend Discovery, the Psychology Engine, the Script Engine (`structured_script`), and the Attention Graph, then directs every second of visual attention: a professional shot list (14 shot types with lens/depth-of-field metadata), 15 runtime-extensible style presets, per-scene 12-trigger visual psychology scores with predicted viewer retention, provider-agnostic asset requests through source adapters (AI image/video, licensed stock, user uploads, brand assets, future avatars), model-ready AI prompts, scored thumbnail concepts with eye direction and click probability, a hook-frame sequence, and a versioned machine-consumable Render Package (see `VISUAL_PRODUCTION_PACKAGE.md`).

- **Owns:** storyboards, shot lists, style presets, visual psychology + retention prediction, visual prompts, asset sourcing, thumbnails, pacing/camera/motion plans, render preparation
- **Modules:** `engines/visual_intelligence.py`, `engines/visual_planning.py`, `engines/scene_planning.py`, `services/visual/`

### Agent 5: Voice & Audio Engine

The sound brain. Converts the script and visual package into a complete audio plan: niche-matched voice style, per-scene narration plan (pace, pauses, emphasis), layered sound effects, background music direction (BPM, key, energy curve), and a scene-by-scene audio cue sheet.

- **Owns:** narration plans, voice styles, SFX, music direction, audio cue sheets
- **Modules:** `engines/voice_audio.py`, `engines/voice.py`, `engines/narration.py`, `services/audio/`

### Agent 6: Video Rendering Engine — LANDED (mock render)

Turns plans into pixels. Consumes the full ProductionPackage (structured script, scene breakdown, visual package, audio package, captions, quality score) and produces the render-ready 9:16 vertical package: a contiguous master timeline, per-scene render instructions (asset type, prompts, footage slots, camera/motion effects), word-by-word caption plans with safe-area layouts, a four-track audio mix plan with ducking and loudness placeholder, validation with a production readiness score, and a **mock render** simulating the full pass. Real backends (AI image/video generation, stock, avatars, ffmpeg/cloud encoding) swap in behind provider interfaces without contract changes.

- **Owns:** asset resolution, timeline construction, scene render plans, caption render plans, audio mixing plans, transitions/motion instructions, render validation, (mock) rendering
- **Modules:** `engines/render/` (engine, models, timeline, scene_plans, assets, captions, audio_mix, transitions, motion, packaging, validator, renderer), `engines/image.py`, `engines/video.py`; legacy media-production helpers: `engines/render_package.py`, `engines/timeline.py`, `engines/subtitle.py`, `engines/asset_manager.py`

### Agent 14: Universal Asset Generation Engine — LANDED (mock providers)

The generation department. Consumes Creative Studio asset requirements (or fallback scene plans) and produces production-ready visual assets through swappable AI provider adapters — images, illustrations, thumbnails, textures, video clips, icons, 3D prep assets, and more. Provider Selection Engine picks the best backend; Prompt Compiler optimizes per dialect; content-address cache avoids duplicate generation; quality analysis gates readiness for render.

- **Owns:** asset generation, prompt compilation, provider selection, asset registry, caching, quality validation
- **Modules:** `engines/asset_generation.py`, `services/asset_generation/`, `providers/generation_provider.py` + `providers/asset_generation/`
- **See:** `ASSET_GENERATION_ENGINE.md`

### Agent 18: AI Director & Executive Creative Decision Engine — LANDED

The executive creative department. Consumes intelligence from Psychology,
Script, Visual Intelligence, Voice, Trend, Market, and Analytics and
determines the optimal production strategy before assets are generated.
Produces structured `director_package` briefs with production strategy,
platform targets, creative/visual/animation style, camera plan, pacing,
shot plan, character/music/narration/editing direction, optimization hints,
asset requirements, quality targets, and orchestration notes for Agents
12–17. Configurable decision policies with a reinforcement-learning
feedback hook. Never generates media or mutates other agents' slots.

- **Owns:** executive creative direction, production strategy, platform/format selection, conflict detection, graceful degradation, orchestration notes
- **Modules:** `engines/ai_director.py`, `services/ai_director/`
- **See:** `AI_DIRECTOR.md`

### Agent 17: Post-Production & Intelligent Editing Engine — LANDED (mock providers)

The editing department. Consumes completed render packages (timeline, caption
render plan, audio mix plan, transitions, motion) plus creative and audio
context, and produces polished publication-ready `post_production_package`
deliverables: master edit timeline, intelligent scene cuts, finalized audio
mix, styled captions, color grading, motion graphics, platform-optimized
exports, and QC validation. Real editing backends (FFmpeg, Premiere,
DaVinci, CapCut, Runway) swap in via provider adapters.

- **Owns:** intelligent editing, edit timeline, audio finalization, caption styling, color grading, VFX/motion graphics planning, platform optimization, export preparation, QC
- **Modules:** `engines/post_production.py`, `services/post_production/`, `providers/post_production/`
- **See:** `POST_PRODUCTION_ENGINE.md`

### Agent 7: Quality Assurance Engine

The last gate before the outside world. Checks rendered output against the plan: hook lands in the first seconds, audio/visual sync, subtitle accuracy, platform policy compliance, citation integrity, and overall craft. Rejects with actionable revision notes rather than a bare pass/fail.

- **Owns:** quality gates, critique, revision routing
- **Modules:** `engines/quality.py`, `engines/critic.py`, `engines/revision.py`, `engines/citation.py`

### Agent 8: Publishing & Platform Engine — LANDED (mock providers)

Gets content live. Manages platform accounts per channel (placeholder accounts — no real credentials), formats metadata (title, description, hashtags, thumbnail) per platform through provider adapters (YouTube Shorts, Instagram Reels, Facebook Reels, TikTok, X, LinkedIn, Pinterest — all mock today), schedules into optimal posting windows with timezone awareness, and runs the publish queue with exponential-backoff retries, full attempt history, and status tracking. Real platform APIs swap in one adapter at a time behind `PublishingProvider`.

- **Owns:** platform accounts (placeholders), metadata formatting, scheduling, publish queue, retries, publish history
- **Modules:** `engines/publishing/` (engine, scheduler_engine), `services/publishing/` (manager, queue, scheduler, retry, package, accounts, extensions), `providers/publishing/` + `providers/publishing_provider.py`; legacy pre-render queue: `engines/publishing_queue.py`

### Agent 9: Analytics & Learning Engine

Closes the loop. Collects post-publish performance (views, retention curves, watch time, engagement, follows), attributes outcomes back to the decisions that produced them, and emits learning signals that adjust future trend selection, psychology weights, script styles, and posting strategy.

- **Owns:** performance ingestion, attribution, learning signals, weight updates
- **Modules:** `engines/analytics.py`, `engines/learning.py`

### Development-agent landing zones (v8.1)

The stage owners above describe *pipeline responsibilities*. The parallel
*development agents* scheduled next map onto them with prepared landing
zones, contract stubs, and orchestrator stages already wired (see
`AGENT_WORKFLOW.md` §6 and each landing zone's README):

| Dev agent | Subsystem | Landing zone | Orchestrator stage |
|---|---|---|---|
| Agent 6 | Render & Video Production — **LANDED** (mock render, live stage) | `engines/render/` | `render` |
| Agent 7 | Publishing & Scheduler — **LANDED** (mock providers, live stage) | `engines/publishing/` + `services/publishing/` + `providers/publishing/` | `publish` |
| Agent 8 | Global Content Optimization (SEO) — **LANDED** (live stage) | `engines/seo/` + `engines/seo_optimization.py` + `services/seo/` | `seo` |
| Agent 9 | Analytics & Learning | `engines/analytics/` | `analytics` · `learning` |
| Agent 10 | Multi-Brand Operating System | `engines/brands/` | `brand_management` |
| Agent 14 | Universal Asset Generation — **LANDED** (mock providers, live stage) | `engines/asset_generation.py` + `services/asset_generation/` + `providers/asset_generation/` | `asset_generation` |
| Agent 18 | AI Director — **LANDED** (live stage) | `engines/ai_director.py` + `services/ai_director/` | `ai_director` |
| Agent 17 | Post-Production & Intelligent Editing — **LANDED** (mock providers, live stage) | `engines/post_production.py` + `services/post_production/` + `providers/post_production/` | `post_production` |

Future engines subclass `ContractEngine` (`engines/contracts.py`) and fill
their slot in the canonical `ContentPackage` (`DATA_CONTRACTS.md`). Their
stages skip cleanly until the engines report ready.

---

## 4. Data Flow

Each stage receives exactly one structured input and produces exactly one structured output. No stage reads another stage's internals.

| Stage | Receives | Outputs |
|---|---|---|
| Trend Discovery | Raw platform/trend signals | `ContentIdea` (scored opportunity candidates) |
| Psychology & Virality | `ContentIdea` | `PsychologyReport` (ViralScore + explanation + threats) |
| Ranking | `ContentIdea` + `PsychologyReport` | `RankedIdea` (prioritized, gated shortlist) |
| Script Generation | `RankedIdea` | `ScriptPackage` (winning variant + alternates + scores) |
| Visual Intelligence | `ScriptPackage` + `PsychologyReport` + Attention Graph scores | `VisualPackage` (directed storyboard + shot list + prompts + asset requests + thumbnails + retention curve + Render Package) |
| Voice & Audio | `ScriptPackage` + `VisualPackage` | `AudioPackage` (narration plan + SFX + music + cue sheet) |
| Video Rendering | `VisualPackage` + `AudioPackage` + `ScriptPackage` + captions | `render_package` v2.0 (timeline, scene/caption/audio-mix plans, validation, mock render manifest — becomes `RenderedVideo` when real backends land) |
| Quality Control | `RenderedVideo` + upstream packages | Approved `RenderedVideo` or revision notes routed back |
| Content Optimization (SEO) | `ContentPackage` (render + script + psychology + trend context) | Enriched `seo_package` + `PublishingPackage` v1.0 (ranked titles/hashtags/thumbnails/windows, keyword + localization packages, Optimization Report) |
| Publishing | Approved `RenderedVideo` + `PublishingPackage` + `Channel` config | `PublishingResult` + per-item `publishing_package` (queued/scheduled/published jobs with post IDs, URLs, timings — mock posts today; becomes `PublishedPost` when real APIs land) |
| Analytics | `PublishedPost` + platform APIs | `AnalyticsRecord` (performance over time) |
| Learning Engine | `AnalyticsRecord` + full decision history | `LearningSignal` (weight/strategy adjustments fed upstream) |

In plain terms: the Trend Engine outputs content ideas. The Psychology Engine scores those ideas. The Ranking stage decides which ideas deserve production. The Script Engine creates structured scripts. The Visual Engine creates storyboards and prompts. The Audio Engine creates narration and sound plans. The Renderer creates the final video. The QA Engine approves it. The Publishing Engine posts it. The Analytics Engine records how it performs. The Learning Engine uses that performance to improve every future decision.

---

## 5. Core Data Objects

These are the contracts between stages. They live in the models layer (`core/models.py`, `core/production_models.py`) and are the **only** way stages communicate. Every object is serializable, versioned, and carries the IDs needed to trace a published post back to the trend that spawned it.

| Object | Purpose | Key fields (indicative) |
|---|---|---|
| **ContentIdea** | A single candidate concept discovered from trends | id, channel_id, topic, angle, source signals, opportunity score, discovered_at |
| **PsychologyReport** | Psychological evaluation of one idea. Concretely implemented as `BehavioralIntelligenceReport` (Section 5.1) | idea_id, dimension scores, ViralScore (0–100), explanation, detected threats |
| **RankedIdea** | An idea that survived ranking | idea_id, rank, composite score, gate decisions, selected platform targets |
| **ScriptPackage** | Complete script output for one idea (concrete shape: `structured_script`, `services/scripts/structure.py`) | idea_id, winning variant, alternate hooks, annotated sections, scene breakdown, emotion/attention timelines, voice instructions, caption plan, retention model, retention checkpoints, CTA, locale, per-variant scores |
| **VisualPackage** | Complete directed visual plan for one script (contract: `VISUAL_PRODUCTION_PACKAGE.md`) | script_id, directed scenes (shot/lens/DOF, style, attention level, predicted retention), shot list, asset requests, image/video prompts per model, thumbnail concepts + click probability, hook frames, retention curve, Render Package, overall visual score |
| **AudioPackage** | Complete audio plan for one script | script_id, voice style, per-scene narration plan (wpm, pauses, emphasis), SFX layers, music direction (BPM/key/energy), cue sheet, overall audio score |
| **RenderedVideo** | The final produced asset | package_ids, file path/URI, duration, resolution, aspect ratio, render manifest, QA status |
| **PublishedPost** | One live post on one platform | video_id, platform_account_id, platform post ID, URL, publish time, metadata used |
| **AnalyticsRecord** | Performance snapshot(s) for one post | post_id, views, retention curve, watch time, likes/comments/shares, follows attributed, captured_at |
| **LearningSignal** | A concrete adjustment derived from outcomes | source records, target (weights/strategy/style), adjustment, confidence, applied_at |
| **Channel** | One faceless brand the system operates | id, name, niche, voice/style profile, target platforms, cadence, strategy state |
| **PlatformAccount** | Credentials and state for one platform login | channel_id, platform, auth/token refs, posting limits, health status |

Object rules:

- New fields are additive; removing or renaming a field is a breaking change and requires updating every consumer plus its tests.
- Every object carries the upstream IDs it derived from, so the Learning Engine can attribute outcomes end to end.
- If a stage needs data another stage doesn't emit, extend the object contract — never reach into another engine.

### 5.1 Behavioral Intelligence Report (concrete implementation)

`PsychologyReport` above is the abstract contract; `BehavioralIntelligenceReport`
(`services/behavioral_intelligence/models.py`) is the concrete, versioned
dataclass every engine actually imports. It exists so Script Generation,
Visual Intelligence, Voice & Audio, and any future consumer never parse
`psychology` / `attention_graph` / `threat_report` dicts by hand — they read
one typed object.

**How reports are generated.** `services/behavioral_intelligence/builder.py::build_report(candidate)`
reads whatever the candidate currently carries and maps each field to its
best available source, preferring the richer/later engine's data and
falling back to an earlier engine (or a heuristic proxy) when it isn't
there yet:

| Report field | Preferred source | Fallback |
|---|---|---|
| `viral_score` | Psychology `viral_score` | — (always present once Psychology runs) |
| `attention_score` | Attention Graph `attention_score` | `viral_score` |
| `curiosity_score` | Psychology `curiosity_gap` | — |
| `emotional_intensity` | Psychology `emotional_intensity` | — |
| `novelty_score` | Psychology `novelty` | — |
| `shareability_score` | Attention Graph `shareability` | Psychology `share_likelihood` |
| `replay_probability` | Attention Graph `rewatch_probability` | Psychology `replay_value` |
| `comment_probability` | Attention Graph `comment_likelihood` | Psychology `comment_likelihood` |
| `retention_prediction` | Psychology `retention_potential` | — |
| `hook_strength` | Attention Graph `first_3_second_hook` | Psychology `first_3_second_hook` |
| `identity_resonance` | Attention Graph `identity_signaling` | Psychology `audience_identity` |
| `visual_interest_score` | Average of Psychology `visual_hook_strength` + Attention Graph `visual_novelty` | Whichever one exists |
| `narrative_tension` | Attention Graph `story_tension` | Average of Psychology `surprise` + `dopamine_curve` |
| `confidence` | Rule-based signal count (see below) | — |
| `recommendations` | Flagged Threat Report fixes + weakest-field growth tips | Generic "no major gaps" message |

**Who attaches it, and when.** `engines/psychology.py` calls
`attach_report()` at the end of its `run()` — the earliest point a report
can exist — so it's already on `candidate["behavioral_intelligence"]` by the
time Script Generation, Visual Intelligence, and Voice & Audio run (they all
execute before the Attention Graph in `core/workflows.py`). `engines/attention_graph.py`
and `engines/threat_detection.py` each call `attach_report()` again at the
end of their own `run()`, so later stages see a progressively richer report
without any stage needing to know about the others.

**Score meanings.** Every field's plain-English meaning and exact source
mapping lives in `FIELD_DESCRIPTIONS` (`services/behavioral_intelligence/models.py`)
— read there rather than duplicating it here, so the doc can never drift
from the code.

**Confidence.** Not a behavioral score — it's how much upstream signal
backed the report. `_confidence()` starts at 55 and adds a fixed amount per
signal present (Psychology +10, Attention Graph +15, Threat Report +10,
script text +5), clamped to 50–98. Today this is a hand-tuned rule; see
below for how it's meant to evolve.

**Recommendations.** Up to 5 strings: flagged Threat Report fixes reserve
their slots first (production risk beats growth opportunity), then the
weakest-scoring fields fill whatever room is left, using the single-tip-per-
field map in `builder.py::FIELD_TIPS`.

**Extension points for future ML models.** Every function in
`builder.py` is a pure function over plain dicts/dataclasses with a fixed
signature, so a learned model can replace any one of them without touching
callers:

- Replace `build_report()`'s per-field mapping with a model that predicts
  all 13 scores jointly from raw text + upstream dimensions — the dataclass
  contract (`BehavioralIntelligenceReport`) doesn't change.
- Replace `_confidence()` with a learned calibration (e.g. predicted-vs-
  actual error conditioned on which signals were present) — must keep
  returning an int 0–100.
- Replace `_recommendations()`'s static `FIELD_TIPS` lookup with a generator
  conditioned on the actual script/visual/audio package, once those exist —
  must keep returning `list[str]`.
- The real target to eventually train against is the Analytics/Learning
  Engine's `AnalyticsRecord` → `LearningSignal` loop (Section 3, Agent 9):
  once published posts report real retention/share/comment outcomes, this
  module is where predicted scores get reconciled against them.

---

## 6. Folder Structure

Target structure for the codebase. New code should conform to this layout; existing top-level modules (`engines/`, `services/`, `core/`, `providers/`, `ui/`, `tests/`) map onto it directly and can be migrated under `src/` incrementally — never as a big-bang rewrite.

```
src/
  engines/              # One folder per pipeline stage — pure logic, no I/O side effects
    trends/             # Agent 1: discovery + opportunity scoring
    psychology/         # Agent 2: virality scoring, attention graph, threat detection
    ranking/            # Gate: composite ranking of scored ideas
    scripts/            # Agent 3: script variants + storytelling structure
    visuals/            # Agent 4: storyboards, prompts, thumbnails
    audio/              # Agent 5: narration, SFX, music planning
    rendering/          # Agent 6: timeline, assembly, subtitles, render (today: engines/render/)
    quality/            # Agent 7: quality gates, critique, revision
    publishing/         # Agent 8: accounts, metadata, scheduling, queue
    analytics/          # Agent 9a: performance ingestion + attribution
    learning/           # Agent 9b: learning signals + weight updates
  models/               # Core data objects (Section 5) — the stage contracts
  services/             # Orchestration (services/orchestrator/ — see ORCHESTRATOR.md), pipelines, job queue, provider wiring, storage
  ui/                   # Streamlit views — display only, zero business logic
  tests/                # Mirrors src/ — one test module per engine minimum
docs/                   # Architecture docs, decisions, session summaries
```

Layering rules:

- **engines** depend on **models** only. Never on services, UI, or each other.
- **services** orchestrate engines and own all external I/O (APIs, storage, queues, provider SDKs).
- **ui** calls services and renders their structured outputs. If the UI computes anything beyond formatting, that logic is in the wrong layer.
- **models** depend on nothing.

---

## 7. MVP Goal

The first true MVP is the **one-button planning pipeline**:

> The user clicks one button, and the system produces a complete content production package:
> **idea + psychology score + script + storyboard + visual prompts + audio plan.**

Concretely, one click runs Trend Discovery → Psychology → Ranking → Script Generation → Visual Intelligence → Voice & Audio, and presents a single unified package the user could hand to any human or AI production team.

Explicitly **out of scope** for the MVP:

- Automatic publishing (no platform posting yet)
- Automatic video rendering (plans, not pixels)
- Analytics and learning loops

The MVP is done when the full package generates reliably end to end, every stage's output validates against its data object contract, and the run is covered by an integration test.

---

## 8. Roadmap

Each phase must be fully integrated and tested before the next begins. "Integrate before expanding" (Section 9) applies at the phase level.

### Phase 1: Planning Pipeline *(current)*
One click produces the complete production package: idea, psychology score, script, storyboard, visual prompts, audio plan. This is the MVP in Section 7.

### Phase 2: Render-Ready Pipeline *(architecture landed — mock render)*
The planning package becomes a finished video: generated visuals, synthesized narration, music and SFX assembled per the cue sheet, subtitles burned in, QA-gated final render. Agent 6 shipped the complete render architecture (timeline, scene/caption/audio-mix plans, validation, provider seams) with a simulated renderer; the remaining work is wiring real generation/encoding providers behind the existing interfaces.

### Phase 3: Automated Publishing *(architecture landed — mock providers)*
Approved videos post themselves: multi-account platform management, per-platform metadata formatting, optimal-window scheduling, publish queue with retries. Agent 7 shipped the complete publishing architecture (provider adapters, timezone-aware scheduler, retry-capable queue, publish history, account/approval/analytics extension seams) with mock adapters; the remaining work is wiring real platform APIs behind the existing `PublishingProvider` interface.

### Phase 4: Analytics Feedback
Published posts report back: performance ingestion from platform APIs, retention-curve analysis, attribution of outcomes to upstream decisions, dashboards per channel.

### Phase 5: Self-Improving Autonomous Media System
The loop closes: learning signals automatically retune trend selection, psychology weights, script styles, visual/audio choices, and posting strategy. The system operates multiple channels with the human as portfolio manager, not operator.

---

## 9. Non-Negotiable Rules

These apply to every agent — human or AI — in every session:

1. **Do not break working pipeline stages.** If a stage works, changes to it must keep its existing tests green. Regressions are never an acceptable cost of new features.
2. **Every engine must have tests.** No engine ships or changes without unit tests, and pipeline changes without integration coverage don't merge.
3. **Every output must be structured.** Engines emit the data objects in Section 5 — never free-form text blobs that downstream stages have to parse.
4. **No decorative UI without function.** Every UI element displays real pipeline data or triggers a real pipeline action. Nothing exists for looks alone.
5. **Prefer a polished MVP over huge broken features.** A small thing that works end to end beats a big thing that almost works.
6. **Integrate before expanding.** A new engine is not "done" when its module works in isolation — it is done when it runs inside the full pipeline with real upstream input.
7. **Agents must summarize changes after each work session.** Every session ends with a summary of what changed, why, what was tested, and what the next agent should do — so no context is lost between sessions.

---

## 10. Next Immediate Step

**Complete Agent 5 (Voice & Audio Engine), then run a full integration test of the planning pipeline: Trend Discovery → Psychology & Virality → Ranking → Script Generation → Visual Intelligence → Voice & Audio Planning.**

Definition of done for this step:

1. Agent 5 produces a complete, contract-valid `AudioPackage` for every scripted candidate.
2. A single integration test drives the entire chain from raw trend input to finished audio plan with no manual intervention.
3. The combined output constitutes the full MVP production package from Section 7.

When this passes, Phase 1 is complete and work on Phase 2 (Video Rendering) may begin.

---

*This document is the source of truth for Generational's architecture. If code and this document disagree, fix one of them in the same session — never leave them divergent.*
