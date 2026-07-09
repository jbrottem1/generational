# Generational — Creative Studio UI (Agent 20)

The primary interface through which users interact with the Generational
platform. The Studio is a **UI layer only** — all production flows through
documented service contracts, never direct engine or provider calls.

## Architecture

```
User Prompt
    ↓
ui/tabs/studio.py                 Streamlit views (display only)
    ↓
services/studio/                  UI adapter layer
    ↓
services/workflow_executor/       Durable ProjectRun (Agent 21)
    ↓
services/orchestrator/            Stage coordination
    ↓
engines / ProviderRuntime         Generation + external AI gateway
```

## Workspace features

- Create, browse, duplicate, archive projects
- Search, folder organization, tags, platform filters
- 15 supported production types (YouTube, TikTok, podcasts, courses, etc.)

## Creative prompt panel

Users enter natural-language commands; the Studio displays full production
settings before execution and routes through the **Workflow Executor**
(which drives the Orchestrator stage-by-stage).

## Pipeline visualization

12-stage view mapped from Workflow Executor / orchestrator stage reports:

Research → Script → Creative Studio → Asset Generation → Animation →
Voice → Music → Post Production → Rendering → Publishing → Analytics → Learning

Each stage shows: pending, running, completed, failed, retry, elapsed time,
estimated time remaining.

## Live preview panels

Scripts, images, animation, voice, music, video, thumbnails, titles,
descriptions, captions, subtitles — extracted from `ContentPackage` slots.

## Long-form support

Commands matching long-form patterns (documentaries, courses, podcasts) are
submitted as durable `workflow_run` jobs via the Workflow Executor
(checkpoints under `data/workflow_runs/`). Legacy `RuntimeExecutionEngine`
(`longform_pipeline`) remains available for Agent 19 tooling but is **not**
the Studio default path.

## Integration points

| Need | Contract |
|---|---|
| Run production | `services.studio.run_studio_production()` → Workflow Executor → Orchestrator |
| Provider status | `services.studio.get_provider_dashboard()` → `ProviderRuntime` |
| Project CRUD | `services.studio.projects` → `core.storage` |
| Pipeline view | `services.studio.build_pipeline_view()` from `stage_reports` |
| Long-form jobs | `services.studio.submit_longform_job()` → `workflow_run` queue |
| Run status | `services.workflow_executor.get_status(run_id)` / `studio_status(run)` |

## Tests

`tests/test_studio.py` — service layer, Workflow Executor routing, long-form jobs.
