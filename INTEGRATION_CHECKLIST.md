# Engine Integration Checklist (v9.6)

Run this checklist top-to-bottom for **every new engine or agent** before
its work merges to `main`. It replaces the one-off v7.1 checklist; the
Creative Studio integration gap (engine built but never registered — nine
failing tests) is exactly the class of failure this list prevents.

## Before writing code

- [ ] **1. Claim your identity** — agent row in `AGENT_REGISTRY.md`, engine
  key(s) in `ENGINE_REGISTRY.md`, ownership row in `AGENT_WORKFLOW.md` §2.1.
- [ ] **2. Read the directives** — `ARCHITECTURE_DIRECTIVES.md` (Directive
  #1: never import another engine), `DATA_CONTRACTS.md`, your landing-zone
  README if one exists.
- [ ] **3. Reserve your package slot** — if you need a new ContentPackage
  field, add it (additive-only) to `services/orchestrator/models.py` AND
  `PRODUCTION_PACKAGE_FIELDS` AND `DATA_CONTRACTS.md` §1 — with Agent 1 review.
- [ ] **4. Branch** — `feature/<subsystem-name>` off latest `main`.

## While building

- [ ] **5. Subclass `ContractEngine`** — declare `version`,
  `input_contract`, `output_contract`, `dependencies` (registered keys
  only), `capabilities`.
- [ ] **6. Vendor code behind providers** — SDKs/APIs live in `providers/`,
  swappable per file; engines/services import interfaces only.
- [ ] **7. Degrade, never crash** — empty input → a "no items" summary;
  broken item → per-item diagnostics; missing provider → mock/demo mode.

## Before committing

- [ ] **8. Register the engine** — import + registration loop entry in
  `engines/__init__.py` (append-only). *An unregistered engine is invisible
  to the orchestrator and every test that resolves it by key.*
- [ ] **9. Wire the stage** — `STAGE_GROUPS` (and `STAGE_OF_ENGINE` /
  `DISTRIBUTION_STAGES` / `WORKFLOWS` if the full pipeline should run it) —
  Agent 1 review.
- [ ] **10. Run the FULL suite** — `python3 -m pytest tests/` — all green,
  including `tests/test_architecture.py` (import rules, registry/stage
  consistency, dependency-graph validity).
- [ ] **11. Update docs** — `README.md` version section,
  `PIPELINE_SPEC.md` flow + stage table, `ENGINE_REGISTRY.md`,
  `DATA_CONTRACTS.md` for new context keys, your subsystem doc.
- [ ] **12. Commit only owned files** — stage by explicit path; check
  `git status` before and after.

## After merging

- [ ] **13. Streamlit smoke test** — `streamlit run app.py` launches; one
  full command runs end to end.
- [ ] **14. Verify the machine registries** — your engine appears in
  `registry.describe_all()`, `registry.capability_index()`, and (if it
  declares dependencies) `registry.dependency_graph()`.

## If anything fails

Stop the next agent from starting. Fix on the feature branch, re-run the
checklist, and only then hand off. `main` must remain releasable at all times.
