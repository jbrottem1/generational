# Landing Zone — Agent 8: SEO & Global Trend Optimization

## What this engine owns
Post-quality, pre-publish optimization across platforms, countries, and
languages: keyword expansion, title/description/hashtag optimization per
platform and locale, international opportunity detection, and search-intent
alignment. This is **distinct from** the live `seo` metadata-packaging
engine (`engines/seo.py`, part of the refinement stage) — that engine stays
owned by the Quality/refinement flow and must not be rewritten here.

## Files Agent 8 may edit
- `engines/seo/` (this folder — implementation modules live here; the
  `seo_optimization` contract stub in `engines/future_stubs.py` graduates
  into this folder, keeping key `seo_optimization`)
- `services/seo/` (create if needed)
- `providers/seo_provider.py` and keyword/SERP provider implementations
- `tests/test_seo_optimization.py` (create)

## Contracts it must use
- Subclass `engines.contracts.ContractEngine`; key `seo_optimization`.
- Input: `ContentPackage.seo_package`, `.keywords`, `.target_platforms`,
  `.target_country`, `.target_language`, trend context.
- Output: enrich `ContentPackage.seo_package` (per-platform/per-locale
  variants) and emit `seo_optimization_report`. **Add fields only — never
  remove or rename**, and never overwrite the base metadata produced by the
  refinement-stage `seo` engine; extend it.

## Outputs it must return
An enriched `seo_package` per ContentPackage plus `seo_optimization_report`
in the context (declared in the stub's `output_contract`).

## Files it must NOT touch
`engines/seo.py` (live refinement engine — different owner) · `app.py` ·
`core/workflows.py` · `engines/__init__.py` (append-only, with review) ·
`engines/registry.py` · `engines/contracts.py` · `services/orchestrator/` ·
other agents' landing zones · `ui/` layout.

Read `AGENT_WORKFLOW.md`, `ORCHESTRATOR.md`, and `DATA_CONTRACTS.md` before
writing code. Work on `feature/seo-optimization`.
