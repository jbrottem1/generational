# AGENT 27 FOUNDING REPORT — Knowledge & Standards Department

**Agent:** 27 — Knowledge & Standards Director  
**Date:** 2026-07-11  
**Status:** COMPLETED  
**Recommendation:** **ACCEPT**

---

## Objective

Found the permanent Knowledge & Standards department package. Make institutional memory searchable and compounding. Index and elevate GCIS — do not duplicate conflicting lesson bodies.

---

## Completed

1. **COMPANY_WIKI.md** — operating manual hub (How we produce · Standards · Characters · Knowledge capture · Where to look)
2. **PRODUCTION_STANDARDS.md** — LOCKED / ASPIRATIONAL across animation, teaching, voice, lip-sync, script, pacing, render, publish, brand, character, docs, testing
3. **PROMPT_LIBRARY.md** — versioned categories + 6 approved v1 patterns + GCIS successful/failed index
4. **LESSONS_LEARNED.md** — index + executive summaries (ES001, coat revision, Fluid Motion, Sprint 6h30, Foundation); full log remains GCIS
5. **EXPERIMENT_REGISTRY.md** + **experiments.json** — 6 real experiments with evidence paths
6. **BEST_PRACTICES.md** — validated required practices
7. **STYLE_GUIDES.md** — index-only pointers (no restatement)
8. **registry.json** — manifest with owners (27, gcis, 26, 16, 15, 0)
9. **Root** `COMPANY_WIKI.md` pointer
10. **services/knowledge_standards/** — `capture.py` + `validation.py`
11. **tests/test_knowledge_standards.py**
12. **GCIS INDEX** updated with Agent 27 package link

---

## Problems encountered

- GCIS `lessons_learned.md` already had newest entries above the formal header — left intact (append-only; no wholesale rewrite).
- Sprint 6h30 cycle-count drift (3 vs 5) documented in experiment lessons, not “fixed” inventively.
- Voice defaults differ slightly between GCIS STD-VOICE-001 (`onyx`) and Gen Character Bible (`nova`) — both cited; series lock wins for Gen.

---

## Files created / updated

### Created

- `COMPANY_WIKI.md` (root pointer)
- `data/knowledge_standards/COMPANY_WIKI.md`
- `data/knowledge_standards/PRODUCTION_STANDARDS.md`
- `data/knowledge_standards/PROMPT_LIBRARY.md`
- `data/knowledge_standards/LESSONS_LEARNED.md`
- `data/knowledge_standards/EXPERIMENT_REGISTRY.md`
- `data/knowledge_standards/experiments.json`
- `data/knowledge_standards/BEST_PRACTICES.md`
- `data/knowledge_standards/STYLE_GUIDES.md`
- `data/knowledge_standards/registry.json`
- `data/knowledge_standards/AGENT27_FOUNDING_REPORT.md`
- `services/knowledge_standards/__init__.py`
- `services/knowledge_standards/capture.py`
- `services/knowledge_standards/validation.py`
- `tests/test_knowledge_standards.py`

### Updated

- `data/gcis/knowledge/INDEX.md` — link to Agent 27 package

---

## Tests

```bash
./venv/bin/python -m pytest tests/test_knowledge_standards.py -q
```

Result: **10 passed** (capture, validation, registry load, anti-duplication check, named docs).

---

## Risks

| Risk | Mitigation |
|------|------------|
| Agents still write only to GCIS and skip experiment registry | Capture API + wiki “Knowledge capture” section; post-sprint checklist |
| PRODUCTION_STANDARDS drifts from GCIS standards.md | Explicit dual-cite; revise via Agent 0, not silent fork |
| Prompt library grows without version bumps | v1 IDs + GCIS failed.md as retired source |

---

## Recommendations

1. **ACCEPT** this founding package — success criteria met.  
2. After every future sprint: `register_experiment` + GCIS lesson append + optional wiki index line.  
3. Next elevation: auto-link AELS / quality JSON into experiment metrics fields.  
4. Keep MacroCenter / phonemes marked ASPIRATIONAL until Foundation ≥80 is stable.

---

## Success criteria check

| Criterion | Evidence |
|-----------|----------|
| All 7 named docs exist | `data/knowledge_standards/{COMPANY_WIKI,PRODUCTION_STANDARDS,PROMPT_LIBRARY,LESSONS_LEARNED,EXPERIMENT_REGISTRY,BEST_PRACTICES,STYLE_GUIDES}.md` |
| No conflicting full lessons duplicate | Index points to GCIS; test asserts shorter + no anti-patterns wholesale copy |
| experiments.json ≥4 real experiments | 6 entries with evidence paths |
| pytest passes | `tests/test_knowledge_standards.py` |
| Recommend ACCEPT only if met | **ACCEPT** |
