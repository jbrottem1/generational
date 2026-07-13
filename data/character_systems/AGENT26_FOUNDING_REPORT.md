# AGENT 26 FOUNDING REPORT — Character Systems Department

**Agent:** 26 — Character Systems Director  
**Date:** 2026-07-11  
**Status:** COMPLETED  
**Recommendation:** **ACCEPT**

---

## Objective

Establish the permanent Character Systems department package with flagship **Professor Gen** (`CHAR-PROFESSOR-001`).

---

## Completed

1. **CHARACTER_BIBLE.md** — single source of truth at `data/character_systems/CHARACTER_BIBLE.md` + root pointer `CHARACTER_BIBLE.md`
2. **PROFESSOR_PROFILE.md** — full personality, teaching philosophy, voice (`nova`/`tts-1-hd`), humor, signature behaviors
3. **CHARACTER_LIBRARY.md** — idle/gesture/pose/expression catalog mapped to `GESTURE_POSES` + planned slots
4. **ANIMATION_STYLE_GUIDE.md** — motion constraints for Agent 16; Foundation white studio aligned
5. **CHARACTER_QC_CHECKLIST.md** — production verification checklist
6. **registry.json** — reusable animation asset registry (all current `GESTURE_POSES` locked + planned slots)
7. **CHAR-PROFESSOR-001/** — CHARACTER.md, design_spec, expression_sheet, gesture_sheet, turnaround notes + PNGs
8. **services/character_systems/** — validation rules + `load_character` / `validate_production_character`
9. **tests/test_character_systems.py** — 13 tests, all passing
10. **Universe registry** — Gen registered; Dash + Stick remain locked with documented relationships

---

## Executive deliverables checklist (7)

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | CHARACTER_BIBLE | Present |
| 2 | PROFESSOR_PROFILE | Present |
| 3 | CHARACTER_LIBRARY | Present |
| 4 | ANIMATION_STYLE_GUIDE | Present |
| 5 | CHARACTER_QC_CHECKLIST | Present |
| 6 | registry.json | Present |
| 7 | Consistency validation (code + tests) | Present + passing |

---

## Files created / updated

### Created

- `CHARACTER_BIBLE.md` (root pointer)
- `data/character_systems/CHARACTER_BIBLE.md`
- `data/character_systems/PROFESSOR_PROFILE.md`
- `data/character_systems/CHARACTER_LIBRARY.md`
- `data/character_systems/ANIMATION_STYLE_GUIDE.md`
- `data/character_systems/CHARACTER_QC_CHECKLIST.md`
- `data/character_systems/registry.json`
- `data/character_systems/AGENT26_FOUNDING_REPORT.md`
- `data/universe/characters/CHAR-PROFESSOR-001/CHARACTER.md`
- `data/universe/characters/CHAR-PROFESSOR-001/design_spec.json`
- `data/universe/characters/CHAR-PROFESSOR-001/expression_sheet.json`
- `data/universe/characters/CHAR-PROFESSOR-001/gesture_sheet.json`
- `data/universe/characters/CHAR-PROFESSOR-001/turnaround_notes.md`
- `data/universe/characters/CHAR-PROFESSOR-001/turnaround_front.png`
- `data/universe/characters/CHAR-PROFESSOR-001/turnaround_sheet.png`
- `services/character_systems/__init__.py`
- `services/character_systems/validation.py`
- `tests/test_character_systems.py`

### Updated

- `data/universe/registry.json` — added `CHAR-PROFESSOR-001`; annotated Dash/Stick relationships; set `foundation_flagship_character`

---

## Tests

```text
./venv/bin/pytest tests/test_character_systems.py -q
.............  13 passed
```

Covered: load Gen, palette reject, id mismatch, proportion reject, wave spam / react forbidden for professor, registry covers all `GESTURE_POSES` + planned keys, universe registry continuity.

---

## Problems / notes

1. **Lab coat gated (RESOLVED in REVISION)** — `professor=True` no longer implies coat; default `coat=False` / `attire="none"`. MacroCenter may opt in later via `coat=True` / `attire="lab_coat"` with a version bump.
2. **Default `StickFigureSpec.character_id`** remains `CHAR-STICK-001` — intentional backward compatibility; Gen production must pass explicit Gen spec.
3. **Planned gestures** (`greeting`, `listening`, `celebrating`, …) are documented with fallbacks; not yet in `GESTURE_POSES`.

---

## Risks

| Risk | Mitigation |
|------|------------|
| Coat vs clean-stick contradiction in educator renders | **RESOLVED** — coat gated; Foundation passes coat=False |
| Scripts inventing gesture keys | Registry + validate_gesture rejects unknowns |
| Accidental Dash merge | Relationship notes + locked statuses |

---

## Recommendations

1. **ACCEPT** Character Systems founding package (+ coat-drift REVISION).
2. Agent 16: wire Foundation renders to Gen `StickFigureSpec` + enforce forbidden gestures from `FORBIDDEN_PROFESSOR_GESTURES`.
3. ~~Agent 16: resolve coat vs clean-stick~~ — **done** (coat gated off by default).
4. Agent 5: optionally default Foundation voice requests to `nova` / `tts-1-hd` from design_spec (preference already documented).
5. Next version: implement planned gesture keys in `GESTURE_POSES` with library fallbacks retired.

---

## Decision

**ACCEPT** — all seven executive deliverables exist; tests pass; Dash and Stick remain locked; Gen is Foundation flagship host.

---

## REVISION — 2026-07-11 (Agent 0 coat-drift REJECT fix)

**Status:** COMPLETED · **Recommendation:** **ACCEPT**

### Blocker addressed

`draw_stick_figure(professor=True)` previously always drew a lab coat + teal accents. Character Bible / PROJECT FOUNDATION lock Gen as **clean black stick, white face, no coat**.

### Changes

1. **`services/animation/stick_figure.py`** — added `coat: bool = False` and `attire` (draw arg + `StickFigureSpec.attire="none"`). Coat polygon/teal accents gated; `professor=True` alone never draws a coat. Opt-in via `coat=True` or `attire="lab_coat"`.
2. **`services/animation/performer.py`** — Foundation / educator path passes `coat=False`, `attire="none"` for Gen demos.
3. **`design_spec.json` / StickFigureSpec** — `attire: "none"` locked; `lab_coat_in_foundation` listed under forbidden.
4. **`validation.py`** — `validate_attire` flags `attire=="lab_coat"` for `CHAR-PROFESSOR-001`.
5. **Turnaround PNGs** — regenerated with professor plate, no coat.
6. **Docs** — one-line coat forbidden notes in CHARACTER_BIBLE, PROFESSOR_PROFILE, ANIMATION_STYLE_GUIDE, CHARACTER.md, turnaround_notes.
7. **Tests** — coat-off pixel check + coat opt-in still works; attire reject for Gen.

### Tests

```text
./venv/bin/pytest tests/test_character_systems.py -q
.................  16 passed (includes coat gate + attire reject)
```

### Decision

**ACCEPT** — coat gated off by default for Gen; MacroCenter coat path preserved behind explicit opt-in; tests pass.
