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

## Project Structure

```
generational/
├── app.py                  # Main entry point — wires sidebar + tabs together
├── requirements.txt        # Python dependencies
├── .env.example            # Template for your OpenAI API key
├── .streamlit/
│   └── config.toml         # Dark theme configuration
├── core/                   # Business logic (no UI code)
│   ├── constants.py        # Niches, models, pipeline steps, example commands
│   ├── parsing.py          # Command parsing (niche/count/subject detection)
│   ├── ai.py                # OpenAI generation + Demo Mode fallback
│   ├── storage.py          # Local JSON project persistence
│   └── state.py            # Streamlit session state helpers
├── ui/                      # Presentation layer
│   ├── styles.py            # CSS injection (dark theme, cards, animations)
│   ├── notify.py            # Success/error toast helpers
│   ├── sidebar.py           # AI Command Center sidebar
│   ├── tab_ideas.py         # Ideas tab (command center)
│   ├── tab_scripts.py       # Scripts tab
│   ├── tab_projects.py      # Projects tab (create/save/open/delete)
│   ├── tab_publishing.py    # Publishing tab
│   ├── tab_analytics.py     # Analytics tab
│   └── tab_settings.py      # Settings tab
└── data/
    └── projects/             # Saved projects (JSON, gitignored)
```

## Roadmap

- 🎙️ AI Voice Generation
- 🎬 AI Video Creation
- 🔍 SEO Optimizer
- 📤 Auto Posting
- 📊 Full Analytics Dashboard
