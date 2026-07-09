# Landing Zone — Agent 7: Publishing & Scheduler

## What this engine owns
Getting content live: platform account management, per-platform metadata
formatting, optimal-window scheduling, the publish queue with retries, and
publish status tracking.

## Files Agent 7 may edit
- `engines/publishing/` (this folder — implementation modules live here)
- `engines/publishing.py` (upgrade the planned stub, key `publishing`)
- The `scheduler` contract stub in `engines/future_stubs.py` graduates into
  this folder as its own module (keep key `scheduler`)
- `services/publishing/` (create if needed), `services/assets.py` publishing queue (with caution)
- `providers/publishing_provider.py` and per-platform provider implementations
- `tests/test_publishing_engine.py` (create)

## Contracts it must use
- Subclass `engines.contracts.ContractEngine`; keys `publishing` / `scheduler`.
- Input: `ContentPackage.render_package`, `.seo_package`, `.target_platforms`,
  plus `Channel`/`PlatformAccount` config from `services/channels.py`.
- Output: write into `ContentPackage.publishing_package` (schedule, account,
  platform post IDs, URLs, publish times) and set `status="scheduled"` /
  `"published"`. **Add fields only — never remove or rename.**
- Platform SDKs/APIs live behind `PublishingProvider` — never in engine logic.

## Outputs it must return
A populated `publishing_package` per ContentPackage; scheduling decisions in
`publish_schedule` context key (declared in the `scheduler` stub contract).

## Files it must NOT touch
`app.py` · `core/workflows.py` · `engines/__init__.py` (append-only, with
review) · `engines/registry.py` · `engines/contracts.py` ·
`services/orchestrator/` · other agents' landing zones · `ui/` layout.

Read `AGENT_WORKFLOW.md`, `ORCHESTRATOR.md`, and `DATA_CONTRACTS.md` before
writing code. Work on `feature/publishing-scheduler`.
