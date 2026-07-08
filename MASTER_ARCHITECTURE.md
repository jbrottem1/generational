# Generational — Master Architecture

**Current version:** v6.0.0  
**Status:** Source-backed research platform with citation engine and multi-factor quality gate  
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

Generational is an autonomous AI content operating system designed to manage multiple social media brands at scale. It is **not** a collection of scripts — it is a modular platform with:

- A **Knowledge Engine** with live Wikipedia, PubMed, arXiv, and Crossref connectors
- A **Citation Engine** that maps scripts to sources and flags unsupported claims
- An **Intelligence Pipeline** (10 stages) through ideas, psychology, scripts, critique, citation, SEO, and quality
- A **Media Production Pipeline** that turns approved scripts into render-ready packages
- A **Provider System** that keeps all vendor integrations swappable
- A **Job Queue + Workflow Engine** that coordinates every stage without tight coupling

### Design Principles

| Principle | Meaning |
|---|---|
| Modularity | Each capability is an isolated engine or service |
| Provider-agnostic | Business logic never imports OpenAI, ElevenLabs, etc. directly |
| Composition over inheritance | Small modules, shared context dict, no god classes |
| UI separation | Streamlit is a thin shell; logic lives in `services/` and `engines/` |
| Fail-safe | Demo/heuristic fallbacks when AI or providers fail — never crash |
| Strong typing at boundaries | `core/models.py`, `core/production_models.py`, `services/research/models.py` |
| Testability | Every service has unit tests; tests never touch real `data/` |

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
│  18 live engines · 6 planned stubs                           │
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
    │   Stage 1: Research (Knowledge Engine)
    │       services/research/manager.py
    │       → parse intent
    │       → query enabled research providers
    │       → normalize ResearchDocument objects
    │       → score + filter weak sources
    │       → generate structured ResearchSummary
    │       → cache by topic (data/research_cache/)
    │       │
    │       ▼
    │   Stages 2–10: Intelligence Pipeline
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
| `research` | Research | Ideation, Script, Quality, UI |
| `research_references` | Research | Script (traceability) |
| `candidates` | Ideation | Psychology, Ranking |
| `ranked_candidates`, `selected_ideas` | Ranking | Script, SEO, Quality |
| `ideas` | Quality | Production, UI, Knowledge Base |
| `quality_summary` | Quality | UI, Production filter |
| `approved_content` | Production service | Media production engines |
| `production_packages` | Production service | UI, project persistence |

**Rule:** Never break backward-compatible keys in `context["research"]` (`topic_context`, `audience`, `search_intent`, `trend_strength`, `summary`, `opportunity_score`).

---

## 4. Development Workflow (ChatGPT + Claude + Cursor)

Generational is developed using a three-tool workflow. Each tool has a distinct role; overlap is intentional but bounded.

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

### Intelligence Pipeline (10 live engines)

| Key | Module | Responsibility |
|---|---|---|
| `research` | `engines/research.py` | Knowledge Engine — live APIs + demo fallback; produces Research Brief |
| `ideation` | `engines/ideation.py` | Generates 20 candidate concepts grounded in research brief |
| `psychology` | `engines/psychology.py` | Scores candidates on 6 virality dimensions (deterministic) |
| `ranking` | `engines/ranking.py` | Weighted ranking; selects top N for scripting |
| `script` | `engines/script.py` | Writes 15–30s voiceover scripts from research facts |
| `critic` | `engines/critic.py` | Adversarial review — flags weak hooks, repetition, pacing |
| `revision` | `engines/revision.py` | Auto-rewrites flagged sections |
| `citation` | `engines/citation.py` | Maps scripts to sources; claim confidence; unsupported claim warnings |
| `seo` | `engines/seo.py` | Titles, hashtags, keywords, description, thumbnail concept |
| `quality` | `engines/quality.py` | Multi-factor publish gate (score + research + citations) |

**Workflow:** `WORKFLOWS["intelligence"]`

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

*(v3.0 was skipped in release numbering.)*

### Planned

| Version | Focus | Dependencies |
|---|---|---|
| **v7.0** | Trend API integrations | Google Trends, YouTube, Reddit, TikTok live APIs |
| **v8.0** | Render engine | Consume `RenderPackage`; ffmpeg or cloud renderer |
| **v8.0** | Publishing automation | YouTube/TikTok/Instagram providers; publishing queue → live posts |
| **v9.0** | Analytics + Learning | Performance ingestion; Learning engine mines Knowledge Base |
| **v10.0** | Multi-channel autonomy | Channel manager UI; scheduled autonomous content for dozens of brands |

### Long-Term Vision

Generational becomes a fully autonomous content operating system:

- Dozens of independent social media channels
- Continuous learning from analytics
- Self-improving prompts and strategy
- High-quality video across science, finance, psychology, history, tech, and current events
- Zero vendor lock-in at every layer

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
| `tests/test_citation_engine.py` | Citation engine + multi-factor quality gate |
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

**77 tests passing** (as of v6.0.0).

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

### Render Engine (v7.0)

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
│   ├── assets.py · voice_profiles.py
│   ├── knowledge.py · channels.py · pipeline.py
├── engines/                        # 18 live + 6 planned pipeline plugins
├── providers/                      # Swappable external backends
├── ui/                             # Streamlit presentation
├── tests/                          # 72+ unit/integration tests
└── data/                           # Runtime persistence (gitignored)
```

---

*Last updated: v6.0.0 — Real Research + Citation Engine*
