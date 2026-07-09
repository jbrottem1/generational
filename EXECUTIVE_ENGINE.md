# Executive Intelligence Engine (Agent 24)

The Executive Intelligence Engine is Generational's **company operating system
layer**. It observes shared pipeline context, prioritizes production
decisions, plans strategy, allocates resources, monitors health, and
delegates execution to the orchestrator — never calling peer engines directly.

## Engine key

- `autonomous_executive` (Agent 24)

## Pipeline position

Manual stage / `OrchestratorHook` — **NOT** in `DISTRIBUTION_STAGES`.

```
Context signals → Executive Intelligence → executive_* context keys
                      ↓ (delegate only)
                 Orchestrator stages
```

## Quick start

```python
import engines  # registers all engines
from engines import registry
from services.orchestrator import Orchestrator

# Direct engine run
updates = registry.get_engine("autonomous_executive").run({
    "market_opportunities": [...],
})

# Orchestrator stage
report = Orchestrator().run_executive_stage(context)

# Hook (runs after pipeline completion)
from services.executive import attach_executive_hook
attach_executive_hook()
```

## Output contract

| Context key | Description |
|---|---|
| `executive_summary` | Run status, decision counts, health level |
| `executive_plan` | Vision, priorities, decisions, roadmap, resources |
| `executive_dashboard` | KPIs, queue, goals, engine inventory |
| `executive_reports` | Daily/weekly/monthly/quarterly/annual/campaign/growth/summary/production/financial |
| `executive_loop` | Operating loop phase trace and delegations |
| `executive_packages` | Per-item `executive_package` slot payloads |

## ContentPackage slot

Agent 24 writes **`executive_package`** on each item in `unified_packages`.
All other slots are read-only.

## Architecture rules

1. Never import peer `engines.*` modules (lazy `registry.describe_all()` only).
2. Never call other engines — coordinate via shared context and orchestrator.
3. Execute phase delegates to `Orchestrator.run_*_stage()` only.
4. Never crash the pipeline — degrade to diagnostics on failure.

## Landing zone

- `engines/executive.py` — thin `ContractEngine` adapter
- `services/executive/` — models, memory, planner, loop, reports, hook

See also: `EXECUTIVE_OPERATING_MODEL.md`, `DATA_CONTRACTS.md`, `PIPELINE_SPEC.md`.
