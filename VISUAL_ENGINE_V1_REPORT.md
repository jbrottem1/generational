# Educational Visual Engine — Engine Lock Report

**Date:** 2026-07-12  
**Mission:** Fix production visual quality at the engine level (not one video)  
**Status:** COMPLETE — visual readability gate **100/100** on turtle demo spec

---

## Root causes (engine failures)

| Observed problem | Root cause |
|------------------|------------|
| Overlapping / stacked titles | Keywords never expired (`reveal` stayed 1.0 forever); same row reused without clear |
| Colliding labels / tray clutter | Timeline + shell sketch + photo panels all painted into the same tray simultaneously |
| Random arrows/circles | Free-floating normalized coords, not tied to any object |
| Annotations out of sync | Independent hand clocks; no fade-out; marks stayed after the beat |
| Presenter covers content | Scale 0.58 + paste-on-top; `professor_zone_rect` unused |

---

## Permanent engine upgrades

### 1. Text layout engine — `services/animation/layout_engine.py`
- Measure every text box before paint
- Collision detection + auto-wrap + font downsize
- Deduplicate identical labels
- Visibility envelope with fade in/out (never persist forever)
- One write per board row at a time (later write replaces earlier)
- Drop rather than clip when a slot cannot fit

### 2. Semantic annotation engine — `services/animation/annotation_engine.py`
- Every arrow/circle/highlight requires a **target** (`keyword:…`, `panel:…`, `shell:N`)
- Resolves target → bbox before drawing
- Skips drawing when target is not visible (no random geometry)
- Single focus annotation at a time; fade in/out
- Circles capped so they cannot enclose half the tray

### 3. Exclusive tray compositor — `compose_v2_teaching_frame`
- Priority: **panel > shell > timeline**
- Never stacks competing evidence layers
- Turtle schedule redesigned: living photo → timeline → shell → fossil

### 4. Presenter occlusion lock — `performer.py`
- V2 character scale **0.58 → 0.42**
- Hard AABB clamp: professor stays left of content zone (`x < 0.34`)
- Auto-scale-down if sprite would invade the board

### 5. Panel lifetime fix — `reality/panel.py`
- Panels now fade out after `end` (previously stayed forever)

### 6. Visual QC gate — `services/quality/visual_layout_qc.py`
Wired into `foundation_gate` for all `foundation_v2_*` exports:

- No overlapping text
- No duplicate labels
- No clipped text
- Annotations have semantic targets
- Presenter does not cover content
- **Readability ≥ 95** or export fails closed

---

## Validation

| Check | Result |
|-------|--------|
| `tests/test_visual_engine.py` | Pass |
| `tests/test_foundation_v2.py` | Pass |
| `tests/test_foundation_gate.py` | Pass |
| Turtle visual QC readability | **100.0** |
| Turtle smoke re-render | Exported `Biology_001_202_Origin_of_Turtles_v2.mp4` |
| `visual_layout_passed` | **true** |

---

## Files added / changed

**New**
- `services/animation/layout_engine.py`
- `services/animation/annotation_engine.py`
- `services/quality/visual_layout_qc.py`
- `tests/test_visual_engine.py`

**Updated**
- `services/animation/foundation_v2.py` — compositor + layout-backed board
- `services/animation/turtle_demos.py` — semantic pointers + exclusive windows
- `services/animation/performer.py` — professor clamp
- `services/animation/foundation_gate.py` — visual QC hook
- `services/reality/panel.py` — fade-out visibility
- `services/reality/planner.py` — non-overlapping turtle panels
- `services/generational_os/final_status.py` — visual hard-fail taxonomy
- `services/generational_os/dashboard.py` — local-queue key fix

---

## Policy going forward

1. **No new topic videos** until visual QC passes on the demo under production.
2. Every Foundation V2 annotation must declare a semantic `target`.
3. Evidence tray layers must be scheduled exclusively (or rely on the compositor).
4. Presenter must remain in the left zone; content zone is sacred.
5. Success = readable frames + QC ≥ 95 — not “code compiled.”

---

## Remaining (not blocking this lock)

- Overall content score stretch ≥ 78 (ending/story/platform) — separate from visual layout
- Batesian / psychology demos should adopt `compose_v2_teaching_frame` on next re-render
- True image-feature detection (anatomical landmarks) — next iteration of annotation anchoring
