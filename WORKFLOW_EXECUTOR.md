# Workflow Executor (Agent 21)

End-to-end production run controller for Generational. Turns one user prompt
into a durable `ProjectRun` that drives the Orchestrator stage-by-stage with
checkpoints, retries, graceful degradation, and Studio UI status.

```python
from services.workflow_executor import get_workflow_executor

executor = get_workflow_executor()
run = executor.execute("Create a 45-second YouTube Short about black holes.")
status = executor.get_status(run.run_id)
# status["current_stage"], status["progress"], status["errors"], ...
```

**Not** a UI agent. **Not** a provider integration agent. **Not** a rewrite of
existing engines. Coordination only — Orchestrator runs stages; ProviderRuntime
serves external AI calls.

---

## Architecture

```
User prompt
   ↓
WorkflowExecutor.create_run()     → ProjectRun + WorkflowRun + WorkflowSteps
   ↓
resolve production type / template
   ↓
for each WorkflowStep:
   Orchestrator.run_stage()       (or _run_production / _run_packaging)
   ProviderRuntime (inside engines, never called directly here)
   checkpoint + persist
   retry / degrade / stop
   ↓
WorkflowResult + package slots + studio_status()
```

| Layer | Role |
|---|---|
| `WorkflowExecutor` | Durable run controller |
| `Orchestrator` | Stage execution (unchanged contracts) |
| `ProviderRuntime` | External AI (usage/cost surfaced in status) |
| `WorkflowRunStore` | JSON persistence under `data/workflow_runs/` |

---

## State model

| Object | Purpose |
|---|---|
| `ProjectRun` | Top-level durable production run |
| `WorkflowRun` | Planned step sequence + progress |
| `WorkflowStep` | One stage with attempts / status |
| `WorkflowStatus` | `pending` · `running` · `completed` · `failed` · `skipped` · `waiting` · `retrying` · `cancelled` |
| `Checkpoint` | Resume point (completed stages + context snapshot) |
| `RetryPolicy` | max retries, backoff, optional skip, distribution degrade |
| `ExecutionLog` | Append-only event log |
| `WorkflowResult` | Final/partial outputs + package slots |
| `FailureReport` | Structured per-stage failure |
| `WorkflowConfig` | Templates, stage order, timeouts, budget, long-form, providers |

---

## Checkpoint system

After every stage the executor writes:

1. `data/workflow_runs/{run_id}.json` — full `ProjectRun`
2. `data/workflow_runs/checkpoints/{run_id}.json` — `Checkpoint`

Resume:

```python
executor.resume(run_id)
```

Failed/interrupted steps reset to `pending` with attempt counter cleared;
completed stages are skipped.

---

## Retry & recovery

- Required intelligence failures → retry then **stop** (partial outputs kept)
- Optional / distribution failures → **degrade to skipped**, continue
- `RetryPolicy.max_retries` (default 2) + optional backoff
- Workflow-level `timeout_sec` aborts with a recoverable failure report
- `cancel(run_id)` marks remaining steps cancelled

---

## Long-form execution

Production types: `youtube_short`, `documentary`, `course`, `podcast`,
`animated_episode`, `campaign`, `longform`, `full_production`.

Inferred from the prompt (e.g. “12-minute documentary” → documentary +
`longform_mode=True`). Long-form runs use the same checkpoint/resume path;
ETA hints are more conservative for Studio UI.

---

## UI integration (Agent 20 Studio)

```python
executor.get_status(run_id)
# or studio_status(run)
```

Returns: `current_stage`, `progress`, `errors`, `outputs`,
`estimated_completion`, `provider_usage`, `costs`, `logs`, `steps`.

Job queue type: `workflow_run` via `ensure_workflow_handler(queue)`.
Also registered by `ensure_runtime_handlers(queue)`.

---

## Configuration

```python
from services.workflow_executor import WorkflowConfig, RetryPolicy

config = WorkflowConfig(
    template="documentary",          # or youtube_short, intelligence_only, ...
    stage_order=[],                  # empty = full canonical plan
    optional_stages=["animation"],
    skip_stages=[],
    retry_policy=RetryPolicy(max_retries=2),
    timeout_sec=0,                   # 0 = no global timeout
    quality_level="high",
    budget_usd=5.0,
    platform_targets=["youtube"],
    provider_preferences={"optimize_for": "quality"},
    longform_mode=True,
    publish_mode="scheduled",
)
run = executor.execute("Create a documentary about Rome", config=config)
```

Templates live in `services/workflow_executor/templates.py`.

---

## Outputs

`WorkflowResult` aggregates:

- `packages` (ContentPackage dicts)
- `production_package` / `asset_package` / `animation_package` /
  `post_production_package` / `render_package` / `publishing_package` /
  `analytics_package` / `learning_context`
- `production_report`, `failure_reports`, `provider_usage`, `estimated_cost_usd`

---

## Extension guide

1. Add a template in `TEMPLATES` / `PRODUCTION_TYPES` (do not reorder
   orchestrator stages — filter/annotate only).
2. New durable fields: append to dataclasses in `models.py` + `DATA_CONTRACTS.md`.
3. Do **not** call engines or vendor SDKs from this package.
4. Wire Studio polling to `get_status()`; Agent 20 schedules via job queue.

---

## Files

| Path | Role |
|---|---|
| `services/workflow_executor/executor.py` | Run controller |
| `services/workflow_executor/models.py` | State contracts |
| `services/workflow_executor/templates.py` | Production types + stage plans |
| `services/workflow_executor/store.py` | Persistence |
| `services/workflow_executor/policy.py` | Retry / degrade / progress |
| `services/workflow_executor/status.py` | Studio UI projection |
| `tests/test_workflow_executor.py` | Coverage |
