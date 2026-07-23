# CHARACTER BIBLE — Generational Character Systems

**Owner:** Agent 26 (Character Systems Director)  
**Status:** LOCKED · Single source of truth  
**Established:** 2026-07-11  
**Package:** `data/character_systems/`

---

## Purpose

This bible defines **who** Generational characters are — identity, proportions, palette, personality, and reusable performance libraries.

- **Agent 26** owns character identity and consistency.
- **Agent 16** owns on-screen motion execution.
- **Agent 15** owns universe IP continuity across brands.

Silent redesigns are forbidden. Any visual change requires a version bump and Agent 0 approval.

---

## Studio alignment (PROJECT FOUNDATION)

Character Systems **must not contradict** the Foundation white studio:

| Rule | Spec |
|------|------|
| Background | Pure white `(255, 255, 255)` |
| Ground | Hairline floor only |
| Primary tool | Whiteboard (stroke-reveal) |
| Scenery | None (MacroCenter / labs deprioritized) |

Module references: `services/animation/foundation_studio.py`, `PROJECT_FOUNDATION.md`.

Characters perform **in** the white studio. They do not carry environments or decorative scenery.

---

## Flagship: Professor Gen

| Field | Value |
|-------|-------|
| ID | `CHAR-PROFESSOR-001` |
| Display name | **Professor Gen** |
| Short name | **Gen** |
| Role | Generational educational host (Foundation + future series) |
| Status | `locked` |
| Visual plate | Clean black stick, white face — `StickFigureSpec` defaults |
| Attire | `none` — **lab coat forbidden for Gen v1**; optional future coat variant needs version bump |
| Outline | `(0, 0, 0, 255)` |
| Face fill | `(255, 255, 255, 255)` |
| Stroke | `7` |
| Head ratio | `0.34` |
| Voice | `nova` + `tts-1-hd` (preference lock; providers owned by Agent 5/19) |
| Motion mode | `educator_mode=True` |

Canonical files:

```
data/universe/characters/CHAR-PROFESSOR-001/
data/character_systems/PROFESSOR_PROFILE.md
```

---

## Character relationship map

| ID | Name | Role | Relationship to Gen |
|----|------|------|---------------------|
| `CHAR-STICK-001` | Stick | Predecessor lip-sync / MacroCenter performer plate | Technical ancestor; Gen inherits plate proportions, not MacroCenter scenery or random-wave habits |
| `CHAR-PROFESSOR-001` | Professor Gen | Foundation flagship host | **Current educational standard** |
| `CHAR-DASH` | Dash | Dash Science mascot | Separate brand world; do not redesign or merge identities |

**Do not unlock or break** `CHAR-DASH` or `CHAR-STICK-001`. Gen is additive.

---

## Consistency locks (all characters)

1. **character_id** must match registry and folder name.
2. **Palette** must match locked outline / face_fill (or character-specific design_spec).
3. **Proportions** (`stroke`, `head_ratio`) must match design_spec within tolerance.
4. **Forbidden gestures** apply per character mode (professor: no wave spam).
5. **Version** bumps required for any silhouette, palette, or proportion change.

Validation: `services.character_systems.validate_production_character`.

---

## Department package index

| Document | Path |
|----------|------|
| This bible | `data/character_systems/CHARACTER_BIBLE.md` |
| Professor profile | `data/character_systems/PROFESSOR_PROFILE.md` |
| Gesture / pose library | `data/character_systems/CHARACTER_LIBRARY.md` |
| Animation style (Agent 16) | `data/character_systems/ANIMATION_STYLE_GUIDE.md` |
| QC checklist | `data/character_systems/CHARACTER_QC_CHECKLIST.md` |
| Asset registry | `data/character_systems/registry.json` |
| Founding report | `data/character_systems/AGENT26_FOUNDING_REPORT.md` |
| Root pointer | `CHARACTER_BIBLE.md` (repo root) |

---

## Teaching rhythm (locked)

```
Welcome → question → board → example → one-line summary → next lesson tease
```

Gen gestures **only when teaching** — never for decoration.

---

## Evolution policy

1. Propose change in Character Systems review.
2. Bump `version` in design_spec + universe registry.
3. Update bible + library + QC if behavior changes.
4. Ship only after Agent 0 ACCEPT.
