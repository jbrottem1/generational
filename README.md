# 🚀 Generational

**AI Content Operating System**

Generational is an AI-powered faceless content operating system designed to help creators generate, produce, and distribute content at scale.

## Version 2.0 — Intelligence Pipeline

v2.0 replaces single-shot generation with a 9-stage AI reasoning pipeline.
Every command now flows through:

1. **Research** — topic context, audience, search intent, trend strength, research summary
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
- The top-ranked ideas (of 20 candidates), each with hook, script, CTA, hashtags, keywords, description, thumbnail concept, critic notes, and all six quality scores
- The publish gate verdict per video, and the remaining production steps: Voice → Image → Video → Publish

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

Generational v1.1 is the foundation of an autonomous, multi-account content
operating system. The Streamlit UI is a thin shell over four layers:

```
        UI (Streamlit tabs + sidebar)
                    │
        services/  (ideation, channels, knowledge, pipeline views)
                    │
   Job Queue ──► Workflow Engine ──► Engine Registry (plugins)
                    │
        core/  (AI providers, storage, models, logging, diagnostics)
```

### Job Queue (`core/jobs.py`)
Every unit of work is a Job with a type, payload, status, and timing.
Handlers are registered per job type. Execution is synchronous today
(Streamlit's model), but callers only depend on submit/run semantics — a
background worker can drain the queue later with zero caller changes.
Running a command in the Ideas tab already flows through the queue.

### Engine plugins (`engines/`)
Each pipeline capability is an Engine plugin registered in
`engines/registry.py`. Nine are live — **Research, Ideation, Psychology,
Ranking, Script, Critic, Revision, SEO, and Quality** — with **Voice,
Image, Video, Publishing, Analytics, and Learning** registered as planned
stubs. An engine receives the shared workflow context and returns updates
to it. Implementing a stage = overriding `run()` and `is_ready()` in its
module; workflows, diagnostics, and the pipeline UI pick it up
automatically. Generative engines call the AI provider through a single
`generate_json` interface and fall back to deterministic heuristics, so
providers/models swap without touching engine code.

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
- **New AI provider** (e.g. Anthropic, local models): implement
  `core/ai/base.py`'s `AIProvider` and register it in `core/ai/__init__.py`.
- **New storage backend** (e.g. SQLite, Postgres): implement
  `core/storage/base.py`'s `ProjectStore` (projects) or mirror
  `core/storage/json_collection.py` (named records) and swap it in.

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
│   ├── ai/                   # AI provider abstraction
│   │   ├── base.py           # AIProvider interface
│   │   ├── openai_provider.py# OpenAI backend (falls back gracefully)
│   │   ├── demo_provider.py  # Placeholder content, no API needed
│   │   └── __init__.py       # Provider selection (get_provider)
│   └── storage/              # Storage abstraction
│       ├── base.py           # ProjectStore interface
│       ├── json_store.py     # Local JSON project backend
│       ├── json_collection.py# Generic named-record JSON store
│       └── __init__.py       # Storage facade (get_store + helpers)
├── engines/                  # Engine plugins (one per pipeline capability)
│   ├── base.py               # Engine / PlannedEngine interfaces
│   ├── registry.py           # Engine registry (register / get / ready)
│   ├── heuristics.py         # Deterministic text-analysis helpers (demo + scoring)
│   ├── research.py           # LIVE: context, audience, intent, trend strength
│   ├── ideation.py           # LIVE: 20 candidate concepts
│   ├── psychology.py         # LIVE: 6-dimension virality scoring
│   ├── ranking.py            # LIVE: weighted ranking + selection
│   ├── script.py             # LIVE: scripts for top concepts only
│   ├── critic.py             # LIVE: adversarial script review
│   ├── revision.py           # LIVE: auto-rewrite of flagged sections
│   ├── seo.py                # LIVE: titles, hashtags, keywords, descriptions
│   ├── quality.py            # LIVE: final scores + publish-threshold gate
│   └── voice|image|video|publishing|analytics|learning.py  # planned stubs
├── services/                 # Business services
│   ├── ideation.py           # Public ideation API (job queue → workflow → engine)
│   ├── pipeline.py           # Pipeline stage views for the UI (from registry)
│   ├── channels.py           # Channel Manager (multi-brand/account)
│   └── knowledge.py          # Knowledge Base (hooks, titles, scripts, SEO, ...)
├── ui/                       # Presentation layer (Streamlit only)
│   ├── styles.py             # CSS injection (dark theme, cards, animations)
│   ├── notify.py             # Success/error toast helpers
│   ├── components.py         # Reusable components (idea card, pipeline flow, ...)
│   ├── sidebar.py            # AI Command Center sidebar
│   └── tabs/                 # One module per workspace tab
│       ├── ideas.py, scripts.py, projects.py
│       └── publishing.py, analytics.py, settings.py
├── tests/                    # Unit tests for every core service
└── data/                     # Local persistence (gitignored)
    ├── projects/             # Saved projects
    ├── channels/             # Channel configurations
    ├── knowledge/            # Knowledge base categories
    └── logs/                 # Runtime logs
```

## Roadmap

- 🎙️ AI Voice Generation
- 🎬 AI Video Creation
- 🔍 SEO Optimizer
- 📤 Auto Posting
- 📊 Full Analytics Dashboard
