# Executive Operating Model

Agent 24 implements a continuous company operating loop:

```
observe → analyze → prioritize → plan → delegate → execute → review → learn → optimize → repeat
```

## Phases

| Phase | Action |
|---|---|
| **observe** | Read shared context (market, analytics, learning, packages) |
| **analyze** | Score signals without calling engines |
| **prioritize** | Rank decisions by ROI, risk, confidence |
| **plan** | Build strategy, roadmap, resource allocation |
| **delegate** | Schedule orchestrator stages (names only) |
| **execute** | Invoke `Orchestrator.run_*_stage()` — never engines |
| **review** | Inspect delegation outcomes |
| **learn** | Persist observations to executive memory |
| **optimize** | Snapshot plan for next cycle |
| **repeat** | Ready for next run |

## Decision scoring

Each `ExecutiveDecision` includes:

- `roi_score`, `views_estimate`, `retention_estimate`
- `cost_estimate`, `revenue_estimate`
- `risk_score`, `confidence`, `priority`

## Resource allocation

`ExecutiveResourceAllocator` discovers engines via
`registry.describe_all()` and maps budget units to orchestrator stages.
It never executes engines.

## Health monitoring

`CompanyHealthMonitor` synthesizes analytics, learning, and risk signals
into `HealthLevel` bands: critical → warning → stable → growing → thriving.

## Memory

Executive memory lives at `data/executive/memory.json` — separate from
analytics and creative memory stores.

## Integration seams

1. **Manual stage:** `Orchestrator().run_executive_stage(context)`
2. **Hook:** `ExecutiveOrchestratorHook` (kind `learning`) via `attach_executive_hook()`
3. **Context keys:** merge `executive_*` outputs into the next run's context
