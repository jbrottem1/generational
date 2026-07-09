# 🚀 Generational

**AI Content Operating System**

Generational is an AI-powered faceless content operating system designed to help creators generate, produce, and distribute content at scale.

## Version 7.5 — Visual Intelligence Engine

The visual brain of the pipeline. Every scripted candidate now receives a
complete **Visual Production Package** — the canonical visual plan that
every downstream renderer (voice, audio, image, video) will consume. No
final videos are generated yet; this is the planning system that makes
generation possible.

### Visual Production Package (`services/visual/` + `engines/visual_intelligence.py`)

Each package contains:

- **Scene-by-scene storyboard** — hook, pattern interrupt, curiosity loop,
  story beats sized to runtime (~one visual change every 7s), payoff, CTA.
  Every scene carries the full visual grammar: purpose, emotion, length,
  camera angle + motion, shot composition, subject placement, lighting,
  environment, color palette, transitions in/out, motion intensity, zoom,
  background, overlay, text overlay, caption timing, sound effect, music
  style, and B-roll.
- **12-dimension visual psychology scores per scene** — Curiosity ·
  Mystery · Wonder · Fear · Beauty · Novelty · Scale · Contrast · Motion ·
  Satisfaction · Humor · Identity — blended into a per-scene Visual Score
  via `VISUAL_SCORE_WEIGHTS` (deterministic word-bank + structure analysis,
  same approach as the psychology/threat engines).
- **AI image prompts** for Midjourney, Flux, Stable Diffusion, DALL-E, and
  OpenAI Images — each carrying lighting, composition, lens, mood, art
  style, color palette, quality tags, and aspect ratio, formatted in each
  model's dialect (e.g. `--ar 9:16 --style raw --v 6` for Midjourney,
  negative prompts for Stable Diffusion).
- **AI video prompts** for Runway, Veo, Pika, Luma, Kling, and Sora
  (future-ready) — each describing the scene, camera movement, character
  actions, lighting, physics, mood, and duration.
- **5 scored thumbnail concepts** — Shock Face Close-Up, Mystery Object
  Macro, Before/After Split, Extreme Scale Contrast, Bold Text Tease —
  each scored on curiosity, readability, contrast, facial focus, object
  focus, color, and emotion, with an **expected CTR %**.
- **Hook Visualizer** — the strongest five-frame first-3-second sequence
  (abrupt motion → novel detail → curiosity gap → direct address → open
  loop) plus a plain-English scroll-stop rationale.
- **Caption plan, visual pacing report, camera plan, transitions, and
  motion report** — cut rhythm vs. the 3-8s retention ideal, camera
  variety score, and a per-scene motion intensity curve.
- One weighted **Overall Visual Score (0-100)** via
  `PACKAGE_SCORE_WEIGHTS` (scene craft 35%, hook 25%, thumbnail 20%,
  pacing 12%, camera variety 8%).

### Pipeline integration

Runs immediately after Script Generation and before the Attention Graph,
so ranking can weigh visual craft and every asset planner downstream shares
one visual source of truth:

```
... → Psychology → Script Generation
    → Visual Intelligence (storyboard + prompts + thumbnails + Visual Score)
    → Attention Graph → Ranking → ... → Quality Gate
```

Everything is deterministic — the full engine runs in Demo Mode with no API
key, and adding a new AI image/video model is one formatter function in
`services/visual/prompts.py`. Every idea card gets a compact "🎥 Visual
Production Package" expander with the storyboard, thumbnail scores, and
hook sequence.

## Version 7.4 — Threat Intelligence (Psychology Threat Detection)

Phase 3 of the attention-engineering stack. Every fully-packaged idea now
gets screened for **10 production failure modes** — the things that quietly
kill watch time, trust, or platform standing even when the underlying
psychology looks strong.

### 10 threats detected (`engines/threat_detection.py`)

Clickbait Without Payoff · Low Dopamine Pacing · Weak Hooks · Viewer
Fatigue · Thumbnail Mismatch · Predictable Scripting · Retention Cliff
Risk · Platform Policy Risk · Manipulative Language · Repetitive Content.

