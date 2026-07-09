# Generational — Creative Studio UI (Agent 20)

The primary interface through which users interact with the Generational
platform. The Studio is a **UI layer only** — all production flows through
documented service contracts, never direct engine or provider calls.

## Architecture

```
ui/tabs/studio.py          Streamlit views (display only)
    ↓
services/studio/           UI adapter layer
    ↓
services/ideation.py       Orchestrator adapter (run_full_pipeline)
services/provider_runtime/ Provider health + long-form jobs
services/workflow_executor/ Durable run status (Agent 21)
core/storage/              Project persistence
```

## Workspace features

- Create, browse, duplicate, archive projects
- Search, folder organization, tags, platform filters
- 15 supported production types (YouTube, TikTok, podcasts, courses, etc.)

## Creative prompt panel

Users enter natural-language commands; the Studio displays full production
settings before execution and routes through the Orchestrator.

## Pipeline visualization

12-stage view mapped from orchestrator `StageReport` diagnostics:

Research → Script → Creative Studio → Asset Generation → Animation →
Voice → Music → Post Production → Rendering → Publishing → Analytics → Learning

Each stage shows: pending, running, completed, failed, retry, elapsed time,
estimated time remaining.

## Live preview panels

Scripts, images, animation, voice, music, video, thumbnails, titles,
descriptions, captions, subtitles — extracted from `ContentPackage` slots.

## Long-form support

Commands matching long-form patterns (documentaries, courses, podcasts) can
be submitted as checkpointed jobs via `ProviderRuntime` long-form execution
or the Workflow Executor (`workflow_run` job type).

## Integration points

| Need | Contract |
|---|---|
| Run production | `services.studio.run_studio_production()` → `ideation.run_command()` → Orchestrator |
| Provider status | `services.studio.get_provider_dashboard()` → `ProviderRuntime` |
| Project CRUD | `services.studio.projects` → `core.storage` |
| Pipeline view | `services.studio.build_pipeline_view()` from `stage_reports` |
| Long-form jobs | `services.studio.submit_longform_job()` → job queue + checkpoints |
| Durable runs | `services.workflow_executor` → `ProjectRun` + checkpoints |

## Tests

`tests/test_studio.py` — 21 tests covering service layer and orchestrator integration.
