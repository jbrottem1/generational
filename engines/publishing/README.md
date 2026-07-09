# Publishing & Distribution Engine — Agent 7 (LANDED, mock providers)

The publish stage of the AI Content Operating System. Consumes a completed
RenderPackage (Agent 6) and the optimization PublishingPackage (Agent 8)
and prepares content for every supported publishing provider: platform-
fitted metadata, timezone-aware scheduling, a durable retry-capable job
queue, mock publish execution, and full attempt history for the future
Analytics Engine. **No real platform API is called yet** — every adapter
is a deterministic mock behind the real interface.

## Responsibilities

- Build one platform-ready publish package per item × platform.
- Decide *when* to publish (immediate, explicit time, or the Optimization
  Engine's ranked publish windows, resolved timezone-aware per country).
- Queue, execute, retry, and track publish jobs; never crash the pipeline.
- Write the ContentPackage `publishing_package` slot and advance `status`
  to `scheduled` / `published`. Never mutate `render_package` (Agent 6)
  or the `publishing_packages` handover key (Agent 8).

## Module map

| Module | Role |
|---|---|
| `engines/publishing/engine.py` | `PublishingEngine` (key `publishing`) — thin ContractEngine façade over the service layer |
| `engines/publishing/scheduler_engine.py` | `SchedulerEngine` (key `scheduler`, graduated from `engines/future_stubs.py`) — emits `publish_schedule` |
| `services/publishing/manager.py` | `PublishingManager` — coordinates everything below |
| `services/publishing/package.py` | Platform publish package assembly (`PLATFORM_PUBLISH_PACKAGE_FIELDS`) |
| `services/publishing/queue.py` | `PublishingQueue` (jobs.json) + `PublishingHistory` (history.json) + `build_publishing_job` |
| `services/publishing/scheduler.py` | `PublishingScheduler` — immediate / explicit / optimal-window, timezone-aware |
| `services/publishing/retry.py` | `RetryManager` — exponential backoff, provider-specific policies, safe failure |
| `services/publishing/accounts.py` | Placeholder PublishingAccounts + `CredentialProvider` contract (no real credentials, ever) |
| `services/publishing/extensions.py` | Future-roadmap seams: `PrePublishGate`, `PublishListener`, `RollbackHandler`, `RegionalScheduleRule` |
| `services/publishing/models.py` | Field tuples + `JobStatus` + `DEFAULT_RETRY_POLICY` — the testable contract |
| `providers/publishing_provider.py` | The `PublishingProvider` interface every platform adapter implements |
| `providers/publishing/` | Mock adapters (YouTube Shorts, Instagram Reels, Facebook Reels, TikTok, X, LinkedIn, Pinterest) + registry |

## PublishingPackage format (per item × platform)

`PLATFORM_PUBLISH_PACKAGE_FIELDS` v1.0 (additive-only): `video`
(file_uri/duration/resolution/aspect_ratio/mock), `thumbnail`, `title`,
`description`, `hashtags`, `keywords`, `captions`, `language`, `country`,
`platform`, `provider`, `account` (placeholder reference), `publish_time`
(ISO-8601 UTC), `timezone` (audience UTC offset), `visibility`, `playlist`
(placeholder), `category` (placeholder), `status`
(prepared/blocked/published), `diagnostics`, `generated_at`. Metadata is
fitted to each platform's constraints by its adapter — truncation is
reported in `diagnostics.format_warnings`, never silent.

## Provider interface

`PublishingProvider` declares: `key` (canonical platform id) + `aliases`
(`youtube` → `youtube_shorts`), `constraints()` (title/description/
hashtag/duration limits, playlist/category support), `retry_policy()`
(per-platform overrides), `validate(package)` (blocking problems),
`format_metadata(package)` (fit + warn), and `publish(package)` (one
attempt → standardized result; must not raise for expected failures).
Adapters register via `register_publishing_provider()` — supporting a new
platform is one adapter file, zero engine changes. Never hardcode
platforms anywhere else.

## Scheduler

`PublishingScheduler.schedule(package, platform, mode, publish_time)`
returns a `PUBLISH_SCHEDULE_ENTRY_FIELDS` entry: immediate → now;
explicit ISO time → honored; otherwise the highest-ranked optimization
window for the platform, resolved from local window hours to UTC using
the country's audience timezone (`LOCALIZATION_TARGETS` offsets), falling
back to the country's default peak hour. Multiple brands, channels, and
countries schedule independently. `region_offset_hours()` is the seam
where a real timezone database plugs in.

## Queue lifecycle

```
prepare_jobs()                 execute_job()
     │                              │
  queued ──(scheduled mode)──▶ scheduled
     │                              │  due (scheduled_time / next_retry_at)
     └──────────────┬───────────────┘
                    ▼
               publishing ──▶ published            (terminal)
                    │
                 failure ──▶ queued (retry, backoff)
                    │           │ retries exhausted
                    │           ▼
                    └────────▶ failed              (terminal, history kept)
        cancel() at any non-terminal point ──▶ cancelled (terminal)
```

Jobs persist in `data/publishing_queue/jobs.json`; every attempt is
appended to `data/publishing_queue/history.json` with an `analytics_ref`
(Agent 9's correlation id). Structured log events: `publishing.job_enqueued`,
`publishing.published`, `publishing.retry_scheduled`, `publishing.job_failed`,
`publishing.job_cancelled`, `publishing.completed`, `scheduler.completed`.

## Retry system

`DEFAULT_RETRY_POLICY`: 3 retries, 30s base delay, ×2 exponential
backoff, 1h cap. Providers override per platform (`TikTokProvider`: 4
retries, 120s base). Exhausted jobs become `failed` with `last_error` and
full history intact — safe recovery, nothing raises, nothing is lost.

## Orchestrator integration

`run_publish_stage(context)` runs `scheduler` then `publishing` (stage
group `publish`). Input: items from `unified_packages` / `ideas` /
`selected_ideas` / `production_packages` + Agent 8's
`publishing_packages`. Output: `publish_schedule`, `publishing_result`
(the standardized PublishingResult, `PUBLISHING_RESULT_FIELDS`), and
`publishing_jobs`; each item's `publishing_package` slot is written.
Empty context → SKIPPED result, never a failure. `publish_mode` context
key: `immediate` (default for the engine) or `scheduled`.

## Future roadmap (interfaces only — do not implement here yet)

Official platform APIs (replace one mock adapter at a time) ·
multi-account publishing (`CredentialProvider` + `AccountRegistry`) ·
regional scheduling (`RegionalScheduleRule`) · approval workflows / human
review (`PrePublishGate` — already consulted before every publish) ·
analytics callbacks (`PublishListener` — already fired per attempt) ·
rollback on failures (`RollbackHandler`).

## Files Agent 7 must NOT touch

`app.py` · `core/workflows.py` · `engines/__init__.py` (append-only, with
review) · `engines/registry.py` · `engines/contracts.py` ·
`services/orchestrator/` · other agents' landing zones · `ui/` layout.

Tests: `tests/test_publishing_engine.py`. Read `AGENT_WORKFLOW.md`,
`ORCHESTRATOR.md`, and `DATA_CONTRACTS.md` §7 before changing contracts.
