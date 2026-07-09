# Generational — Multi-Agent Development Workflow

This document governs how multiple AI agents (and humans) work on Generational
in parallel without stepping on each other. It complements
`MASTER_ARCHITECTURE.md`, which describes *what* the system is; this document
describes *who may change what, and how*.

**Golden rule:** engines never call each other, and agents never edit each
other's modules. All coordination happens through the shared `context` dict
and the Workflow Engine — and through this document.

---

## 1. Current Active Agents

| Agent | Role | Primary surface |
|---|---|---|
| **Agent 1** | Architecture / Trend Discovery owner | Trend Discovery subsystem, orchestration layer, architecture docs, cross-cutting reviews |
| **Agent 2** | Psychology & Virality Engine | Psychology scoring, virality dimensions, ranking weights |
| **Agent 3** | Script Generation Engine | Script writing, critique, revision loop |
| **Agent 4** | Visual Intelligence Engine (Cinematic AI Director) | Storyboards, shot lists, style presets, visual psychology + retention prediction, AI prompts, asset source adapters, thumbnails, render preparation |
| **Agent 6** | Render & Video Production | `engines/render/` landing zone — see its README |
| **Agent 7** | Publishing & Scheduler | `engines/publishing/` landing zone — see its README |
| **Agent 8** | SEO & Global Trend Optimization | `engines/seo/` landing zone — see its README |
| **Agent 9** | Analytics & Learning | `engines/analytics/` landing zone — see its README |
| **Agent 10** | Multi-Brand Operating System | `engines/brands/` landing zone — see its README |

Agent 1 also acts as the reviewer for changes to shared files (see §2.3).

---

## 2. Ownership Rules

### 2.1 Exclusive ownership — edit freely within your area

| Agent | Owned paths |
|---|---|
| **Agent 1** | `services/trends/` · `providers/trend_sources/` · `engines/trend_discovery.py` · `engines/opportunity_ranking.py` · `services/orchestrator/` · `tests/test_trend_discovery.py` · `tests/test_orchestrator.py` · `MASTER_ARCHITECTURE.md` · `AGENT_WORKFLOW.md` · `ORCHESTRATOR.md` |
| **Agent 2** | `engines/psychology.py` · `engines/ranking.py` · `tests/test_psychology_engine.py` |
| **Agent 3** | `engines/script.py` · `engines/critic.py` · `engines/revision.py` · script-related tests |
| **Agent 4** | `engines/visual_intelligence.py` · `services/visual/` · `tests/test_visual_intelligence.py` · `VISUAL_PRODUCTION_PACKAGE.md` |
| **Agent 6** | **Render files only:** `engines/render/` · `engines/image.py` · `engines/video.py` · `services/rendering/` · render/video providers · `tests/test_render_engine.py` |
| **Agent 7** | **Publishing files only:** `engines/publishing/` · `engines/publishing.py` · scheduler module · `services/publishing/` · publishing providers · `tests/test_publishing_engine.py` |
| **Agent 8** | **SEO-optimization files only:** `engines/seo/` (NOT the live `engines/seo.py`) · `services/seo/` · SEO providers · `tests/test_seo_optimization.py` |
| **Agent 9** | **Analytics/learning files only:** `engines/analytics/` · `engines/analytics.py` · `engines/learning.py` · `services/analytics/` · `services/learning/` · analytics providers · analytics/learning tests |
| **Agent 10** | **Brand/account/channel files only:** `engines/brands/` · `services/brands/` · `tests/test_brand_management.py` (extends `services/channels.py` with caution) |

Every landing-zone README (`engines/render/README.md`, `engines/publishing/README.md`,
`engines/seo/README.md`, `engines/analytics/README.md`, `engines/brands/README.md`)
is the authoritative per-agent scope definition. Read it before writing code.

### 2.2 Shared — edit with caution, keep diffs minimal, mention in commit body

| Path | Why it is shared |
|---|---|
| `engines/heuristics.py` | Imported by **seven** modules (psychology, critic, revision, seo, quality, research citation, summarizer). Only **add** helpers; never change existing signatures or constants without checking all importers. |
| `engines/quality.py` | Final gate — consumes scores produced by psychology, citation, and research. Threshold logic changes affect every agent's output. |
| `core/constants.py` | App-wide config. Add keys; don't rename or remove. `APP_VERSION` bumps belong to the agent shipping the release. |
| `core/state.py` | Session defaults. Add keys only. |
| `services/ideation.py` · `services/production.py` | Pipeline orchestrators — pass-through wiring for every stage's output. |
| `ui/components.py` · `ui/tabs/ideas.py` · `ui/tabs/settings.py` | Presentation for all engines. Add compact panels/controls; never restructure layout during backend work. |
| `tests/test_intelligence_pipeline.py` · `tests/test_engines.py` · `tests/test_media_production.py` | End-to-end expectations (stage counts, context keys). Update the specific assertion your change affects; nothing else. |
| `README.md` | Version sections are append-only; each agent documents its own release. |

### 2.3 Do NOT edit without explicit approval (Agent 1 review)

These files define contracts every agent depends on. Changing them silently
breaks parallel work:

- `core/workflows.py` — `WORKFLOWS` stage order is the system's spine
- `engines/base.py` · `engines/registry.py` — the Engine contract
- `engines/contracts.py` · `engines/future_stubs.py` — the ContractEngine interface and Agents 6-10 stage stubs
- `engines/__init__.py` — registration list (append-only, coordinate to avoid merge conflicts)
- `core/models.py` · `core/production_models.py` — canonical data shapes
- `services/orchestrator/models.py` — the canonical ContentPackage / ProductionPackage (fields are additive-only; see `DATA_CONTRACTS.md`)
- `core/jobs.py` — job queue semantics
- `providers/research_source.py` · `providers/trend_sources/base.py` — provider interfaces
- `app.py` — Streamlit shell
- `.gitignore` · `requirements.txt` · `requirements-dev.txt`

