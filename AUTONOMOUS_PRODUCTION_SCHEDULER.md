# Autonomous Production Scheduler

Agent 0 operating loop that turns Generational into an autonomous AI media OS.

**Architecture is frozen.** This layer does **not** add rendering, scripting, publishing, research, or analytics engines. It only orchestrates:

- Trend Intelligence (`services.trend_opportunity`)
- GenOS production queue (`services.generational_os.scheduler`)
- Production Operations (`run_studio_ops` via `core.jobs`)
- GenOS media library + Channel OS packaging
- Publishing queue **preparation only** (execution remains opt-in)

## Workflow

```
Trend Intelligence
    ↓
Production Queue (GenOS)
    ↓
Autonomous Scheduler tick
    ↓
Research → Psychology → Script → Scene Builder → World/Media
    → Asset Resolution → Voice → Cinematic Director → Renderer → QA
    ↓
Library
    ↓
Publishing Queue (disabled unless enabled)
```

## Job fields

Each GenOS job row stores:

| Field | Description |
|---|---|
| `topic` | Production topic |
| `category` | Category / domain |
| `priority` | Higher runs first |
| `target_channel` | Channel OS brand id (optional) |
| `narrator` | Narrator profile |
| `world` | World selection id |
| `estimated_duration_sec` | Target runtime |
| `status` | queued / running / succeeded / failed / retry_queued |
| `retry_count` | Recovery attempts |
| `start_time` / `completion_time` | Timing |
| `failure_reason` | Last failure |
| `quality_score` | Ops / creative score after finish |

## CLI

```bash
# Dashboard metrics
./venv/bin/python scripts/autonomous_scheduler.py dashboard

# Trend → queue
./venv/bin/python scripts/autonomous_scheduler.py ingest --category science --queue 5

# Run next job
./venv/bin/python scripts/autonomous_scheduler.py tick

# Ingest + drain N jobs (publishing off)
./venv/bin/python scripts/autonomous_scheduler.py run --queue 3 --execute 2

# Manual enqueue
./venv/bin/python scripts/autonomous_scheduler.py enqueue --topic "How bees dance" --category Biology --priority 90

# Queue snapshot
./venv/bin/python scripts/autonomous_scheduler.py queue
```

Publishing prep flag only (still does not auto-publish):

```bash
./venv/bin/python scripts/autonomous_scheduler.py run --publish --execute 1
```

## Dashboard

- JSON: `data/autonomous_scheduler/SCHEDULER_DASHBOARD.json`
- Markdown: `AUTONOMOUS_SCHEDULER_DASHBOARD.md`
- Metrics log: `data/autonomous_scheduler/METRICS.jsonl`

Displays: waiting, running, completed, failed, retry queue, average render time, average quality, success rate, today’s output, weekly output.

## Recovery policy

Uses existing GenOS `classify_error` / `should_retry`:

- **Retry:** network, API limit, provider, voice, render, missing assets
- **Skip / fail:** authentication, quality failure, exhausted retries
- Success requires a physical MP4 (aligned with production reliability truth)

## Composition map

| Responsibility | Existing call |
|---|---|
| Rank topics | `run_trend_opportunity` |
| Select + queue | `schedule_production` |
| Launch | `run_next_job` → ops handler → `run_studio_ops` |
| Organize | `register_library_entry` + `package_channel_production` |
| Publish prep | `PublishingManager.prepare_jobs` (no execute) |
| Summaries | `write_scheduler_dashboard` + metrics JSONL |

## Durability note

`core.jobs` is in-process. GenOS `PRODUCTION_QUEUE.json` is durable. Before each tick, `run_next_job` **rehydrates** missing live jobs from GenOS metadata and recovers stale `running` rows after crashed CLI processes.

## Validated

Autonomous batch (`run --skip-ingest --execute 2`) completed **2/2** productions with library organization and dashboard metrics (publishing disabled).