Each is scored 0-100 (higher = riskier) from the same deterministic
text-feature analysis used throughout the pipeline, reusing the already-
computed Psychology dimensions, script/thumbnail package, and retention
checkpoints — plus new dedicated word banks in `engines/heuristics.py` for
policy-risk and manipulative-pressure language. **Repetitive Content**
additionally compares an idea against every other idea in the same batch
to catch near-duplicate hooks/topics.

### Threat Level, Confidence, and fixes

The 10 scores blend into one weighted **Threat Score** (0-100) via
`THREAT_WEIGHTS`, mapped to a **Threat Level** (`Low` / `Medium` / `High`)
plus a **Confidence %** reflecting how much of the packaged idea (script,
thumbnail concept, retention checkpoints, CTA) was available to analyze.
Every idea card gets a compact "🚨 Threat Report" expander listing any
flagged threats with a concrete, dimension-specific fix — recommendations
are always available for all 10 dimensions, not just the flagged ones.

### Pipeline integration

Runs after SEO packaging (so the thumbnail concept and full script exist)
and before the final Quality Gate — a purely additive diagnostic layer that
doesn't change the publish-gate math:

```
... → Ranking → Script → Critic → Revision → Citation → SEO
    → Threat Detection (10 failure modes → Threat Level + Confidence + fixes)
    → Quality Gate
```

## Version 7.3 — Attention Intelligence (Attention Graph)

Phase 2 of the attention-engineering stack. Every idea now gets an
**Attention Graph** — a 12-dimension radar-chart-ready score, a single
weighted 0-100 Attention Score, and a concrete recommendation for raising
every dimension (not just the weak ones).

### 12 dimensions (`engines/attention_graph.py`)

First 3-Second Hook · Curiosity Gap · Dopenness · Emotional Intensity ·
Story Tension · Surprise · Visual Novelty · Shareability · Rewatch
Probability · Comment Likelihood · Identity Signaling · Tribal Engagement.

Nine of the twelve reuse the already-tested Phase 1 psychology dimension
scorer so the two phases stay consistent. Three are new to this phase:

- **Dopenness** — how quickly and openly the concept opens an anticipatory
  dopamine/reward loop for a broad, low-jargon audience
- **Story Tension** — turning-point language and setup/twist structure
- **Visual Novelty** — concrete, filmable transformation and reveal cues

### Attention Score + radar chart

