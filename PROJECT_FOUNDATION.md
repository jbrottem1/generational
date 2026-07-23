# PROJECT FOUNDATION — Perfect the Teacher

**Status:** ACTIVE refinement phase  
**Owner:** Agent 0 (PMO) · Animation Director (Agent 16) · AELS (Agent 24)  
**Established:** 2026-07-11

---

## Mission

Simplify the animation pipeline. Perfect fundamentals before adding visual complexity.

**Priority:** Teaching quality · Animation quality · Lip sync · Educational clarity · Timing

**Deprioritized (temporary):** Environments · Laboratories · MacroCenter · Decorative effects · Scenery

---

## Studio

| Rule | Spec |
|------|------|
| Background | Pure white `(255, 255, 255)` |
| Ground | Hairline floor only |
| Primary tool | Whiteboard (stroke-reveal writing) |
| Distractions by | Nothing |

Module: `services/animation/foundation_studio.py`  
Whiteboard: `services/animation/whiteboard.py`

---

## The Professor

| Do | Don't |
|----|-------|
| Stand confidently | Float |
| Walk with purpose | Pace without reason |
| Face the audience | Constantly wave |
| Blink & breathe naturally | Fidget / overact |
| Write, point, gesture when teaching | Gesture for decoration |

Character: `CHAR-PROFESSOR-001` **Professor Gen** (short: **Gen**) via `StickFigureSpec` + `educator_mode=True`  
Attire: clean black stick only (`attire="none"`) — see `AGENT_26.md` / Character Bible  
New gesture: `write` (hand to board)

---

## Lesson structure

```
Opening (2–3s)  →  "Welcome back to Generational."
Question        →  Today's question…
Whiteboard      →  Write / circle / underline / diagram
Real-world      →  One concrete example
Summary         →  One sentence
Closing         →  "In the next lesson…"
```

No filler. One question per Short.

---

## Benchmark series (Newton's Second Law)

| File | Title | Demo ID |
|------|-------|---------|
| `Physics_001_F_Equals_MA.mp4` | What Does F = ma Actually Mean? | `foundation_f_equals_ma` |
| `Physics_002_Force_and_Mass.mp4` | Why Does a Heavy Object Need More Force? | `foundation_force_mass` |
| `Physics_003_Newtons_Second_Law.mp4` | How Newton's Second Law Explains Everyday Life | `foundation_newton_everyday` |

Produce:

```bash
./venv/bin/python scripts/project_foundation_benchmarks.py
```

Export: `~/Desktop/AI Start-up/videos/Test run 2 generational/` (never overwrite)

---

## Quality bar

The viewer should feel they are in a one-on-one tutoring session with a brilliant professor.

When fundamentals meet premium standard, richer environments may return — without sacrificing clarity.
