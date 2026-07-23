# ANIMATION STYLE GUIDE — Professor Gen

**Audience:** Agent 16 (Animation Director)  
**Character:** `CHAR-PROFESSOR-001` · Professor Gen  
**Studio:** PROJECT FOUNDATION white studio  
**Owner:** Agent 26 (identity constraints) · Agent 16 (execution)

---

## Principle

Better motion, not more motion. Gen should feel like a calm tutor in a one-on-one session — grounded, purposeful, alive.

---

## How Gen moves

| Quality | Spec |
|---------|------|
| Grounding | Feet planted; never float |
| Walk | Short purposeful steps; plant; teach |
| Idle life | Slow breath (~3.8s), micro weight (~5.2s), soft blink |
| Gesture | Only on teaching beats |
| Transitions | `GestureBlender` anticipation + ease — **no snaps** |
| Face audience | Question + summary beats look to camera |
| Board | Turn/lean to write or point; return |

Use `fluid_life(..., professor=True)` and `breath_scale(..., professor=True)` amps.

---

## Constraints (hard)

1. **Background** stays pure white `(255, 255, 255)` — hairline floor only.
2. **No MacroCenter scenery**, labs, or decorative environments in Foundation.
3. **Palette lock:** black outline, white face — match `StickFigureSpec` defaults.
4. **Attire lock:** `attire="none"` — lab coat forbidden for Gen v1; future coat variant needs version bump (`coat=True` / `attire="lab_coat"`).
5. **Proportions lock:** `stroke=7`, `head_ratio=0.34`.
6. **`wave` forbidden** in professor / Foundation mode (no greeting spam).
7. **No fidget loops** — AELS retention-safe; avoid decorative arm chatter.
8. **No phoneme inventing** — mouth from amplitude / existing lip-sync drivers only.
9. **Do not redesign Dash** or unlock Stick.

---

## Allowed teaching gestures (priority)

1. `idle` — between beats  
2. `write` — whiteboard stroke-reveal  
3. `point` — emphasize board / concept  
4. `think` — question framing  
5. `present` — summary / reveal  
6. `push` — only when demo requires force metaphor  

Avoid: `wave`, energetic `react` spam.

---

## Timing guidance

| Beat | Motion |
|------|--------|
| Opening 2–3s | Idle / soft present; face audience |
| Question | Think or slight lean; brows up |
| Board | Write window synced to stroke-reveal |
| Example | Point or present; one concrete beat |
| Summary | Present; face audience |
| Close | Idle; calm; next-lesson line |

Blend ~0.32s with ~0.08s anticipation (`GestureBlender` defaults).

---

## Lip sync

- Prefer foundation / educator mouth profile when `educator_mode=True`.
- Mouth smoother: snappier close bias for educator clarity.
- Do **not** invent viseme/phoneme systems in this department.

---

## QC hooks Agent 16 should hit

- `purposeful_gestures`
- `interactive_teaching`
- `grounded`
- Character Systems `validate_production_character` before ship

See `CHARACTER_QC_CHECKLIST.md`.

---

## Fallback for planned gestures

Until Agent 16 implements planned keys (`greeting`, `listening`, `celebrating`, …), use library fallbacks in `CHARACTER_LIBRARY.md`. Do not invent ad-hoc gesture names in render calls.
