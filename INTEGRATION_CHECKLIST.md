# Integration Checklist — Psychology + Script Generation

Run this checklist top-to-bottom when the Psychology and Script Generation
agents have both landed, before declaring the combined pipeline stable.
Ownership and merge rules: see `AGENT_WORKFLOW.md`.

**State at time of writing (2026-07-08):** Psychology v7.1.0 is merged and
pushed (`239593e`). Script Generation is in progress and uncommitted — it is
touching shared files (`core/workflows.py`, `engines/__init__.py`,
`requirements.txt`, `services/ideation.py`), so steps 7–8 deserve extra care.

## Checklist

- [ ] **1. Pull latest main** — `git pull origin main`; working tree clean before starting (`git status`).
- [ ] **2. Confirm Psychology commit is present** — `git log --oneline | grep v7.1.0` shows `239593e v7.1.0 Psychology & Virality Engine`.
- [ ] **3. Confirm Script Generation commit is present** — a `v7.2.0`-series commit exists containing `engines/script_generation.py` (or its final module name) and its tests; no leftover uncommitted script work in the tree.
- [ ] **4. Run full tests** — `python -m pytest` passes with zero failures (baseline was 103 before Script Generation; expect more).
- [ ] **5. Launch Streamlit** — `streamlit run app.py` starts with no import errors or tracebacks in the terminal.
- [ ] **6. Test one full command end-to-end** — in the Ideas tab, run e.g. "Create 3 science shorts about black holes" and verify the flow Trend Discovery → Opportunity Ranking → Research → Psychology → Script: trend panel renders, psychology/viral scores appear per idea, scripts are generated, quality gate reports publishable counts.
- [ ] **7. Check for duplicate engines** — one module per engine `key`; verify `engines/script.py` vs new `engines/script_generation.py` don't both register a scripting stage, and `WORKFLOWS["intelligence"]` references each stage exactly once.
- [ ] **8. Check shared files for conflicts** — review the merged state of `core/workflows.py`, `engines/__init__.py`, `engines/heuristics.py`, `core/constants.py`, `services/ideation.py`, `services/production.py` (stage defs match workflow), `requirements.txt`, and `ui/components.py`; no clobbered registrations, no renamed/removed context keys.
- [ ] **9. Confirm docs are updated** — `README.md` has version sections for both releases; `MASTER_ARCHITECTURE.md` engine tables, pipeline diagram, version roadmap, and test count reflect the merged state.
- [ ] **10. Confirm next safe agent is Production Engine** — with the intelligence pipeline stable through Quality, the Render/Production Package agent starts next on `feature/render-package-engine`; add its ownership row to `AGENT_WORKFLOW.md` §2.1 before it writes code.

## If anything fails

Stop the next agent from starting. Fix on a feature branch, re-run the full
checklist, and only then hand off. `main` must remain releasable at all times.
