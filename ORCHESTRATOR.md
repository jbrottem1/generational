# Generational — Orchestration Layer

`services/orchestrator/` is the coordination layer that turns Generational's
engines into **one autonomous AI Content Operating System**. It exposes a
single clean interface; every subsystem (current and future) plugs into it
instead of being called directly.

```
User Command
    │
    ▼
Orchestrator.run_full_pipeline()
    │
    ├─ trend        trend_discovery → opportunity_ranking
    ├─ research     research → ideation (candidate pool)
    ├─ psychology   psychology (ViralScore, 18 dimensions)
    ├─ script       script_generation (multi-style variants)
    ├─ attention    attention_graph (12-dimension radar)
    ├─ visual       visual_intelligence (Cinematic AI Director)
    ├─ audio        voice_audio (Audio Production Package)
    ├─ refinement   ranking → script → critic → revision → citation → seo → threat_detection
    ├─ quality      quality (multi-factor publish gate)
    ├─ production   media production + publishing queue (approved ideas only)
    ├─ packaging    → list[ProductionPackage]
    ├─ render       image → video (Agent 6: render packages, mock render)
    ├─ seo          seo_optimization (Agent 8: Global Content Optimization)
    └─ publish      scheduler → publishing (Agent 7: jobs queued/published)
                    → one Production Report for the whole run
```

---

## 1. The one interface

```python
from services.orchestrator import get_orchestrator

result = get_orchestrator().run_full_pipeline("Create 3 science shorts about black holes")

result.status             # SUCCESS | WARNING | FAILED
result.packages           # list[ProductionPackage] — render/seo/publishing slots filled
result.stage_reports      # list[StageReport] — full diagnostics per stage
result.production_report  # ONE unified Production Report (see §3a)
result.context            # the shared pipeline context (advanced use)
```

`run_full_pipeline()` executes the **complete integrated workflow**: every
intelligence stage, media production, packaging, and then the distribution
stages — render → global content optimization → publishing — automatically.
`publish_mode` defaults to `"scheduled"` (jobs are queued into optimal
posting windows, nothing posts immediately); pass
`publish_mode="immediate"` to execute publishes (mock providers today).

Per-stage execution (fixture input, debugging, partial runs):

```python
orch = get_orchestrator()
context = {"command": "..."}
orch.run_trend_stage(context)      # StageReport
orch.run_script_stage(context)
orch.run_visual_stage(context)
orch.run_audio_stage(context)
orch.run_quality_stage(context)
orch.run_render_stage(context)     # Agent 6 — Render & Video Production
orch.run_seo_stage(context)        # Agent 8 — Global Content Optimization
orch.run_publish_stage(context)    # Agent 7 — Publishing & Scheduler
orch.run_analytics_stage(context)  # Agent 9 — Analytics collection (live)
orch.run_learning_stage(context)   # Agent 9 — Learning feedback (live)

# Future stages — wired now, light up when their engines report ready;
# until then they skip with diagnostics, never crash:
orch.run_brand_stage(context)      # Agent 10 — Multi-Brand OS
```

Agent 9's stages run post-publish: on demand via the runners above, or
automatically after every full run once
`services.analytics.integration.enable_continuous_learning()` has attached
its `analytics` / `learning` hooks (see §5) — the closed loop where every
published video makes the next one more intelligent.

The Streamlit UI reaches the orchestrator through `services/ideation.py`
(a thin adapter that reshapes `PipelineResult` into the result dict the UI
has always consumed). **No code should execute engines directly** — not the
UI, not services, not future agents.

## 2. ProductionPackage — the standardized data model

One `ProductionPackage` per idea flows out of every run
(`services/orchestrator/models.py`). Contract fields:

`project_id · brand · language · target_country · platforms · trend_score ·
competition_score · psychology_score · attention_score · hook · script ·
scene_breakdown · visual_assets · voice_assets · music_assets · captions ·
thumbnail_plan · seo_package · quality_score · publish_ready ·
analytics_placeholder`

Rules:

- **Future engines only ADD fields. Never remove or rename existing ones.**
- Unknown fields survive `to_dict()`/`from_dict()` round-trips via `extras`,
  so newer packages are never truncated by older code.
- `services/orchestrator/packager.py` is the only place that maps engine
  outputs onto the package — engines never build packages themselves.

## 3. Stage execution & error handling

Every stage returns a `StageReport`:

| Field | Meaning |
|---|---|
| `status` | `SUCCESS` · `WARNING` (engines skipped / soft errors) · `FAILED` |
| `started_at` / `finished_at` / `duration_ms` | Centralized timing |
| `confidence` | 0-100 signal read from what the stage produced |
| `warnings` / `errors` | Human-readable diagnostics |
| `diagnostics` | Engine-level step results and stage metrics |

