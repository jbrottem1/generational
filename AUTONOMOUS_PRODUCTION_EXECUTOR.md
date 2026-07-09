# Autonomous Production Executor (Agent 23)

Coordinates complete media productions from a single user request. Turns one
prompt into a durable `ProductionJob` that drives WorkflowExecutor →
Orchestrator stage-by-stage with scheduling, checkpoints, pause/resume,
parallel units, quality scoring, and detailed execution logs.

```python
from services.autonomous_production import get_production_executor

executor = get_production_executor()
job = executor.execute("Create a 45-second YouTube Short about black holes.")
status = executor.get_status(job.job_id)
```

**Not** a UI agent. **Not** a provider integration agent. **Not** a rewrite of
engines or the Orchestrator. Coordination only.

## Architecture

```
User request → AutonomousProductionExecutor → WorkflowExecutor → Orchestrator
  → Engines → ProviderRuntime → ProductionSummary + quality score
```

Do **not** bypass the Orchestrator. Do **not** call engines or vendor SDKs
from this package.

## Execution lifecycle

1. Create job (mode, estimates, manifest, chapters)
2. Optional schedule via job queue `autonomous_production`
3. Execute via WorkflowExecutor (or parallel child jobs)
4. Checkpoint (stages + chapter/scene indexes)
5. Pause / Resume / Cancel
6. Finalize with ProductionSummary + QC

## Project management objects

`ProductionJob` · `ExecutionContext` · `ExecutionState` · `Checkpoint` ·
`StageResult` · `ProductionManifest` · `ProductionSummary`

## Production modes

`single_video` · `video_series` · `podcast` · `course` · `marketing_campaign` ·
`documentary` · `animated_story` · `audiobook` · `educational_program` ·
`full_production`

## Checkpoint / long-form / recovery

- Job checkpoints: `data/production_jobs/checkpoints/`
- Workflow checkpoints: `data/workflow_runs/checkpoints/` (Agent 21)
- Chapters + scene groups; multi-unit fan-out for course/series/campaign
- Required failures stop; optional/distribution degrade; budget QC warnings

## Observability & QC

`get_status()` / `execution_log()` — stage, progress, elapsed/remaining,
provider usage, costs, failures, warnings, quality score.

`validate_job()` — pipeline failures, missing outputs, stage mismatches,
provider failures, budget overruns → `quality_score` 0–100.

## Extension guide

1. Add modes in `PRODUCTION_MODES` / `modes.py`
2. Append fields in `models.py` + `DATA_CONTRACTS.md`
3. Never call engines or vendor SDKs here
4. Use `PRODUCTION_JOB_TYPE` / `ensure_production_handler`

## Files

| Path | Role |
|---|---|
| `services/autonomous_production/executor.py` | Run controller |
| `services/autonomous_production/models.py` | Contracts |
| `services/autonomous_production/modes.py` | Mode resolution |
| `services/autonomous_production/estimates.py` | Cost/runtime |
| `services/autonomous_production/quality.py` | QC |
| `services/autonomous_production/longform.py` | Chapters/units |
| `services/autonomous_production/parallel.py` | Parallel units |
| `services/autonomous_production/scheduler.py` | Job queue |
| `services/autonomous_production/store.py` | Persistence |
| `services/autonomous_production/observability.py` | Logs |
| `tests/test_autonomous_production.py` | Coverage |
