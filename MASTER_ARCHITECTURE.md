# Generational — Master Architecture

**Current version:** v7.1.0  
**Status:** Source-backed research platform with a 18-dimension Psychology & Virality Engine, citation engine, and multi-factor quality gate  
**Entry point:** `app.py` (Streamlit shell only — no business logic)

This document is the canonical architecture reference for Generational. It describes how the system is built today, how to extend it safely, and how the team develops using ChatGPT, Claude, and Cursor.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Layered Architecture](#2-layered-architecture)
3. [End-to-End Flow](#3-end-to-end-flow)
4. [Development Workflow (ChatGPT + Claude + Cursor)](#4-development-workflow-chatgpt--claude--cursor)
5. [Engine Responsibilities](#5-engine-responsibilities)
6. [Provider System](#6-provider-system)
7. [Services Layer](#7-services-layer)
8. [Data & Persistence](#8-data--persistence)
9. [UI Contract](#9-ui-contract)
10. [Version Roadmap](#10-version-roadmap)
11. [Testing Rules](#11-testing-rules)
12. [Git Workflow](#12-git-workflow)
13. [Future Modules](#13-future-modules)
14. [Extension Points](#14-extension-points)

---

## 1. System Overview

### Mission

Generational is **not a content generator**. It is an **autonomous AI Media Operating System**: software that builds, operates, optimizes, and scales a portfolio of profitable digital media brands with minimal human intervention.

The system as a whole must be capable of: discovering profitable opportunities, understanding human psychology and SEO, researching topics, writing scripts, creating images, animation, video, narration, and music, rendering professional short-form content, publishing automatically, monitoring analytics, learning from results, improving future content, and managing many brands simultaneously.

The goal is not to automate one YouTube channel. The goal is software that operates an entire portfolio of AI media companies.

### What exists today

Generational v7.1 is a modular platform with:

- A **Trend Discovery Engine** — the front door: auto-discovered trend providers, a universal Trend model, and 0-100 Opportunity Scoring that gates what enters the pipeline
- A **Psychology & Virality Engine** — scores every candidate idea across 18 attention-science dimensions, blends them into a weighted 0-100 ViralScore, and produces a plain-English psychology report explaining why
- A **Knowledge Engine** with live Wikipedia, PubMed, arXiv, and Crossref connectors
- A **Citation Engine** that maps scripts to sources and flags unsupported claims
- An **Intelligence Pipeline** (12 stages) from trend discovery and opportunity ranking through ideas, psychology, scripts, critique, citation, SEO, and quality
- A **Media Production Pipeline** that turns approved scripts into render-ready packages
- A **Provider System** that keeps all vendor integrations swappable
- A **Job Queue + Workflow Engine** that coordinates every stage without tight coupling

### Design Principles

| Principle | Meaning |
|---|---|
| **Modular** | Everything is replaceable — providers, models, APIs, platforms, voice/video engines all sit behind interfaces. Never hardcode a vendor. |
| **Scalable** | Architecture must serve 1, 10, 100, or 1000 channels. No decision may cap future growth. |
| **Autonomous** | The system trends toward zero-touch operation; humans provide approvals and strategic decisions only. |
| **Self-improving** | Every completed video is training data. CTR, retention, watch time, comments, shares, revenue, SEO rank, thumbnail/hook performance, narration quality, visual style, music, publish timing, and trend timing all feed the Learning Engine. |
| **Safe** | Nothing publishes without passing Quality Gates (SEO, psychology, research confidence, fact confidence, visual/audio/narration quality, overall publish score). Below threshold → reject, revise, retry. |
| Provider-agnostic | Business logic never imports OpenAI, ElevenLabs, etc. directly |
| Composition over inheritance | Small modules, shared context dict, no god classes |
| UI separation | Streamlit is a thin shell; logic lives in `services/` and `engines/` |
| Fail-safe | Demo/heuristic fallbacks when AI or providers fail — never crash |
| Strong typing at boundaries | `core/models.py`, `core/production_models.py`, `services/research/models.py` |
| Testability | Every service has unit tests; tests never touch real `data/` |

### Target end-state pipeline

```
Research Engine → Trend Discovery → SEO Analysis → Psychology Analysis
    → Opportunity Ranking → Script Engine → Voice Engine → Image Engine
    → Animation Engine → Video Engine → Quality Review → Publishing
    → Analytics → Learning Engine → Knowledge Base → Continuous Improvement
```

Every stage in this chain already has a registered engine key (live or planned stub), so lighting up a stage never requires orchestration changes.

---

## 2. Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  UI (Streamlit)                                             │
│  app.py · ui/tabs/* · ui/components.py · ui/sidebar.py      │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  Services (orchestration)                                     │
│  ideation · production · research · assets · knowledge ·      │
│  channels · voice_profiles · pipeline                         │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  Job Queue (core/jobs.py)                                   │
│  submit → run → status · synchronous today, async-ready      │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  Workflow Engine (core/workflows.py)                        │
│  WORKFLOWS["intelligence"] · WORKFLOWS["media_production"]   │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  Engine Registry (engines/registry.py)                      │
│  20 live engines · 6 planned stubs                           │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  Providers (providers/)                                     │
│  Research sources · LLM · Voice · Image · Video · Music ·     │
│  Publishing · Analytics · Trend · SEO                         │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  Core (core/)                                               │
│  models · constants · parsing · state · storage · log ·       │
│  diagnostics · production_models · ai/                      │
└─────────────────────────────────────────────────────────────┘
```

### Package Responsibilities

| Package | Role |
|---|---|
| `app.py` | Page config, tab wiring, sidebar — **no business logic** |
| `ui/` | Streamlit presentation only |
| `services/` | Public APIs the UI calls; orchestrates jobs and workflows |
| `engines/` | Pipeline stage plugins — one module per capability |
| `providers/` | Swappable external backends (APIs, TTS, research sources) |
| `core/` | Shared infrastructure — no UI, no vendor SDKs |
| `tests/` | Unit and integration tests |
| `data/` | Local persistence (gitignored runtime data) |

---

## 3. End-to-End Flow

When the user clicks **Run Command** in the Ideas tab:

```
User Command
    │
    ▼
services/ideation.run_command()
    │
    ├─► Job Queue: workflow = "intelligence"
    │       │
    │       ▼
    │   Stage 0: Trend Discovery (front door)
    │       engines/trend_discovery.py → services/trends/manager.py
    │       → query all auto-discovered trend providers
    │       → normalize into universal Trend model
    │       │
    │       ▼
    │   Stage 1: Opportunity Ranking
    │       engines/opportunity_ranking.py → services/trends/scorer.py
    │       → score every trend 0-100 (11 factors)
    │       → only top 5 opportunities move forward
    │       → trend keywords feed ideation
    │       │
    │       ▼
    │   Stage 2: Research (Knowledge Engine)
    │       services/research/manager.py
    │       → parse intent
    │       → query enabled research providers
    │       → normalize ResearchDocument objects
    │       → score + filter weak sources
    │       → generate structured ResearchSummary
    │       → cache by topic (data/research_cache/)
    │       │
    │       ▼
    │   Stages 3–12: Intelligence Pipeline
    │       ideation → psychology → ranking → script →
    │       critic → revision → citation → seo → quality
    │       │
    │       ▼
    │   context["ideas"] with scores, SEO, references
    │
    ├─► services/knowledge.py — record hooks, scripts, research briefs
    │
    └─► services/production.run_media_production()
            │
            ▼
        Job Queue: workflow = "media_production"
        (publishable scripts only)
            │
            scene_planning → narration → visual_planning →
            asset_manager → subtitle → timeline →
            render_package → publishing_queue
            │
            ▼
        ProductionPackage attached to each approved idea
```

### Shared Context Contract

Every engine receives and returns updates to a shared `context: dict`. Key fields:

| Field | Set by | Consumed by |
|---|---|---|
| `command`, `niche`, `subject`, `goal` | Research | All downstream engines |
| `trends` | Trend Discovery | Opportunity Ranking |
| `trend_opportunities`, `top_opportunity`, `trend_dashboard` | Opportunity Ranking | UI (Trend Dashboard) |
| `trend_keywords` | Opportunity Ranking | Ideation prompt |
| `research` | Research | Ideation, Script, Quality, UI |
| `research_references` | Research | Script (traceability) |
| `candidates` | Ideation | Psychology, Ranking |
| `candidates[].psychology`, `.psychology_score`, `.viral_score`, `.psychology_report` | Psychology | Ranking, Quality, UI (idea card report expander) |
| `psychology_summary` | Psychology | UI, diagnostics |
| `ranked_candidates`, `selected_ideas` | Ranking | Script, SEO, Quality |
| `ideas` | Quality | Production, UI, Knowledge Base |
| `quality_summary` | Quality | UI, Production filter |
| `approved_content` | Production service | Media production engines |
| `production_packages` | Production service | UI, project persistence |

**Rule:** Never break backward-compatible keys in `context["research"]` (`topic_context`, `audience`, `search_intent`, `trend_strength`, `summary`, `opportunity_score`).

---

## 4. Development Workflow (ChatGPT + Claude + Cursor)

Generational is developed using a three-tool workflow. Each tool has a distinct role; overlap is intentional but bounded.

> **Multiple agents now work on this codebase in parallel.** Ownership rules, merge safety rules, branch strategy, and the pre-merge review checklist live in [`AGENT_WORKFLOW.md`](AGENT_WORKFLOW.md). Read it before editing shared files.

### Role Split

| Tool | Primary Role | When to Use |
|---|---|---|
| **ChatGPT** | Product vision, feature specs, prompt design, niche strategy | Define *what* to build before coding |
| **Claude** | Architecture review, large refactors, documentation, test design | Design *how* to build safely at scale |
| **Cursor** | Implementation, debugging, test runs, commits | Write and ship code in the repo |

### Recommended Cycle

```
1. SPEC (ChatGPT)
   Write a version brief: goals, constraints, success criteria.
   Example: "v5.0 — do not redesign UI, add Knowledge Engine."

2. ARCHITECTURE (Claude)
   Review spec against MASTER_ARCHITECTURE.md.
   Identify: new engines, services, providers, context fields, tests.
   Output: file list + integration points + risks.

3. IMPLEMENT (Cursor Agent)
   Follow spec + architecture notes.
   Rules:
   - Minimize diff scope
   - Match existing conventions
   - No UI redesign unless explicitly requested
   - Run pytest before commit

4. REVIEW (Claude or Cursor Bugbot)
   Check: provider isolation, context contract, fail-safes, tests.

5. DOCUMENT + COMMIT
   Update README.md for user-facing changes.
   Update MASTER_ARCHITECTURE.md for structural changes.
   Commit with version tag message: "vX.Y.Z Short description"
```

### Cursor-Specific Rules

- **Agent mode** for multi-file features (new engines, services, providers)
- **Ask mode** for architecture questions without code changes
- Never commit unless explicitly requested
- Never force-push `main`
- Tests must pass before declaring a version complete
- Use isolated `tmp_path` fixtures — never write to real `data/`

### Version Upgrade Checklist

When shipping a new version:

- [ ] Bump `APP_VERSION` in `core/constants.py`
- [ ] Add/update engines in `engines/__init__.py` if new stages
- [ ] Add workflow steps in `core/workflows.py` if new pipeline
- [ ] Extend tests in `tests/`
- [ ] Update `README.md` (user-facing)
- [ ] Update `MASTER_ARCHITECTURE.md` (developer-facing)
- [ ] Run `python -m pytest`
- [ ] Commit: `vX.Y.Z Description`

---

## 5. Engine Responsibilities

Engines are plugins registered in `engines/registry.py`. They **never call each other** — only the Workflow Engine coordinates them.

### Engine Contract

```python
class Engine(ABC):
    key: str           # registry key, used in WORKFLOWS
    label: str         # human-readable name
    icon: str          # UI display
    description: str

    def is_ready(self) -> bool: ...   # False = skipped by workflow
    def run(self, context: dict) -> dict: ...  # returns merge updates
```

### Intelligence Pipeline (12 live engines)

| Key | Module | Responsibility |
|---|---|---|
| `trend_discovery` | `engines/trend_discovery.py` | Front door — queries all trend providers; normalizes into universal Trend model |
| `opportunity_ranking` | `engines/opportunity_ranking.py` | Scores trends 0-100 (11 factors); only top opportunities move forward |
| `research` | `engines/research.py` | Knowledge Engine — live APIs + demo fallback; produces Research Brief |
| `ideation` | `engines/ideation.py` | Generates 20 candidate concepts grounded in research brief |
| `psychology` | `engines/psychology.py` | Psychology & Virality Engine — scores candidates on 18 attention dimensions, blends a weighted ViralScore (0-100), and produces a psychology report (deterministic) |
| `ranking` | `engines/ranking.py` | Weighted ranking; selects top N for scripting |
| `script` | `engines/script.py` | Writes 15–30s voiceover scripts from research facts |
| `critic` | `engines/critic.py` | Adversarial review — flags weak hooks, repetition, pacing |
| `revision` | `engines/revision.py` | Auto-rewrites flagged sections |
| `citation` | `engines/citation.py` | Maps scripts to sources; claim confidence; unsupported claim warnings |
| `seo` | `engines/seo.py` | Titles, hashtags, keywords, description, thumbnail concept |
| `quality` | `engines/quality.py` | Multi-factor publish gate (score + research + citations) |

**Workflow:** `WORKFLOWS["intelligence"]`

### Psychology & Virality Engine (deep dive)

`engines/psychology.py` is the attention-engineering core of the pipeline. It
runs immediately after Ideation (itself downstream of Trend Discovery) and
before Ranking/Script, so no concept is scripted, produced, or published
without first passing through a measurable model of human attention.

- **18 dimensions** (`score_dimensions()`): curiosity gap, emotional
  intensity, surprise, novelty, fear, humor, satisfaction, retention
  potential, replay value, comment likelihood, share likelihood, controversy
  (bounded by platform safety — capped ceiling regardless of trigger-word
  density), visual hook strength, first-3-second hook, dopamine curve,
  information density, audience identity, community appeal. Each is scored
  0-100 by deterministic text-feature analysis (word banks in
  `engines/heuristics.py`, punctuation, structure, digits, hook length) —
  free, fast, reproducible in every mode, no API key required.
- **ViralScore** (`viral_score()`): the 18 dimensions blend into one weighted
  0-100 score via `VIRAL_SCORE_WEIGHTS` — data, not code, so the future
  Learning Engine can retune weights from real performance results without
  touching scoring logic.
- **Psychology report** (`build_report()`): every candidate gets a tier
  (e.g. *Strong Viral Potential*), its top 3 strengths, its 3 weakest
  levers, a per-dimension explanation, and a one-line summary — attached to
  the idea as `psychology_report` and surfaced in the Ideas tab as a compact
  expander (no new UI pages).
- **Backward compatibility:** `psychology_score` (alias of the ViralScore)
  and the `psychology` dimension dict remain on every candidate so
  `ranking.py` and `quality.py` need no structural changes to consume it.
- **Quality Gate integration:** `engines/quality.py` derives `retention`,
  `ctr`, and a dedicated `virality` score (share/comment likelihood,
  audience identity, community appeal, bounded controversy) from the 18
  dimensions, so the publish gate rewards concepts built to spread — not
  just to be watched once.

### Media Production Pipeline (8 live engines)

| Key | Module | Responsibility |
|---|---|---|
| `scene_planning` | `engines/scene_planning.py` | Splits script into structured scenes |
| `narration` | `engines/narration.py` | Voice track via VoiceProvider (AI / recorded / clone-ready) |
| `visual_planning` | `engines/visual_planning.py` | Visual prompts per scene for future image/video providers |
| `asset_manager` | `engines/asset_manager.py` | Registers narration, visuals, thumbnails in Asset Manager |
| `subtitle` | `engines/subtitle.py` | Sentence + word-level subtitle timing, SRT output |
| `timeline` | `engines/timeline.py` | Assembles narration, visual, subtitle, music timing |
| `render_package` | `engines/render_package.py` | Bundles all assets for a future renderer |
| `publishing_queue` | `engines/publishing_queue.py` | Queues render packages for auto-posting |

**Workflow:** `WORKFLOWS["media_production"]` — runs only on `publishable` ideas via `services/production.py`

### Planned Engines (registered, not implemented)

| Key | Module | Future Role |
|---|---|---|
| `voice` | `engines/voice.py` | Standalone TTS generation engine (superseded in part by `narration`) |
| `image` | `engines/image.py` | AI image generation from visual prompts |
| `video` | `engines/video.py` | AI video generation / assembly |
| `publishing` | `engines/publishing.py` | Auto-post to YouTube, TikTok, Instagram, X |
| `analytics` | `engines/analytics.py` | Performance tracking and reporting |
| `learning` | `engines/learning.py` | Mines Knowledge Base to improve prompts and strategy |

Planned engines return `{"{key}_status": "not_implemented"}` and are skipped when `is_ready() == False`.

### Adding a New Engine

1. Create `engines/my_engine.py` with an `Engine` subclass
2. Register in `engines/__init__.py`
3. Append key to the appropriate `WORKFLOWS[...]` list in `core/workflows.py`
4. Add tests in `tests/test_engines.py` or a dedicated test file
5. Update production dashboard stage defs in `services/production.py` if user-visible

---

## 6. Provider System

Providers live in `providers/` and implement abstract interfaces in `providers/base.py`. **Engines and services call factories — never vendor SDKs.**

### Provider Categories

| Category | Interface | Factory | Implementations |
|---|---|---|---|
| LLM | `providers/llm.py` | `get_llm_provider()` | `core/ai/openai_provider.py`, `core/ai/demo_provider.py` |
| Research sources | `providers/research_source.py` | `get_research_source_providers()` | wikipedia, pubmed, arxiv, crossref (live); news, trends, youtube, reddit, tiktok (placeholder) |
| Trend sources | `providers/trend_sources/base.py` | `get_trend_providers()` — **auto-discovered** | google_trends, youtube_trending, tiktok_trends, reddit_trends, rss_feeds, news_api, keyword_api (placeholders) |
| Voice | `providers/voice/base.py` | `get_voice_provider(mode)` | demo_ai, recorded, clone (stub) |
| Image | `providers/image_provider.py` | *(stub)* | — |
| Video | `providers/video_provider.py` | *(stub)* | — |
| Music | `providers/music_provider.py` | *(stub)* | — |
| SEO | `providers/seo_provider.py` | *(stub)* | engines use LLM directly today |
| Publishing | `providers/publishing_provider.py` | *(stub)* | — |
| Analytics | `providers/analytics_provider.py` | *(stub)* | — |
| Trend | `providers/trend_provider.py` | *(stub)* | — |

### Research Source Provider Contract

Every research provider implements:

```python
class ResearchSourceProvider(Provider):
    key: str
    label: str

    def is_available(self) -> bool: ...
    def search(self, topic: str, niche: str = "", limit: int = 3) -> list[ResearchDocument]: ...
```

Returns normalized `ResearchDocument` objects regardless of upstream API shape. The UI **never** displays which provider supplied data.

### Trend Source Provider Contract (v7.0)

```python
class TrendSourceProvider(ABC):
    key: str        # registry key
    label: str      # human-readable name
    platform: str   # where the signal comes from

    def is_available(self) -> bool: ...
    def discover(self, topic, category="general", country="US",
                 language="en", limit=3) -> list[Trend]: ...
```

Returns universal `Trend` objects (topic, keywords, growth %, search volume,
velocity, competition, freshness, category, country, language, platform,
source, timestamp, confidence). The registry in
`providers/trend_sources/__init__.py` **scans the package automatically** —
adding a provider is dropping one module into the folder. No registration
code, no imports to edit.

### Voice Provider Contract

Three modes via `VoiceMode`:

| Mode | Provider | Status |
|---|---|---|
| `ai` | `DemoAIVoiceProvider` | Live (demo) |
| `recorded` | `RecordedVoiceProvider` | Live (metadata + file paths) |
| `clone` | `CloneVoiceProvider` | Architecture stub only |

### Adding a New Provider

**Research source:**
1. Create `providers/my_source.py` implementing `ResearchSourceProvider`
2. Register in `providers/__init__.py` → `_load_research_sources()`
3. Add key to `RESEARCH_PROVIDERS` in `core/constants.py`
4. Add tests in `tests/test_research_engine.py`

**Trend source:**
1. Create `providers/trend_sources/my_source.py` implementing `TrendSourceProvider`
2. Done — the registry auto-discovers it. Add a test in `tests/test_trend_discovery.py`

**Other capability:**
1. Implement the ABC in `providers/`
2. Add factory function in `providers/__init__.py`
3. Wire engine to call factory — never import vendor SDK in engine code

---

## 7. Services Layer

Services are the public API between UI and infrastructure.

| Service | Module | Role |
|---|---|---|
| Ideation | `services/ideation.py` | Runs intelligence pipeline + production; records to Knowledge Base |
| Production | `services/production.py` | Runs media_production workflow; builds production dashboard |
| Research | `services/research/` | Knowledge Engine — manager, cache, scorer, summarizer, models |
| Trends | `services/trends/` | Trend Discovery — universal Trend model, 11-factor opportunity scorer, discovery manager |
| Assets | `services/assets.py` | Asset registry + publishing queue persistence |
| Voice Profiles | `services/voice_profiles.py` | Profile CRUD, recording metadata, style presets |
| Knowledge | `services/knowledge.py` | Append-only JSON memory (hooks, titles, scripts, research briefs) |
| Channels | `services/channels.py` | Multi-brand/account configuration |
| Pipeline | `services/pipeline.py` | Stage views for UI from engine registry |

### Knowledge Engine Internals (`services/research/`)

| Module | Role |
|---|---|
| `manager.py` | Orchestrates full research flow; entry point for Research engine |
| `models.py` | `ResearchDocument`, `ResearchIntent`, `ResearchSummary`, `ResearchSettings`, `ResearchBundle` |
| `cache.py` | Topic-level cache with TTL (`data/research_cache/`) |
| `scorer.py` | Authority, freshness, popularity, scientific reliability, citations, relevance |
| `summarizer.py` | Executive summary, facts, stats, myths, contrarian ideas, Q&A, trends |
| `citation.py` | Script-to-source mapping, claim confidence, fact-check notes |

---

## 8. Data & Persistence

All runtime data lives under `data/` (gitignored except `.gitkeep` files).

| Path | Contents |
|---|---|
| `data/projects/` | Saved project JSON files |
| `data/projects/{slug}/knowledge/` | Per-project research artifacts |
| `data/knowledge/` | Global Knowledge Base (hooks, titles, scripts, research briefs) |
| `data/research_cache/` | Topic-level research cache |
| `data/assets/` | Asset registry index |
| `data/voice_profiles/` | Voice profile metadata |
| `data/voice_recordings/` | User narration recordings |
| `data/publishing_queue/` | Queued render packages |
| `data/channels/` | Channel configurations |
| `data/logs/` | Structured runtime logs |

### Key Data Models

| Model | Location | Purpose |
|---|---|---|
| Result / Project dict | `core/models.py` | Session and persisted project shape |
| Production models | `core/production_models.py` | Scene, Timeline, RenderPackage, VoiceProfile, Asset |
| Research models | `services/research/models.py` | ResearchDocument, ResearchSummary, ResearchBundle |

---

## 9. UI Contract

The Streamlit UI is intentionally stable across versions. Major releases add **compact panels and settings** — not new pages or layout redesigns.

### Tabs (fixed since v1.0)

| Tab | Module | Purpose |
|---|---|---|
| Ideas | `ui/tabs/ideas.py` | Command input, pipeline run, breakdown, idea cards |
| Scripts | `ui/tabs/scripts.py` | Copy-friendly script view |
| Projects | `ui/tabs/projects.py` | Save / open / delete projects |
| Publishing | `ui/tabs/publishing.py` | Platform placeholders + roadmap |
| Analytics | `ui/tabs/analytics.py` | Session metrics + roadmap |
| Settings | `ui/tabs/settings.py` | API key, model, voice, research, quality gate, diagnostics |

### UI Rules for Future Versions

- Do not add new top-level tabs without explicit product decision
- Do not move business logic into `ui/` — call `services/` only
- Settings additions go as new sections within the existing Settings tab
- Pipeline progress uses `components.production_dashboard()` — extend, don't replace

---

## 10. Version Roadmap

### Shipped

| Version | Commit theme | Key deliverable |
|---|---|---|
| **v1.0** | AI Command Center | Streamlit workspace, OpenAI integration, demo mode, project saving |
| **v1.1** | Autonomous OS foundation | Job queue, engine registry, workflows, channels, knowledge base, tests |
| **v2.0** | Intelligence Pipeline | 9-stage reasoning: research → ideation → psychology → ranking → script → critic → revision → SEO → quality |
| **v4.0** | Media Production Engine | 8-stage production pipeline, voice architecture, render packages, production dashboard |
| **v5.0** | Knowledge Engine | Multi-source research, source scoring, cache, traceability, research settings |
| **v6.0** | Real Research + Citation | Live Wikipedia/PubMed/arXiv/Crossref APIs, Citation Engine, multi-factor quality gate |
| **v7.0** | Trend Discovery Engine | Auto-discovered trend provider registry, universal Trend model, 11-factor Opportunity Scoring, pipeline front door, Trend Dashboard |
| **v7.1** | Psychology & Virality Engine | 18-dimension attention scoring, weighted ViralScore, per-idea psychology report, virality-aware Quality Gate |

*(v3.0 was skipped in release numbering.)*

### Planned

| Version | Focus | Dependencies |
|---|---|---|
| **v7.x** | Live trend APIs | Google Trends, YouTube Data, TikTok, Reddit HTTP clients behind the existing `TrendSourceProvider` interface — per-file swaps, no pipeline changes |
| **v8.0** | Render engine (Image → Animation → Video) | Consume `RenderPackage`; ffmpeg or cloud renderer; image/video providers |
| **v9.0** | Publishing automation | YouTube/TikTok/Instagram providers; publishing queue → live posts; per-channel credentials |
| **v10.0** | Analytics + Learning Engine | Performance ingestion; Learning engine mines Knowledge Base; feedback into ranking/prompts |
| **v11.0** | Multi-brand autonomy | Business entity model; per-brand pipelines, scheduling, and learning history |

### Long-Term Vision

Generational becomes the operating system for a portfolio of AI-powered media companies — researching, creating, publishing, analyzing, and improving high-quality content at scale:

- Many independent brands, each with its own channels, voice, visual identity, audience, posting schedule, SEO profile, psychology profile, revenue, analytics, and learning history
- Continuous learning from analytics feeding back into every pipeline stage
- Self-improving prompts, ranking weights, and channel strategy
- High-quality video across science, finance, psychology, history, tech, and current events
- Zero vendor lock-in at every layer
- Human involvement limited to approvals and strategic decisions

### Multi-brand data model (target)

Each **Business** aggregates: brand identity, channels, voice profiles, visual identity, audience definition, posting schedule, SEO profile, psychology profile, revenue tracking, analytics, and learning history. `services/channels.py` is the seed of this model; it grows into a full business entity without breaking existing channel data.

### Future feature classes (design for now, build later)

Architecture must absorb these without major refactoring:

- AI voice clone (owner's voice, with authorization) — `providers/voice/clone.py` stub already exists
- AI-assisted reaction video workflows using owner recordings
- Podcast generation, long-form YouTube, blog and newsletter generation
- Social media repurposing, translation, multi-language publishing
- Affiliate automation, sponsorship management, merchandise, course creation, community management

Each maps to either a new engine (registered stub first), a new provider interface, or a new workflow definition — never a rewrite of orchestration.

---

## 11. Testing Rules

### Running Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

### Test Structure

| File | Covers |
|---|---|
| `tests/conftest.py` | Isolated tmp fixtures — never touches real `data/` |
| `tests/test_engines.py` | Registry completeness, live vs planned engines |
| `tests/test_workflows.py` | Context merging, skip/fail behavior, job queue |
| `tests/test_intelligence_pipeline.py` | End-to-end intelligence pipeline |
| `tests/test_psychology_engine.py` | Psychology & Virality Engine — 18 dimensions, ViralScore weights, determinism, report shape, pipeline integration |
| `tests/test_citation_engine.py` | Citation engine + multi-factor quality gate |
| `tests/test_trend_discovery.py` | Trend provider auto-discovery, universal model, opportunity scoring, pipeline integration |
| `tests/test_media_production.py` | Production pipeline and dashboard |
| `tests/test_providers.py` | Voice provider factory |
| `tests/test_knowledge.py` | Knowledge Base CRUD |
| `tests/test_models.py` | Result/project round-trip |
| `tests/test_parsing.py` | Command parsing |
| `tests/test_jobs.py` | Job queue |
| `tests/test_storage.py` | Project store |
| `tests/test_channels.py` | Channel manager |
| `tests/test_diagnostics.py` | Health checks |
| `tests/test_ai_providers.py` | LLM provider selection |

### Testing Rules

1. **No real `data/`** — always use `tmp_path` fixtures from `conftest.py`
2. **Demo mode by default** — tests run without `OPENAI_API_KEY`
3. **Deterministic scoring** — psychology, ranking, quality must be reproducible
4. **Provider failures** — test graceful fallback when all providers fail
5. **Context contract** — assert backward-compatible `research` fields after engine changes
6. **New engines** — add to `LIVE_KEYS` or `PLANNED_KEYS` in `test_engines.py`
7. **New providers** — add factory test + at least one search/normalization test
8. **No trivial tests** — don't assert the obvious; test real behavior and edge cases
9. **Run full suite before version commit** — all tests must pass

### Current Baseline

**103 tests passing** (as of v7.1.0).

---

## 12. Git Workflow

### Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Stable, version-tagged releases |
| `feature/*` | Optional feature branches for large changes |

### Commit Message Format

```
vX.Y.Z Short description of why this release exists

Optional longer body explaining architectural impact.
```

Examples from history:

```
v5.0.0 Knowledge Engine: multi-source research platform grounds every video in vetted data
v4.0.0 Autonomous Media Production Engine: auto-build render packages from approved scripts
v2.0.0 Intelligence Pipeline: 9-stage AI reasoning replaces single-shot generation
```

### Commit Rules

- Only commit when explicitly requested
- Never `--force` push to `main`
- Never skip hooks (`--no-verify`)
- Never amend pushed commits unless explicitly requested
- Never commit secrets (`.env`, API keys)
- Run tests before committing a version release

### Push

```bash
git push origin main
```

Requires GitHub authentication on the developer machine (HTTPS keychain or SSH).

### Pull Requests

For multi-commit features:

```bash
git push -u origin HEAD
gh pr create --title "..." --body "..."
```

---

## 13. Future Modules

These modules are architecturally anticipated but not yet implemented.

### Live Trend APIs (v7.x)

- **Change:** Replace demo data in `providers/trend_sources/*.py` with real HTTP clients
- **No pipeline changes** — same `discover()` interface, same universal `Trend` output

### Render Engine (v8.0)

- **Input:** `RenderPackage` from `data/publishing_queue/`
- **Output:** Final MP4/WebM file
- **Location:** `engines/video.py` (upgrade from PlannedEngine) + `providers/video_provider.py`
- **Integration:** New workflow step or post-production job type

### Publishing Automation (v8.0)

- **Input:** Render package + platform credentials from `services/channels.py`
- **Output:** Published post URLs, publishing history in Knowledge Base
- **Providers:** YouTube, TikTok, Instagram, X implementations of `PublishingProvider`

### Analytics Ingestion (v9.0)

- **Input:** Platform analytics APIs
- **Output:** Performance rows in `CATEGORY.PERformance` Knowledge Base
- **Consumer:** Learning engine improves prompts, ranking weights, niche strategy

### Learning Engine (v9.0)

- **Input:** Knowledge Base (hooks, titles, scripts, performance, research briefs)
- **Output:** Prompt improvements, winning pattern extraction, channel recommendations
- **Location:** `engines/learning.py` (upgrade from PlannedEngine)

### Multi-Channel UI (v10.0)

- **Input:** `services/channels.py` data
- **Output:** Channel switcher, per-channel pipelines, autonomous scheduling
- **Constraint:** Add to sidebar or Settings — no new top-level tab without product decision

### Live Research APIs (v6.0)

- **Change:** Replace demo data in `providers/wikipedia.py`, `pubmed.py`, etc. with real HTTP clients
- **No pipeline changes** — same `search()` interface, same `ResearchDocument` output

### Real TTS Providers

- **Change:** Implement `OpenAIVoiceProvider`, `ElevenLabsVoiceProvider` behind `VoiceProvider`
- **No engine changes** — `engines/narration.py` already calls `get_voice_provider()`

---

## 14. Extension Points

Quick reference for common extensions:

| Goal | Action |
|---|---|
| Add research provider | New file in `providers/` + register in `_load_research_sources()` + add to `RESEARCH_PROVIDERS` |
| Add trend provider | Drop a `TrendSourceProvider` module into `providers/trend_sources/` — auto-discovered |
| Add pipeline stage | New engine module + register in `engines/__init__.py` + append to `WORKFLOWS` |
| Add voice backend | Implement `VoiceProvider` + register in `get_voice_provider()` |
| Add storage backend | Implement `core/storage/base.py` `ProjectStore` |
| Add workflow | New key in `WORKFLOWS` dict in `core/workflows.py` |
| Add knowledge category | New constant in `services/knowledge.py` `CATEGORY` |
| Add UI setting | New key in `core/state.py` `DEFAULTS` + control in `ui/tabs/settings.py` |
| Build renderer | Read `RenderPackage` objects from publishing queue |
| Build auto-poster | Implement `PublishingProvider` + wire `engines/publishing.py` |

---

## Appendix: File Map

```
generational/
├── app.py                          # Streamlit entry (orchestration only)
├── MASTER_ARCHITECTURE.md          # This document
├── README.md                       # User-facing documentation
├── core/
│   ├── constants.py                # APP_VERSION, research settings, niches
│   ├── models.py                   # Result/project dict shapes
│   ├── production_models.py        # Scene, Timeline, RenderPackage, VoiceProfile
│   ├── workflows.py                # WORKFLOWS definitions + WorkflowEngine
│   ├── jobs.py                     # Job queue
│   ├── state.py                    # Streamlit session defaults
│   ├── parsing.py                  # Command parsing
│   ├── log.py · diagnostics.py
│   ├── ai/                         # LLM providers (OpenAI + demo)
│   └── storage/                    # JSON project store
├── services/
│   ├── ideation.py                 # Intelligence + production orchestrator
│   ├── production.py               # Media production orchestrator
│   ├── research/                   # Knowledge Engine
│   ├── trends/                     # Trend Discovery (models, scorer, manager)
│   ├── assets.py · voice_profiles.py
│   ├── knowledge.py · channels.py · pipeline.py
├── engines/                        # 20 live + 6 planned pipeline plugins
├── providers/                      # Swappable external backends
│   └── trend_sources/              # Auto-discovered trend providers
├── ui/                             # Streamlit presentation
├── tests/                          # 90 unit/integration tests
└── data/                           # Runtime persistence (gitignored)
```

---

*Last updated: v7.1.0 — Psychology & Virality Engine*