A `FAILED` **intelligence** stage stops the pipeline gracefully — the run
returns with partial context, everything before the failure preserved, and
hooks are still notified. A `FAILED` **distribution** stage (render / seo /
publish) degrades the run to `WARNING` and the remaining stages still
execute — finished content is never discarded. Nothing crashes.

Contract validation runs around every engine step: `ContractEngine`
subclasses declare `input_contract` / `output_contract` keys, and any
missing key is recorded as a stage warning plus a `contract_validation`
diagnostics entry — validation never fails a run.

## 3a. The Production Report

Every `run_full_pipeline()` call returns **one Production Report**
(`services/orchestrator/report.py`, attached to
`result.production_report` and `context["production_report"]`):

| Section | Contents |
|---|---|
| `workflow` | The eight production areas (trend discovery → publishing), each resolved to SUCCESS/WARNING/FAILED with confidence + diagnostics |
| `stages` | Every StageReport as a dict (status, timing, confidence, warnings, errors, engine steps) |
| `engines` | Availability/readiness inventory of every engine the run touched, with declared contracts |
| `content` | Packages produced, publish-ready count, render readiness, optimization scores, publishing jobs/platforms |
| `warnings` / `errors` | Full rollup across every stage, prefixed by stage name |

The report is diagnostics only — building it never mutates the context and
never raises (a malformed result yields a safe fallback report).

All stage lifecycle events flow through the central structured logger
(`core/log.py`): `orchestrator.stage_started`, `orchestrator.stage_finished`
(with duration, confidence, warning/error counts), `orchestrator.pipeline_*`.

## 4. Plugin architecture — no hardcoded dependencies

The orchestrator has **one source of truth for engine order**:
`WORKFLOWS["intelligence"]` in `core/workflows.py`. `stages.py` partitions
that list into named stages at call time, so reordering the canonical
workflow automatically reorders the orchestrated pipeline.

Plugging in a future engine (Render, SEO, Learning, Publishing, Analytics,
Avatar, Voice Clone, Brand Manager, ...):

1. Create the engine module — it auto-registers via `engines/registry.py`.
2. Either add its key to `WORKFLOWS["intelligence"]` (canonical placement)
   **or** call `register_stage("render", ["image", "video"], after="quality")`
   to schedule a new named stage. Nothing in the orchestrator changes.

Stages whose engines report `is_ready() == False` are skipped with a
`WARNING` report — which is why `run_render_stage()` and
`run_publish_stage()` already exist and will light up on their own.

## 5. Autonomy preparation — hooks

Scheduling is **not built** (by design). The `analytics` and `learning`
hook kinds are LIVE: `enable_continuous_learning()`
(`services/analytics/integration.py`) attaches `AnalyticsHook` +
`LearningHook`, which drive `run_analytics_stage()` /
`run_learning_stage()` after every completed run. The attachment points:

```python
from services.orchestrator import OrchestratorHook, attach_hook

class MyAnalyticsAgent(OrchestratorHook):
    kind = "analytics"        # scheduler | publisher | analytics | learning
    name = "my-agent"

    def on_pipeline_complete(self, result):
        ...                    # consume PipelineResult

attach_hook(MyAnalyticsAgent())
```

Hooks are notified after every run (success or failure) and can never crash
the pipeline. A future Scheduler agent submits `ORCHESTRATOR_JOB_TYPE`
("run_pipeline") jobs to the existing job queue
(`ensure_orchestrator_handler(queue)`) instead of calling anything directly.

## 6. File map

```
services/orchestrator/
├── __init__.py        # public surface (the ONE import point)
├── orchestrator.py    # Orchestrator: run_full_pipeline + stage runners + logging
├── models.py          # ProductionPackage, StageReport, PipelineResult, StageStatus
├── stages.py          # stage registry derived from WORKFLOWS — plugin surface
├── packager.py        # final context → ProductionPackage mapping
├── report.py          # build_production_report — one report per run
└── hooks.py           # scheduler/publisher/analytics/learning attachment points
tests/test_orchestrator.py          # integration proof: command → ProductionPackage
tests/test_production_pipeline.py   # integration proof: full workflow + Production Report
```

## 7. Rules for future agents

- Call the orchestrator, never engines, from UI/services/automation code.
- Add ProductionPackage fields additively; map them in `packager.py`.
- New stages register via `register_stage()` or the canonical workflow list.
- Autonomous behavior attaches via hooks — the orchestrator is never edited
  to accommodate a new consumer.
