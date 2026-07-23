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
| **Agent 1** | Architecture / Trend Discovery owner | Trend Discovery subsystem, architecture docs, cross-cutting reviews |
| **Agent 2** | Psychology & Virality Engine | Psychology scoring, virality dimensions, ranking weights |
| **Agent 3** | Script Generation Engine | Script writing, critique, revision loop |

Agent 1 also acts as the reviewer for changes to shared files (see §2.3).

---

## 2. Ownership Rules

### 2.1 Exclusive ownership — edit freely within your area

| Agent | Owned paths |
|---|---|
| **Agent 1** | `services/trends/` · `providers/trend_sources/` · `engines/trend_discovery.py` · `engines/opportunity_ranking.py` · `tests/test_trend_discovery.py` · `MASTER_ARCHITECTURE.md` · `AGENT_WORKFLOW.md` · `services/editorial/` |
| **Agent 2** | `engines/psychology.py` · `engines/ranking.py` · `tests/test_psychology_engine.py` |
| **Agent 3** | `engines/script.py` · `engines/critic.py` · `engines/revision.py` · `services/scripts/` · script-related tests |

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
- `engines/__init__.py` — registration list (append-only, coordinate to avoid merge conflicts)
- `core/models.py` · `core/production_models.py` — canonical data shapes
- `core/jobs.py` — job queue semantics
- `providers/research_source.py` · `providers/trend_sources/base.py` — provider interfaces
- `app.py` — Streamlit shell
- `.gitignore` · `requirements.txt` · `requirements-dev.txt`

**Context contract:** never rename or remove existing keys in the shared
`context` dict (`research`, `trends`, `trend_opportunities`, `candidates`,
`selected_ideas`, `ideas`, `quality_summary`, ...). Add new keys instead.

---

## 3. Merge Safety Rules

1. **Always pull latest `main` before starting** — `git pull origin main`.
2. **Run the full test suite before committing** — `python -m pytest`. All tests must pass, including ones you didn't write.
3. **Commit small logical changes** — one concern per commit; never batch a feature with unrelated cleanup.
4. **Do not edit unrelated files** — if a file outside your ownership area appears in `git status`, exclude it from the commit (`.DS_Store` is never committed).
5. **Do not redesign UI during backend work** — UI additions are compact panels within existing tabs, matching current patterns.
6. **Never commit another agent's in-progress work** — stage files by explicit path, not `git add .` / `git add -A`.
7. **Keep modules small** — largest file today is 360 lines (`engines/psychology.py`); treat ~400 lines as the signal to split.

---

## 4. Branch Strategy

- **`main` is stable** — every commit on `main` passes the full test suite and launches cleanly.
- **Each agent should work on a feature branch**, merging to `main` only when the review checklist (§5) passes:

```
feature/psychology-engine
feature/script-engine
feature/render-package-engine
feature/trend-live-apis
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

## 6. Next Planned Agents

| Agent | Subsystem | Landing zone (already stubbed) |
|---|---|---|
| **Render Package Engine** | Turn `RenderPackage` objects into finished video | `engines/render_package.py` (live) → `engines/video.py` + `providers/video_provider.py` |
| **Voice Pipeline** | Real TTS + voice clone providers | `providers/voice/` · `engines/narration.py` |
| **Thumbnail Engine** | Thumbnail generation from concepts | new `engines/thumbnail.py` + `providers/image_provider.py` |
| **Analytics & Learning** | Performance ingestion + self-improvement loop | `engines/analytics.py` · `engines/learning.py` (planned stubs) |
| **Publishing Scheduler** | Queue → scheduled live posts | `engines/publishing.py` · `services/assets.py` publishing queue |

Each new agent gets: an ownership row in §2.1, a feature branch, and a
dedicated test file — before writing feature code.

---

*Maintained by Agent 1 (Architecture). Update this document whenever an agent
is added, ownership shifts, or a shared file changes category.*
