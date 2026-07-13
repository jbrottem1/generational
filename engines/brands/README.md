# Landing Zone — Agent 10: Multi-Brand Operating System

## What this engine owns
Operating many brands in parallel: the Business/Brand entity (identity,
niche, voice profile, visual identity, audience, cadence, SEO/psychology
profiles, revenue, learning history), per-brand channel and account
management, and brand strategy updates driven by learning signals.

## Files Agent 10 may edit
- `engines/brands/` (this folder — implementation modules live here; the
  `brand_management` contract stub in `engines/future_stubs.py` graduates
  into this folder, keeping key `brand_management`)
- `services/brands/` (create), growing from `services/channels.py`
  (extend it with caution — it is live and tested; never break existing
  channel data on disk)
- `tests/test_brand_management.py` (create)

## Contracts it must use
- Subclass `engines.contracts.ContractEngine`; key `brand_management`.
- Input: `ContentPackage.learning_metadata`, `.analytics_package`, existing
  channel config from `services/channels.py`.
- Output: set `ContentPackage.brand_id` / `.channel_id` at packaging time
  (coordinate the packager change with Agent 1), and emit
  `brand_strategy_update` in the context. **Add fields only — never remove
  or rename.**
- Per-brand pipeline runs go through `Orchestrator.run_full_pipeline`
  (one call per brand/command) — never through engines directly.

## Outputs it must return
Brand entities (serializable, versioned, ID-carrying) and
`brand_strategy_update` records; downstream stages read brand context from
the ContentPackage, never from brand internals.

## Files it must NOT touch
`app.py` · `core/workflows.py` · `engines/__init__.py` (append-only, with
review) · `engines/registry.py` · `engines/contracts.py` ·
`services/orchestrator/` (coordinate packager changes with Agent 1) ·
other agents' landing zones · `ui/` layout.

Read `AGENT_WORKFLOW.md`, `ORCHESTRATOR.md`, and `DATA_CONTRACTS.md` before
writing code. Work on `feature/multi-brand-os`.
