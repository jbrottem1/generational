# Generational — Master Architecture

**Current version:** v7.5.0  
**Status:** Source-backed research platform with an 18-dimension Psychology & Virality Engine, a multi-variant multi-platform Script Generation Engine, a Visual Intelligence Engine (storyboards, AI image/video prompts, scored thumbnails, hook sequences), a Voice & Audio Engine (narration plans, voice styles, SFX, music direction, audio cue sheets, retention pacing notes), a 12-dimension Attention Graph, a 10-threat Psychology Threat Detection layer, citation engine, and multi-factor quality gate  
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

Generational v7.6 is a modular platform with:

- A **Trend Discovery Engine** — the front door: auto-discovered trend providers, a universal Trend model, and 0-100 Opportunity Scoring that gates what enters the pipeline
- A **Psychology & Virality Engine** — scores every candidate idea across 18 attention-science dimensions, blends them into a weighted 0-100 ViralScore, and produces a plain-English psychology report explaining why
- A **Script Generation Engine** — runs immediately after Psychology: every candidate gets multiple stylistically distinct, platform-aware script variants (13 storytelling components each: hook, pattern interrupt, curiosity loop, core story, emotional progression, retention checkpoints, CTA, SEO keywords, B-roll, AI visual prompts, sound effects, music style, estimated runtime), scored 0-100 across six weighted factors, best variant wins
- A **Visual Intelligence Engine** — the visual brain: every scripted candidate receives a complete Visual Production Package (scene-by-scene storyboard with full visual grammar, 12-dimension visual psychology scores per scene, model-ready AI image prompts for 5 image models and AI video prompts for 6 video models, 5 scored thumbnail concepts with expected CTR, a five-frame hook sequence, caption plan, and pacing/camera/motion reports) blended into one weighted Overall Visual Score (0-100)
- A **Voice & Audio Engine** — the sound brain: every scripted candidate's visual package becomes a complete Audio Production Package (niche-matched voice style, per-scene narration plan with target words-per-minute / scripted pauses / emphasis words, layered sound effect recommendations, background music direction with BPM range / key / energy curve / sections, audio mood progression, a scene-by-scene audio cue sheet, and retention pacing notes) blended into one weighted Overall Audio Score (0-100) — planning only, no audio files generated
- An **Attention Graph Engine** — scores every candidate across 12 attention dimensions into a radar-chart-ready profile plus a weighted 0-100 Attention Score, with a concrete recommendation for raising every dimension
- A **Psychology Threat Detection Engine** — screens every packaged idea for 10 production failure modes (clickbait without payoff, weak hooks, platform policy risk, manipulative language, and more), producing a Threat Level (Low/Medium/High), a confidence %, and a fix recommendation for every flagged threat
- A **Knowledge Engine** with live Wikipedia, PubMed, arXiv, and Crossref connectors
- A **Citation Engine** that maps scripts to sources and flags unsupported claims
- An **Intelligence Pipeline** (17 stages) from trend discovery and opportunity ranking through ideas, psychology, script generation, visual intelligence, voice & audio, attention graph, ranking, critique, citation, SEO, threat detection, and quality
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
│  24 live engines · 6 planned stubs                           │
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
    │   Stages 3–17: Intelligence Pipeline
    │       ideation → psychology → script_generation →
    │       visual_intelligence → voice_audio → attention_graph → ranking →
    │       script (fallback) → critic → revision → citation →
    │       seo → threat_detection → quality
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
| `candidates` | Ideation | Psychology, Script Generation, Ranking |
| `candidates[].psychology`, `.psychology_score`, `.viral_score`, `.psychology_report` | Psychology | Script Generation, Ranking, Quality, UI (idea card report expander) |
| `psychology_summary` | Psychology | UI, diagnostics |
| `candidates[].script_variants`, `.script`, `.cta`, `.script_score`, `.script_style`, `.estimated_runtime_sec`, `.retention_checkpoints`, `.broll_suggestions`, `.visual_prompts`, `.sound_effects`, `.music_style` | Script Generation | Ranking, Critic, Citation, Quality, Production, UI |
| `candidates[].structured_script` (title, hook, narration, scene_breakdown, timestamps, emotional_beats, visual_notes, cta, platform_format) | Script Generation | Visual Intelligence, future renderers |
| `script_generation_summary` | Script Generation | UI, diagnostics |
| `target_platform`, `script_variant_count` | Caller (optional) | Script Generation, Visual Intelligence |
| `candidates[].visual_package` (`.scenes`, `.storyboard`, `.image_prompts`, `.video_prompts`, `.thumbnails`, `.hook_sequence`, `.caption_plan`, `.pacing_report`, `.camera_plan`, `.motion_report`, `.visual_score`), `.visual_score`, `.thumbnail_concepts` | Visual Intelligence | Future renderers (image/video/thumbnail/caption), UI (visual package expander) |
| `visual_intelligence_summary` | Visual Intelligence | UI, diagnostics |
| `candidates[].audio_package` (`.voice_style`, `.narration_plan`, `.pacing`, `.pause_map`, `.emphasis_map`, `.sfx_plan`, `.music_direction`, `.audio_mood`, `.scene_cues`, `.retention_notes`, `.audio_score`), `.audio_score` | Voice & Audio | Future renderers (voice/music/video), UI |
| `voice_audio_summary` | Voice & Audio | UI, diagnostics |
| `candidates[].attention_graph` (`.scores`, `.attention_score`, `.radar_chart`, `.recommendations`) | Attention Graph | Ranking, UI (radar chart expander) |
| `attention_graph_summary` | Attention Graph | UI, diagnostics |
| `ranked_candidates`, `selected_ideas` | Ranking | Script (fallback), SEO, Threat Detection, Quality |
| `selected_ideas[].threat_report` (`.threats`, `.threat_score`, `.threat_level`, `.confidence`, `.flagged_threats`, `.recommendations`) | Threat Detection | UI (threat report expander), diagnostics |
| `threat_detection_summary` | Threat Detection | UI, diagnostics |
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