**Context contract:** never rename or remove existing keys in the shared
`context` dict (`research`, `trends`, `trend_opportunities`, `candidates`,
`selected_ideas`, `ideas`, `quality_summary`, ...). Add new keys instead.

**Orchestrator contract (v8.0):** UI, services, and future autonomous agents
call `services/orchestrator/` — never engines directly. `ProductionPackage`
fields are additive-only; new stages plug in via `register_stage()` or
`WORKFLOWS["intelligence"]`; autonomy attaches via `OrchestratorHook`.
See `ORCHESTRATOR.md`.

**ContentPackage contract (v8.1):** the shared data model in
`services/orchestrator/models.py` is the single package every stage reads
and writes. Agents may **append** fields (coordinate with Agent 1) and fill
their own package slot (`render_package`, `publishing_package`,
`seo_package`, `analytics_package`, `learning_metadata`, brand fields) —
never remove, rename, or repurpose existing fields. See `DATA_CONTRACTS.md`.

---

## 3. Merge Safety Rules

1. **Always pull latest `main` before starting** — `git pull origin main`.
2. **Run the full test suite before committing** — `python -m pytest`. All tests must pass, including ones you didn't write.
3. **Commit small logical changes** — one concern per commit; never batch a feature with unrelated cleanup.
4. **Do not edit unrelated files** — if a file outside your ownership area appears in `git status`, exclude it from the commit (`.DS_Store` is never committed).
5. **Do not redesign UI during backend work** — UI additions are compact panels within existing tabs, matching current patterns.
6. **Never commit another agent's in-progress work** — stage files by explicit path, not `git add .` / `git add -A`. **Commit only files you own.**
7. **Keep modules small** — treat ~400 lines as the signal to split.
8. **Shared contracts require caution** — `ContentPackage` fields, `context` keys, and engine `input_contract`/`output_contract` declarations are additive-only. `app.py`, `core/workflows.py`, the engine registry, and the data contracts require explicit Agent 1 review before editing (§2.3).
9. **Use feature branches wherever possible** (§4); direct `main` commits only for small fully-tested isolated changes.

---

## 4. Branch Strategy

- **`main` is stable** — every commit on `main` passes the full test suite and launches cleanly.
- **Each agent should work on a feature branch**, merging to `main` only when the review checklist (§5) passes:

```
feature/psychology-engine
feature/script-engine
feature/trend-live-apis
feature/render-engine          (Agent 6)
feature/publishing-scheduler   (Agent 7)
feature/seo-optimization       (Agent 8)
feature/analytics-learning     (Agent 9)
feature/multi-brand-os         (Agent 10)
```

- Rebase or merge `main` into the feature branch before opening a PR so conflicts are resolved by the branch owner, not the reviewer.
- Direct commits to `main` are acceptable only for small, isolated, fully-tested changes (docs, single-file fixes).

---

## 5. Review Checklist (before merging to main)

- [ ] `python -m pytest` — all tests pass (no skipped regressions)
- [ ] `streamlit run app.py` launches without errors
- [ ] `README.md` updated (version section for feature releases)
- [ ] `MASTER_ARCHITECTURE.md` updated (engine tables, roadmap, test count)
- [ ] No duplicate engines — one module per `key`, registered once in `engines/__init__.py`
- [ ] No broken imports — every module the change touches still imports (pytest collection catches this)
- [ ] No giant files — split modules approaching ~400 lines
- [ ] No unrelated UI redesigns — diff to `ui/` limited to the feature's own panel/controls
- [ ] No unrelated files in the commit (check `git status` before and after staging)

---

## 6. Next Planned Agents (landing zones prepared, v8.1)

| Agent | Subsystem | Landing zone | Engine keys | Orchestrator stage |
|---|---|---|---|---|
| **Agent 6** | Render & Video Production — **LANDED (mock render)** | `engines/render/` | `image` · `video` · `render` | `render` (live) |
| **Agent 7** | Publishing & Scheduler | `engines/publishing/` | `publishing` · `scheduler` | `publish` |
| **Agent 8** | Global Content Optimization (SEO) — **LANDED** | `engines/seo/` (docs) + `engines/seo_optimization.py` + `services/seo/` | `seo_optimization` | `seo` (live) |
| **Agent 9** | Analytics & Learning | `engines/analytics/` | `analytics` · `learning` | `analytics` · `learning` |
| **Agent 10** | Multi-Brand Operating System | `engines/brands/` | `brand_management` | `brand_management` |

Agent 6 has landed: the render stage is live end-to-end with mock providers
(full render plan + simulated render; real backends swap in behind
`providers/` and `engines.render.assets.register_fulfiller()` — see
`engines/render/README.md`). Agent 8 has landed: the seo stage is live —
the Global Content Optimization Engine enriches `seo_package` additively
and emits standardized PublishingPackages for Agent 7 (see
`engines/seo/README.md`; SEO signal providers auto-discover from
`providers/seo_sources/`). The remaining three stages are wired into the
orchestrator and skip cleanly (WARNING with diagnostics, never a crash)
until their engines report ready. Contract stubs for the missing keys live
in `engines/future_stubs.py`.
Each agent's landing-zone README defines exact ownership, contracts, and
forbidden files. Also planned: Voice Pipeline (real TTS/clone providers) and
Thumbnail Engine — coordinate with Agent 1 before starting.

Each new agent gets: an ownership row in §2.1, a feature branch, and a
dedicated test file — before writing feature code.

---

*Maintained by Agent 1 (Architecture). Update this document whenever an agent
is added, ownership shifts, or a shared file changes category.*
