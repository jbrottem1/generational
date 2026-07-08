# 🚀 Generational

**AI Content Operating System**

Generational is an AI-powered faceless content operating system designed to help creators generate, produce, and distribute content at scale.

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
Placeholder platform connection cards (YouTube Shorts, TikTok, Instagram Reels, X) plus a roadmap for Auto Posting, AI Voice Generation, and AI Video Creation.

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

## Architecture

Generational v5.0 is an autonomous content operating system. The Streamlit UI
is a thin shell over five layers:

```
        UI (Streamlit tabs + sidebar)
                    │
        services/  (research, ideation, production, assets, voice profiles, channels, knowledge)
                    │
   Job Queue ──► Workflow Manager ──► Engine Registry (18 live plugins)
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
**18 live engines** across two pipelines. Intelligence (10): Research, Ideation,
Psychology, Ranking, Script, Critic, Revision, Citation, SEO, Quality. Production (8):
Scene Planning, Narration, Visual Planning, Asset Manager, Subtitle, Timeline,
Render Package, Publishing Queue. Future render engines (Voice/Image/Video
generation) remain as planned stubs.

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
- **Renderer**: consume `RenderPackage` objects from `data/publishing_queue/`.

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
│   ├── llm.py, voice/, image_provider.py, video_provider.py, music_provider.py
│   └── publishing_provider.py, analytics_provider.py, trend_provider.py
├── engines/                  # Engine plugins (intelligence + production)
│   ├── research … quality.py # Intelligence pipeline (9 live)
│   ├── scene_planning … publishing_queue.py  # Media production (8 live)
│   └── voice|image|video|publishing|analytics|learning.py  # future render stubs
├── services/
│   ├── research/             # Knowledge Engine (manager, cache, scorer, summarizer)
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
    └── publishing_queue/     # Queued render packages
```

## Roadmap

- 🌐 Live API integrations for research providers (Wikipedia, PubMed, arXiv APIs)
- 🎬 Video/image generation from visual prompts (providers wired, engines stubbed)
- 🎙️ Real TTS providers (ElevenLabs, OpenAI) behind VoiceProvider
- 🧬 Voice cloning provider
- 📤 Auto Posting from publishing queue
- 📊 Full Analytics Dashboard + Learning loop (mines Knowledge Base + research)
