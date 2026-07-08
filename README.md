# 🚀 Generational

**AI Content Operating System**

Generational is an AI-powered faceless content operating system designed to help creators generate, produce, and distribute content at scale.

## Version 1.0 — AI Command Center

v1.0 upgrades the original idea generator into a full AI Command Center workspace:

- **Real AI generation** — when an `OPENAI_API_KEY` is available, Generational calls OpenAI to generate real viral hooks, titles, 15-30s scripts, CTAs, hashtags, and thumbnail concepts. Without a key, it automatically falls back to **Demo Mode** with clean placeholder content — the app never crashes.
- **Workspace tabs** — Ideas, Scripts, Projects, Publishing, Analytics, and Settings.
- **Project saving** — Create, Save, Open, and Delete projects, persisted locally as JSON files under `data/projects/`.
- **AI sidebar** — always-visible API status, active model, app version, ideas generated, projects saved, and token usage.
- **Polished dark UI** — custom theme, cards, spacing, loading spinners, and success/error notifications.

## Features

### 💡 Ideas
Type a natural language command (e.g. *"Create 10 psychology shorts about procrastination"*), or click an example to auto-fill the command box. Running the command shows:
- Detected niche, videos requested, and content goal
- 10 generated ideas (hook, script, CTA, hashtags, thumbnail concept)
- The next pipeline steps: Research → SEO → Script → Voice → Visuals → Edit → Publish

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

Generational is built in three layers so it can grow into a multi-account
autonomous content operating system without rewrites:

- **`core/`** — foundations: config, data models, logging, and swappable
  abstractions for AI providers and storage backends.
- **`services/`** — pipeline stages. Ideation is live today; research, SEO,
  voice, video, publishing, analytics, and self-improvement each get their
  own service module here and register in the pipeline stage registry.
- **`ui/`** — Streamlit presentation only. Tabs render state and call
  services; reusable pieces live in `ui/components.py`.

Key extension points:

- **New AI provider** (e.g. Anthropic, local models): implement
  `core/ai/base.py`'s `AIProvider` and register it in `core/ai/__init__.py`.
- **New storage backend** (e.g. SQLite, Postgres): implement
  `core/storage/base.py`'s `ProjectStore` and swap it in
  `core/storage/__init__.py`.
- **New pipeline stage**: add a module under `services/` and flip the stage
  to available in `services/pipeline.py`.

## Project Structure

```
generational/
├── app.py                    # Main entry point — wires sidebar + tabs together
├── requirements.txt          # Python dependencies
├── .env.example              # Template for your OpenAI API key
├── .streamlit/
│   └── config.toml           # Dark theme configuration
├── core/                     # Foundations (no UI code)
│   ├── constants.py          # App config: niches, models, example commands
│   ├── models.py             # Canonical result/project data shapes
│   ├── parsing.py            # Command parsing (niche/count/subject detection)
│   ├── state.py              # Streamlit session state helpers
│   ├── log.py                # Central logging (console + data/logs/)
│   ├── ai/                   # AI provider abstraction
│   │   ├── base.py           # AIProvider interface
│   │   ├── openai_provider.py# OpenAI backend (falls back gracefully)
│   │   ├── demo_provider.py  # Placeholder content, no API needed
│   │   └── __init__.py       # Provider selection (get_provider)
│   └── storage/              # Storage abstraction
│       ├── base.py           # ProjectStore interface
│       ├── json_store.py     # Local JSON backend
│       └── __init__.py       # Storage facade (get_store + helpers)
├── services/                 # Pipeline stages (business orchestration)
│   ├── ideation.py           # Command → parsed intent → generated content
│   └── pipeline.py           # Stage registry (research, SEO, voice, video, ...)
├── ui/                       # Presentation layer (Streamlit only)
│   ├── styles.py             # CSS injection (dark theme, cards, animations)
│   ├── notify.py             # Success/error toast helpers
│   ├── components.py         # Reusable components (idea card, pipeline flow, ...)
│   ├── sidebar.py            # AI Command Center sidebar
│   └── tabs/                 # One module per workspace tab
│       ├── ideas.py          # Ideas tab (command center)
│       ├── scripts.py        # Scripts tab
│       ├── projects.py       # Projects tab (create/save/open/delete)
│       ├── publishing.py     # Publishing tab
│       ├── analytics.py      # Analytics tab
│       └── settings.py       # Settings tab
└── data/
    ├── projects/             # Saved projects (JSON, gitignored)
    └── logs/                 # Runtime logs (gitignored)
```

## Roadmap

- 🎙️ AI Voice Generation
- 🎬 AI Video Creation
- 🔍 SEO Optimizer
- 📤 Auto Posting
- 📊 Full Analytics Dashboard