The 12 dimensions blend into one weighted **Attention Score** (0-100) via
`ATTENTION_GRAPH_WEIGHTS`. Every idea card in the Ideas tab gets a compact
"🕸️ Attention Graph" expander with a Plotly radar chart of all 12
dimensions (falls back to a plain score list if `plotly` isn't installed)
plus a recommendation for increasing every score, sorted weakest-first.

### Pipeline integration

```
Trend Discovery → Opportunity Ranking → Research → Ideation
    → Psychology & Virality (18 dimensions → ViralScore)
    → Script Generation (multi-variant, multi-style, scored)
    → Attention Graph (12 dimensions → radar chart + recommendations)
    → Ranking → Critic → Revision → Citation → SEO → Quality Gate
```

## Version 7.2 — Script Generation Engine

v7.2 rebuilds scriptwriting into a modular **Script Generation Engine** that
runs immediately after the Psychology & Virality Engine. Instead of one
script per winning idea, every psychology-scored candidate receives multiple
stylistically distinct, platform-aware script variants — each scored 0-100 —
and the best telling wins before ranking even happens.

### Supported platforms (`services/scripts/platforms.py`)

YouTube Shorts · TikTok · Instagram Reels · Facebook Reels · X (Twitter)
video · Long-form YouTube. Each platform is a data-driven `PlatformSpec`
(runtime window, narration pacing, tone, hook window, CTA style) — adding or
tuning a platform never touches generation or scoring logic.

### Every script is a complete storytelling package

Each variant carries all thirteen components:

Hook · Pattern Interrupt · Curiosity Loop · Core Story · Emotional
Progression · Retention Checkpoints (re-hooks at the 25/50/75% drop-off
points) · Call To Action · SEO Keywords · Suggested B-roll · Suggested AI
Visual Prompts · Suggested Sound Effects · Suggested Background Music Style ·
Estimated Runtime.

### Multiple variants, scored and ranked

Four narrative archetypes compete per idea — **Authority Reveal**, **Story
First**, **Myth Bust**, **Countdown Payoff** — plus an **AI Enhanced**
variant for the strongest candidates when an OpenAI key is present. Every
variant is scored deterministically across six weighted factors (hook power,
retention engineering, emotional arc, story substance, platform fit, CTA
strength — `VARIANT_SCORE_WEIGHTS` in `services/scripts/scorer.py`), and the
winner becomes the candidate's script.

### Pipeline integration

The new `script_generation` stage runs **immediately after Psychology**, so
the Ranking engine now weighs script quality (20%) alongside psychology
(50%) and trend opportunity (30%) when selecting what gets produced:

```
Trend Discovery → Opportunity Ranking → Research → Ideation
    → Psychology & Virality (18 dimensions → ViralScore)
    → Script Generation (multi-variant, multi-style, scored)
    → Ranking → Critic → Revision → Citation → SEO → Quality Gate
```

The previous `script` stage remains as a safety-net fallback for custom
workflows — it never overwrites generated variants. As with every stage,
Demo Mode runs the entire engine deterministically without an API key.

## Version 7.1 — Psychology & Virality Engine

v7.1 turns the psychology stage into a full **attention-engineering system**.
Every candidate idea is no longer just "scored" — it is measured against 18
behavioral-science dimensions of what makes short-form content get watched,
rewatched, commented on, and shared, and it receives a plain-English report
explaining exactly why.

### 18 psychology dimensions (`engines/psychology.py`)

Curiosity Gap · Emotional Intensity · Surprise · Novelty · Fear · Humor ·
Satisfaction · Retention Potential · Replay Value · Comment Likelihood ·
Share Likelihood · Controversy (bounded by platform safety) · Visual Hook
Strength · First 3-Second Hook · Dopamine Curve · Information Density ·
Audience Identity · Community Appeal.

Each dimension is scored 0-100 with deterministic text-feature analysis
(word-bank hits, punctuation, structure, digits, hook length) — fast, free,
reproducible with or without an API key, and fully unit-tested.

### ViralScore (0-100)

The 18 dimensions blend into one weighted **ViralScore** (`VIRAL_SCORE_WEIGHTS`
in `engines/psychology.py`) — data, not code, ready for the future Learning
Engine to tune from real performance results.

### Psychology Report

Every candidate gets a `psychology_report`: a viral tier (e.g. *Strong Viral
Potential*), its top 3 strengths, its 3 weakest levers, a per-dimension note
explaining why it scored that way, and a one-line plain-English summary. The
Ideas tab shows it as a compact expander on every idea card — no new pages.

### Pipeline integration

The Psychology engine runs immediately after Ideation (which itself runs
after Trend Discovery) and before Ranking and Script Generation, so nothing
is scripted, produced, or published without first passing through the
attention model:

```
Trend Discovery → Opportunity Ranking → Research → Ideation
    → Psychology & Virality (18 dimensions → ViralScore + report)
    → Ranking → Script → Critic → Revision → Citation → SEO → Quality Gate
```

The Quality Gate now also computes a dedicated **virality** score (share,
comment, identity, community, bounded controversy) alongside publish, SEO,
psychology, retention, and CTR — so the publish gate rewards concepts built
to spread, not just to be watched once.

## Version 7.0 — Trend Discovery Engine

v7.0 makes Trend Discovery the **front door** of the operating system. Instead
of the user guessing what content to make, the system discovers opportunities
automatically before any research or generation begins.

### Trend provider layer (`providers/trend_sources/`)

Plug-and-play providers behind one interface (`TrendSourceProvider`):
Google Trends, YouTube Trending, TikTok Trends, Reddit Rising, RSS Feeds,
News APIs, and Keyword APIs (all deterministic placeholders today, live API
wiring is a per-file swap). The registry **auto-discovers** providers — adding
a source means dropping a single module into the package. No registration code.

### Universal Trend Model (`services/trends/models.py`)

Every provider normalizes into one `Trend` dataclass: topic, keywords,
growth %, search volume, velocity, competition, freshness, category, country,
language, platform, source, timestamp, and confidence. Downstream systems
consume only this model.

### Opportunity Scoring (`services/trends/scorer.py`)

Every trend receives a 0-100 **Opportunity Score** blended from eleven factors:
search demand, growth velocity, competition, historical performance, content
difficulty, monetization potential, virality potential, evergreen potential,
freshness, audience size, and international potential. Factor weights are data,
ready for the future Learning Engine to tune.

### Pipeline integration

Two new stages open the intelligence pipeline — `trend_discovery` and
`opportunity_ranking` — so the flow is now:

```
Trend Discovery → Opportunity Ranking → Research → Ideation → Psychology
    → Ranking → Script → Critic → Revision → Citation → SEO → Quality Gate
```

Only the top 5 opportunities move forward; their keywords feed the ideation
prompt so generated concepts ride real trend signals.

### Trend Dashboard

The Ideas tab now shows a compact Trend Discovery panel (no redesign): top
opportunity score, average growth, velocity, trending countries / platforms /
languages, discovery timestamp, and a ranked list of the top opportunities.

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
Placeholder platform connection cards (YouTube Shorts, TikTok, Instagram Reels, Facebook Reels, X, YouTube Long-form) plus a roadmap for Auto Posting, AI Voice Generation, and AI Video Creation.

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
- [Plotly](https://plotly.com/python/) — Attention Graph radar chart (optional; falls back to a plain score list if absent)

## Architecture

Generational v5.0 is an autonomous content operating system. The Streamlit UI
is a thin shell over five layers:

```
        UI (Streamlit tabs + sidebar)
                    │
        services/  (research, ideation, production, assets, voice profiles, channels, knowledge)
                    │
   Job Queue ──► Workflow Manager ──► Engine Registry (23 live plugins)
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
**24 live engines** across two pipelines. Intelligence (16): Trend Discovery,
Opportunity Ranking, Research, Ideation, Psychology, Script Generation,
Visual Intelligence, Attention Graph, Ranking, Script (fallback), Critic,
Revision, Citation, SEO, Threat Detection, Quality. Production (8): Scene
Planning, Narration, Visual Planning, Asset Manager, Subtitle, Timeline,
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
│   ├── trend_sources/        # Trend providers (auto-discovered registry)
│   ├── llm.py, voice/, image_provider.py, video_provider.py, music_provider.py
│   └── publishing_provider.py, analytics_provider.py, trend_provider.py
├── engines/                  # Engine plugins (intelligence + production)
│   ├── trend_discovery.py, opportunity_ranking.py  # v7.0 front door
│   ├── script_generation.py  # v7.2 multi-variant Script Generation Engine
│   ├── attention_graph.py    # v7.3 12-dimension Attention Graph
│   ├── threat_detection.py   # v7.4 10-threat Psychology Threat Detection
│   ├── visual_intelligence.py # v7.5 Visual Production Package planner
│   ├── research … quality.py # Intelligence pipeline (16 live)
│   ├── scene_planning … publishing_queue.py  # Media production (8 live)
│   └── voice|image|video|publishing|analytics|learning.py  # future render stubs
├── services/
│   ├── research/             # Knowledge Engine (manager, cache, scorer, summarizer)
│   ├── trends/               # Trend Discovery (models, scorer, manager)
│   ├── scripts/              # Script Generation (models, platforms, generator, scorer)
│   ├── visual/               # Visual Intelligence (models, psychology, scenes, prompts, thumbnails, hooks, package)
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

- 📡 Live trend APIs (Google Trends, YouTube Data, TikTok, Reddit) behind the trend provider interface
- 🎬 Video/image generation from visual prompts (providers wired, engines stubbed)
- 🎙️ Real TTS providers (ElevenLabs, OpenAI) behind VoiceProvider
- 🧬 Voice cloning provider
- 📤 Auto Posting from publishing queue
- 📊 Full Analytics Dashboard + Learning loop (mines Knowledge Base + research)
