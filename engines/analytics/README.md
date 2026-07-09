# Landing Zone — Agent 9: Analytics & Learning

**Status: LANDED (v9.2).** The `analytics` and `learning` engines are live
`ContractEngine`s. Implementation lives in `services/analytics/`,
`services/learning/`, and `providers/analytics/`; full documentation in
`ANALYTICS_LEARNING.md` and `DATA_CONTRACTS.md` §8.

## What this engine owns
Closing the loop: post-publish performance ingestion (views, retention
curves, watch time, engagement, follows), attribution of outcomes back to
the upstream decisions that produced them, and learning signals that retune
trend selection, psychology weights, script styles, and posting strategy.

## Files Agent 9 may edit
- `engines/analytics/` (this folder — implementation modules live here)
- `engines/analytics.py`, `engines/learning.py` (upgrade the planned stubs)
- `services/analytics/`, `services/learning/` (create if needed)
- `providers/analytics_provider.py` and per-platform implementations
- `services/knowledge.py` performance categories (with caution — shared)
- `tests/test_analytics_engine.py`, `tests/test_learning_engine.py` (create)

## Contracts it must use
- Subclass `engines.contracts.ContractEngine`; keys `analytics` / `learning`.
- Input: `ContentPackage.publishing_package`, `.analytics_placeholder`,
  platform APIs behind `AnalyticsProvider`.
- Output: write into `ContentPackage.analytics_package` (performance over
  time) and `ContentPackage.learning_metadata` (signals, weight adjustments,
  confidence). **Add fields only — never remove or rename.**
- Learning outputs feed upstream through `OrchestratorHook` (kind
  `"analytics"` / `"learning"`) — attach hooks; do not edit the orchestrator.

## Outputs it must return
Populated `analytics_package` and `learning_metadata` per ContentPackage;
`LearningSignal`-style records for the Knowledge Base.

## Files it must NOT touch
`app.py` · `core/workflows.py` · `engines/__init__.py` (append-only, with
review) · `engines/registry.py` · `engines/contracts.py` ·
`services/orchestrator/` (attach hooks instead) · other agents' landing
zones · `ui/` layout.

Read `AGENT_WORKFLOW.md`, `ORCHESTRATOR.md`, and `DATA_CONTRACTS.md` before
writing code. Work on `feature/analytics-learning`.