### Intelligence Pipeline (17 live engines)

| Key | Module | Responsibility |
|---|---|---|
| `trend_discovery` | `engines/trend_discovery.py` | Front door — queries all trend providers; normalizes into universal Trend model |
| `opportunity_ranking` | `engines/opportunity_ranking.py` | Scores trends 0-100 (11 factors); only top opportunities move forward |
| `research` | `engines/research.py` | Knowledge Engine — live APIs + demo fallback; produces Research Brief |
| `ideation` | `engines/ideation.py` | Generates 20 candidate concepts grounded in research brief |
| `psychology` | `engines/psychology.py` | Psychology & Virality Engine — scores candidates on 18 attention dimensions, blends a weighted ViralScore (0-100), and produces a psychology report (deterministic) |
| `script_generation` | `engines/script_generation.py` | Script Generation Engine — runs immediately after Psychology; multi-style, platform-aware script variants per candidate (13 storytelling components), scored 0-100, best variant attached; delegates to `services/scripts/` |
| `visual_intelligence` | `engines/visual_intelligence.py` | Visual Intelligence Engine — runs immediately after Script Generation; every scripted candidate receives a Visual Production Package (storyboard, per-scene visual psychology scores, AI image/video prompts, scored thumbnails, hook sequence, pacing/camera/motion reports) and an Overall Visual Score (0-100); delegates to `services/visual/` |
| `voice_audio` | `engines/voice_audio.py` | Voice & Audio Engine — runs immediately after Visual Intelligence; every scripted candidate receives an Audio Production Package (voice style, narration plan with pacing/pauses/emphasis, SFX recommendations, music direction, audio mood, scene-by-scene audio cues, retention pacing notes) and an Overall Audio Score (0-100); planning only, no audio files; delegates to `services/audio/` |
| `attention_graph` | `engines/attention_graph.py` | Attention Graph Engine — scores candidates on 12 attention dimensions, blends a weighted Attention Score (0-100), and returns a radar-chart payload plus per-dimension recommendations (deterministic) |
| `ranking` | `engines/ranking.py` | Weighted ranking (psychology 50% + opportunity 30% + script quality 20%); selects top N |
| `script` | `engines/script.py` | Fallback scriptwriter — covers ideas that reach ranking unscripted; never overwrites generated variants |
| `critic` | `engines/critic.py` | Adversarial review — flags weak hooks, repetition, pacing |
| `revision` | `engines/revision.py` | Auto-rewrites flagged sections |
| `citation` | `engines/citation.py` | Maps scripts to sources; claim confidence; unsupported claim warnings |
| `seo` | `engines/seo.py` | Titles, hashtags, keywords, description, thumbnail concept |
| `threat_detection` | `engines/threat_detection.py` | Psychology Threat Detection Engine — screens the packaged idea for 10 failure modes, blends a weighted Threat Score (0-100), and returns a Threat Level (Low/Medium/High), a confidence %, and fix recommendations (deterministic) |
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

