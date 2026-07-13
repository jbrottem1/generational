# Technical Debt Report

**Owner:** Agent 28 · **Prioritized by impact** · **Updated:** 2026-07-12

---

## P0 — Blocks reliable release

| ID | Debt | Impact | Owner | Fix |
|----|------|--------|-------|-----|
| TD-01 | **13 pytest failures** (render_engine, research_engine, engines, workflows, project workspace) | Regression blind spot | Agent 1 + 6 + 11 | Fix failing tests; root-cause NameError in research_engine |
| TD-02 | **Live OAuth / API keys** absent in default env | Publish/analytics loop blocked | Agent 7 + 19 | Operator credential setup; document dry-run path |

## P1 — Quality / maintainability

| ID | Debt | Impact | Owner | Fix |
|----|------|--------|-------|-----|
| TD-03 | **Phoneme lip-sync stub** (amplitude only) | Teaching quality ceiling ~77–79 | Agent 16 | Phoneme driver after Foundation ≥80 stable |
| TD-04 | **Atlas UI browser** not shipped | Operator cannot browse library | Agent 20 | Studio tab for Knowledge Atlas |
| TD-05 | **biology_academy / physics series** not on Atlas path | Inconsistent visual evidence | Agent 3 + 4 | Port export scripts to `plan_visual_evidence()` |
| TD-06 | **Dual catalog** Reality JSON + Atlas JSON | Sync drift risk | Agent 4 | Single ingest pipeline; Reality reads from Atlas |

## P2 — Cleanup

| ID | Debt | Impact | Owner | Fix |
|----|------|--------|-------|-----|
| TD-07 | **streamlit import** in `core.ai.openai_provider` breaks lean test imports | CI friction | Agent 19 | Lazy import or test shim |
| TD-08 | **MacroCenter / rich environments** deferred but code remains | Confusion vs Foundation doctrine | Agent 16 | Document deprecation path in PROJECT_FOUNDATION |
| TD-09 | **Sprint report cycle-count drift** vs sprint_state.json | Executive reporting accuracy | Agent 0 | Single source of truth |
| TD-10 | **Duplicate readiness** (`services/readiness`, `studio/readiness`, Agent 28) | Overlap | Agent 28 | Agent 28 wraps existing; document ownership |

## P3 — Organizational

| ID | Debt | Impact | Owner | Fix |
|----|------|--------|-------|-----|
| TD-11 | **Agent 22 Autonomous Executive** planned not staffed | Executive automation gap | Agent 0 | Roadmap decision |
| TD-12 | **Marketing / Legal / Finance** unstaffed | GTM limits | Agent 0 | Reserved slots |
| TD-13 | **Demo library registry** backlog in GCIS reusable_assets | Reuse tracking | Agent 27 | Version + reuse_count registry |

---

## Overlapping responsibilities (resolve)

| Area | Agents | Resolution |
|------|--------|------------|
| Visual evidence | Agent 4, 14, Reality, Atlas | Atlas = curated evidence; Agent 14 = generated assets; Agent 4 owns selection |
| Readiness scoring | Agent 17, 28, `services/readiness` | Agent 28 owns **release gate**; Agent 17 owns **content QC** |
| Standards | Agent 27, GCIS | Agent 27 indexes; GCIS canonical lessons log |

---

## Debt paydown order (Executive approved)

1. TD-01 (test failures)  
2. TD-05 (series Atlas rollout)  
3. TD-03 (lip-sync)  
4. TD-04 (Atlas UI)  
5. TD-06 (catalog unification)
