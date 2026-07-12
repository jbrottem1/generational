# Generational OS V2.5 — Autonomous Media Operating System

**Owner:** Agent 0 · Executive Office  
**Status:** LOCKED · Phase II  
**Supersedes:** ad-hoc agent collection → coordinated four-layer OS

---

## Mission

Transform Generational from a collection of agents into a **dependable, scalable, self-improving media operating system** capable of thousands of productions across brands, platforms, languages, and domains.

Every task has an owner. Every handoff is explicit. Every production is traceable from idea → research → render → publish → analytics → improvement.

---

## Four execution layers

| Layer | Runs on | Output | Module |
|-------|---------|--------|--------|
| **1 · Intelligence** | Cloud | `PRODUCTION_BRIEF.json` | `services/generational_os/brief.py` |
| **2 · Pre-Production** | Cloud | `RENDER_PACKAGE.json` | `services/generational_os/render_package.py` |
| **3 · Local Production** | Mac only | Verified MP4 + manifest | `services/generational_os/export.py` |
| **4 · Post-Production** | Both | `READY_TO_PUBLISH/` | (Agent 18 / 28 — next phase) |

Details: [EXECUTION_MODE.md](./EXECUTION_MODE.md) · [CLOUD_EXECUTION.md](./CLOUD_EXECUTION.md) · [LOCAL_EXECUTION.md](./LOCAL_EXECUTION.md)

---

## Standard pipeline

```
Idea → Research → Scientific Verification → SEO Analysis → Script → Storyboard
→ Visual Planning → Render Package → Local Production → QC → Export
→ Archive → Publishing Package → Analytics
```

Stage registry: `services/generational_os/pipeline.py`

No stage bypass without Executive approval.

---

## Production manifest

Every production: `data/generational_os/productions/{project_id}/PRODUCTION_MANIFEST.json`

Tracks project ID, series, episode, sources, QC score, export path, publishing status, pipeline stage, and verification block.

Database index: `data/generational_os/productions/index.json`

---

## Export standard (V2.5)

**Canonical path:**

```
~/Desktop/AI Start-up/Generational/Videos/{Domain}/{filename}.mp4
```

**Domain folders:** Biology, Physics, Chemistry, Mathematics, Earth Science, Astronomy, Medicine, Technology, Engineering, Psychology, History, Business, Artificial Intelligence, Miscellaneous

Classifier: `services/generational_os/export_classifier.py`

Legacy path (`videos/Test run 2 generational/`) remains referenced for migration — new exports use classified Generational tree.

---

## Asset management

| Library | Registry |
|---------|----------|
| Characters, backgrounds, props, diagrams, real images, … | `data/generational_os/asset_registry.json` |
| Download cache (no duplicates) | `data/local_cache/` |

API: `services/generational_os/asset_registry.py`

---

## Local-first policy

- **Cloud:** planning, coding, briefs, render packages — never `"Video exported."`
- **Local Mac:** render, verify, classify export, update manifest + DB
- Gate: `services/media_production/local_first.py` → `services/generational_os/orchestrator.py`

---

## Commands

```bash
# Cloud: prepare brief + render package (no render)
python3 scripts/foundation_v2_turtles.py

# Local Mac: execute render package
python3 scripts/run_render_package.py --package RENDER_PACKAGE.json

# Refresh executive dashboard
python3 scripts/generational_os_dashboard.py
```

---

## Executive dashboard

- JSON: `data/generational_os/dashboard.json`
- Markdown: `EXECUTIVE_OPERATING_DASHBOARD.md`

Shows queues (research, script, render, QC, publish), metrics, asset cache health, and ranked self-improvement recommendations.

---

## Self-improvement

`services/generational_os/improvement.py` — recommends before implementing. Production quality and reliability over feature creep.

---

## Scalability design

- Configuration-driven domains, platforms, characters (not architectural forks)
- JSON manifest + index scales to thousands of productions
- Render packages portable across machines
- Asset registry versioned for long-term character consistency

---

## Agent compliance

All production agents must:

1. Use `gate_production()` / `prepare_production()` before render
2. Write `PRODUCTION_BRIEF.json` + `RENDER_PACKAGE.json` in cloud mode
3. Use `export_verified_production()` for local export (manifest + DB)
4. Never claim Desktop SUCCESS from cloud VM paths

Standards: [data/knowledge_standards/PRODUCTION_STANDARDS.md](./data/knowledge_standards/PRODUCTION_STANDARDS.md)

---

## Package layout

```
services/generational_os/
├── layers.py          # Four layers + owners
├── pipeline.py        # Standard stages
├── brief.py           # Layer 1
├── render_package.py  # Layer 2
├── export.py          # Layer 3 verified export
├── manifest.py        # Permanent production record
├── database.py        # Production index
├── export_classifier.py
├── asset_registry.py
├── dashboard.py       # Executive dashboard
├── improvement.py     # Self-improvement
└── orchestrator.py    # End-to-end cloud handoff
```