### Visual Intelligence (deep dive)

`engines/visual_intelligence.py` is the visual brain of the pipeline. It runs
immediately after Script Generation and before the Attention Graph, so every
scripted candidate carries a complete visual plan before ranking happens, and
every downstream renderer (voice → audio → image → video) consumes one
canonical Visual Production Package. No videos are generated yet — this is
the planning layer future render engines execute. Planning is delegated to
the modular `services/visual/` package (usable standalone via
`build_visual_package(idea, niche=..., subject=..., aspect_ratio=...)`).

- **Scene planner** (`services/visual/scenes.py`): breaks the winning script
  variant into hook → pattern interrupt → curiosity loop → story beats
  (~one visual change every 7 seconds, max 6 beats) → payoff → CTA. Each
  scene carries the full visual grammar: purpose, emotion (from the
  variant's emotional progression), length, narration, visual description,
  camera angle + motion, shot composition, subject placement, lighting +
  environment (per-emotion looks), niche color palette, transitions in/out
  (chained so every scene's `transition_in` matches the previous scene's
  `transition_out`), motion intensity, zoom, background, overlay, text
  overlay, caption timing, sound effect, music style, and B-roll. All
  grammar lives in data tables (`PURPOSE_GRAMMAR`, `EMOTION_LOOKS`,
  `NICHE_VISUAL_PALETTES`) — art-direction changes never touch planner code.
- **Visual psychology** (`services/visual/psychology.py`): every scene is
  scored 0-100 on 12 perceptual triggers — curiosity, mystery, wonder, fear,
  beauty, novelty, scale, contrast, motion, satisfaction, humor, identity —
  using deterministic word-bank + structure analysis (new visual banks plus
  shared banks from `engines/heuristics.py`), blended into a per-scene
  Visual Score via `VISUAL_SCORE_WEIGHTS` (data, not code).
- **AI prompt builders** (`services/visual/prompts.py`): one shared
  model-agnostic spec per scene (lighting, composition, lens, mood, art
  style, palette, quality, aspect ratio, camera movement, character action,
  physics, duration) formatted into each model's dialect — image prompts for
  Midjourney, Flux, Stable Diffusion, DALL-E, and OpenAI Images; video
  prompts for Runway, Veo, Pika, Luma, Kling, and Sora (future-ready).
  Adding a model is one formatter function.
- **Thumbnail engine** (`services/visual/thumbnails.py`): five archetypes
  (shock face close-up, mystery object macro, before/after split, extreme
  scale contrast, bold text tease) scored on 7 dimensions — curiosity,
  readability, contrast, facial focus, object focus, color, emotion — via
  `THUMBNAIL_SCORE_WEIGHTS`, each mapped to an expected CTR % (1.5-14%).
- **Hook visualizer** (`services/visual/hooks.py`): the strongest five-frame
  first-3-second sequence (abrupt motion → novel detail anchor → curiosity
  gap → direct address → open loop) with a plain-English scroll-stop
  rationale.
- **Package assembly** (`services/visual/package.py`): storyboard, caption
  plan, visual pacing report (cut rhythm vs. the 3-8s retention ideal),
  camera plan with a variety score, transition list, and motion report
  (per-scene intensity curve). Components blend into one weighted **Overall
  Visual Score (0-100)** via `PACKAGE_SCORE_WEIGHTS` (scene craft 0.35,
  hook strength 0.25, thumbnail power 0.20, pacing fitness 0.12, camera
  variety 0.08).
- Attached to every candidate as `visual_package` (plus `visual_score` and
  `thumbnail_concepts`); a batch `visual_intelligence_summary` (planned
  count, total scenes, average visual score, platform/aspect ratio) is
  attached to the pipeline context for diagnostics. Fully deterministic —
  Demo Mode carries the entire engine, and the idea card surfaces a compact
  "🎥 Visual Production Package" expander (no new UI pages).

### Voice & Audio (deep dive)

`engines/voice_audio.py` is the sound brain of the pipeline. It runs
immediately after Visual Intelligence — consuming the storyboard's caption
timings, motion intensities, emotional arc, and per-scene SFX/music hints —
and before every rendering stage (voice synthesis, image, video), so all
renderers execute one canonical sound plan. No audio files are generated —
this is the brief the future TTS/music providers execute. Planning is
delegated to the modular `services/audio/` package (usable standalone via
`build_audio_package(idea, niche=..., subject=..., platform=...)`; ideas
without a `visual_package` get a standalone storyboard planned on the fly).

- **Voice style** (`services/audio/voice.py`): a narrator persona per niche
  (tone, pitch, character in `NICHE_VOICE_STYLES` — data, not code), a vocal
  energy level derived from the storyboard's average motion intensity, and
  delivery notes tied to the emotional arc and the platform's narration tone.
- **Narration plan** (`services/audio/narration.py`): per-scene delivery
  directions from `PURPOSE_DELIVERY` (urgent hook open, conspiratorial
  curiosity tease, slow-breathing payoff, warm CTA), target words-per-minute
  per scene (platform base × purpose factor — hooks read faster, payoffs
  slower), scripted pauses (purpose pause plus beats after questions and
  ellipses, the payoff's 0.7s dramatic silence longest of all), and emphasis
  words (numbers first, then curiosity/surprise/emotion trigger words), with
  a global pacing verdict and fitness comparing actual vs. target wpm.
- **SFX planner** (`services/audio/sfx.py`): keeps each scene's primary
  effect from the visual storyboard and layers purpose-specific support cues
  (transition whooshes, tension drones, UI pops) with timing, intensity, and
  a mix note; reports scene coverage diagnostics.
- **Music direction + mood** (`services/audio/music.py`): style (from the
  script's music style), BPM range from average motion intensity, major/minor
  key from the emotional arc's tension density, a per-scene energy curve,
  named sections per purpose (cold-open sting → low pulse build → driving
  groove → full swell → stripped-back outro), sidechain ducking guidance, and
  a seamless-loop note; plus the overall audio mood and its scene-by-scene
  progression via `EMOTION_AUDIO_MOODS` (the sonic complement of the visual
  `EMOTION_LOOKS`).
- **Retention pacing notes** (`services/audio/retention.py`): audits planned
  audio events (SFX cues + music section changes + pauses) against the
  short-form ideal of 1.5-4 events per 10 seconds and emits scene-anchored
  fixes — sound inside the first 0.5s, silence before the payoff reveal, a
  mid-video texture reset, a thinned mix under the CTA — with a fitness score.
- **Package assembly** (`services/audio/package.py`): merges everything into
  a scene-by-scene audio cue sheet (`AudioSceneCue` — narration delivery,
  wpm, pauses, emphasis, SFX, music section/energy/ducking, mood, retention
  reminder) and blends components into one weighted **Overall Audio Score
  (0-100)** via `AUDIO_SCORE_WEIGHTS` (narration fitness 0.30, retention
  audio 0.20, SFX coverage 0.20, music dynamics 0.20, mood variety 0.10).
- Attached to every candidate as `audio_package` (plus `audio_score`); a
  batch `voice_audio_summary` is attached to the pipeline context for
  diagnostics. Fully deterministic — Demo Mode carries the entire engine.

### Attention Graph (deep dive)

`engines/attention_graph.py` is Phase 2 of the attention-engineering stack. It
runs after Script Generation and before Ranking, giving every candidate a
radar-chart-ready profile of the moment-to-moment attention mechanics a
finished video would need to execute.

- **12 dimensions** (`score_dimensions()`): first-3-second hook, curiosity
  gap, dopenness, emotional intensity, story tension, surprise, visual
  novelty, shareability, rewatch probability, comment likelihood, identity
  signaling, tribal engagement. Nine dimensions reuse the already-tested
  Phase 1 psychology scorer so the two phases stay consistent; three are new
  to this phase — **dopenness** (how quickly and openly the concept opens an
  anticipatory reward loop for a broad, low-jargon audience), **story
  tension** (turning-point language and setup/twist structure), and
  **visual novelty** (concrete, filmable transformation/reveal cues) — all
  backed by new word banks in `engines/heuristics.py`.
- **Attention Score** (`attention_score()`): the 12 dimensions blend into one
  weighted 0-100 score via `ATTENTION_GRAPH_WEIGHTS` — data, not code, so the
  future Learning Engine can retune weights from real performance results.
- **Radar chart payload** (`radar_chart()`): labels + scores arrays consumed
  by `ui/components.attention_radar_chart()`, which renders a Plotly
  Scatterpolar chart (falls back to a plain score list if `plotly` isn't
  installed) inside a compact "🕸️ Attention Graph" expander on the idea card
  — no new UI pages.
- **Recommendations** (`build_recommendations()`): a concrete, dimension-
  specific suggestion for raising every one of the 12 scores, surfaced
  weakest-first in the same expander.
- Attached to every candidate as `attention_graph` (`scores`, `attention_score`,
  `radar_chart`, `recommendations`); a batch `attention_graph_summary` is
  attached to the pipeline context for diagnostics.

### Psychology Threat Detection (deep dive)

`engines/threat_detection.py` is Phase 3 of the attention-engineering stack.
It runs after SEO packaging (so the thumbnail concept and full script
already exist) and before the final Quality Gate, screening the *finished*
package for the failure modes that erode watch time, trust, or platform
standing even when the underlying psychology scored well.

- **10 threat detectors** (`score_threats()`): clickbait without payoff,
  low dopamine pacing, weak hooks, viewer fatigue, thumbnail mismatch,
  predictable scripting, retention cliff risk, platform policy risk,
  manipulative language, and repetitive content. Each is scored 0-100
  (higher = riskier) by deterministic text-feature analysis that reuses the
  already-computed Psychology dimensions, script/thumbnail package, and
  retention checkpoints, plus new word banks in `engines/heuristics.py`
  (`PAYOFF_WORDS`, `GENERIC_OPENER_PHRASES`, `POLICY_RISK_WORDS`,
  `MANIPULATIVE_WORDS`). **Repetitive Content** is the one dimension that
  looks across the batch — it compares an idea's title/hook against every
  other selected idea in the same run to catch near-duplicates.
- **Threat Score** (`overall_threat_score()`): the 10 dimensions blend into
  one weighted 0-100 score via `THREAT_WEIGHTS` — data, not code, so the
  future Learning Engine can retune weights from real moderation/performance
  outcomes without touching detection logic.
- **Threat Level**: `overall_threat_score` maps to `Low` / `Medium` / `High`
  via fixed thresholds (`LEVEL_THRESHOLDS`).
- **Confidence** (`_confidence()`): 50-97%, reflecting how much of the
  packaged idea (script, psychology dimensions, retention checkpoints,
  thumbnail concept, CTA) was available to analyze — more signal present
  means a more confident assessment, independent of the risk score itself.
- **Fix recommendations** (`build_threat_report()`): every dimension always
  has a concrete fix (`THREAT_FIXES`); dimensions scoring at/above the flag
  threshold (55) are surfaced worst-first in `flagged_threats`, each paired
  with its fix, plus a one-line plain-English `summary`.
- Attached to every selected idea as `threat_report`; a batch
  `threat_detection_summary` (scored count, average threat score, level
  counts) is attached to the pipeline context for diagnostics. Purely
  additive — it does not alter `quality.py`'s publish-gate math.

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
| Scripts | `services/scripts/` | Script Generation — `PlatformSpec` for 6 platforms, `ScriptVariant` model (13 components), deterministic multi-style generator, 6-factor variant scorer, `generate_script_package()` standalone API |
| Visual | `services/visual/` | Visual Intelligence — `ScenePlan` + `ThumbnailConcept` models, 12-dimension visual psychology scorer, deterministic scene planner, per-model AI image/video prompt builders, thumbnail engine, hook visualizer, `build_visual_package()` standalone API |
| Audio | `services/audio/` | Voice & Audio — `AudioSceneCue` model, niche voice styles, narration planner (pacing/pauses/emphasis), SFX planner, music direction + audio mood, retention pacing audit, `build_audio_package()` standalone API |
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
| **v7.2** | Script Generation Engine | Multi-variant multi-style scripts for 6 platforms, 13 storytelling components per script, 6-factor variant scoring, runs immediately after Psychology, script quality feeds ranking |
| **v7.3** | Attention Graph (Attention Intelligence) | 12-dimension attention scoring, weighted Attention Score, radar-chart payload + Plotly visualization, per-dimension recommendations, runs after Script Generation and before Ranking |
| **v7.4** | Psychology Threat Detection (Threat Intelligence) | 10-threat production risk screening, weighted Threat Score, Threat Level (Low/Medium/High), confidence %, fix recommendations, runs after SEO and before the Quality Gate |
| **v7.5** | Visual Intelligence Engine | Visual Production Package per scripted candidate — storyboard with full visual grammar, 12-dimension visual psychology per scene, AI image prompts (5 models) + video prompts (6 models), 5 scored thumbnail concepts with expected CTR, five-frame hook sequence, pacing/camera/motion reports, Overall Visual Score (0-100); runs after Script Generation and before the Attention Graph |
| **v7.6** | Voice & Audio Engine | Audio Production Package per scripted candidate — niche-matched voice style, narration plan with per-scene pacing/pauses/emphasis, layered SFX recommendations, music direction (BPM/key/energy curve/sections/ducking), audio mood progression, scene-by-scene audio cue sheet, retention pacing notes, Overall Audio Score (0-100); runs after Visual Intelligence and before every rendering stage — planning only, no audio files |

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
| `tests/test_script_generation.py` | Script Engine — platform specs, 13-component variants, deterministic scoring, pipeline position, ranking blend, fallback behavior |
| `tests/test_attention_graph.py` | Attention Graph Engine — 12 dimensions, weight normalization, determinism, radar chart shape, recommendations, pipeline integration |
| `tests/test_visual_intelligence.py` | Visual Intelligence Engine — 12 visual dimensions, weight normalization, scene planner components/ordering/timing, image+video prompt coverage, thumbnail scoring + CTR, hook sequence, package shape, determinism, pipeline position, pipeline integration |
| `tests/test_voice_audio.py` | Voice & Audio Engine — voice styles, narration plan (wpm modulation, pauses, emphasis), SFX layering + coverage, music direction (tempo/key/sections/energy), audio mood, retention pacing audit, package shape, determinism, no-audio-generated guarantee, pipeline position, pipeline integration |
| `tests/test_threat_detection.py` | Psychology Threat Detection Engine — 10 threats, weight normalization, determinism, threat-level/confidence bounds, flagged-threat sorting, fix recommendations, pipeline position, pipeline integration |
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

**190 tests passing** (as of v7.5.0).

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
│   ├── scripts/                    # Script Generation (models, platforms, generator, scorer)
│   ├── visual/                     # Visual Intelligence (models, psychology, scenes, prompts, thumbnails, hooks, package)
│   ├── audio/                      # Voice & Audio (models, voice, narration, sfx, music, retention, package)
│   ├── assets.py · voice_profiles.py
│   ├── knowledge.py · channels.py · pipeline.py
├── engines/                        # 25 live + 6 planned pipeline plugins
├── providers/                      # Swappable external backends
│   └── trend_sources/              # Auto-discovered trend providers
├── ui/                             # Streamlit presentation
├── tests/                          # 220+ unit/integration tests
└── data/                           # Runtime persistence (gitignored)
```

---

*Last updated: v7.6.0 — Voice & Audio Engine (Audio Production Packages)*
