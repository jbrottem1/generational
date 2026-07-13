# CHARACTER LIBRARY — Idle / Gesture / Pose / Expression Catalog

**Owner:** Agent 26  
**Mapped to code:** `services.animation.fluid_motion.GESTURE_POSES`  
**Registry:** `data/character_systems/registry.json`  
**Status:** LOCKED keys must match code; PLANNED keys are reserved slots

---

## Code-backed gestures (LOCKED)

These keys exist in `GESTURE_POSES` and may be used in production today.

| Library ID | Gesture key | Arms / intent | Professor Gen | Notes |
|------------|-------------|---------------|---------------|-------|
| `GESTURE-IDLE` | `idle` | Arms down, relaxed | Default | Continuous breath/weight via `fluid_life` |
| `GESTURE-WAVE` | `wave` | Raised greeting arm | **FORBIDDEN** in professor mode | Allowed for non-educator plates only |
| `GESTURE-POINT` | `point` | Right arm extended | Teaching | Board callouts, force direction |
| `GESTURE-THINK` | `think` | Hand near chin | Questions | Curiosity beat |
| `GESTURE-PRESENT` | `present` | Both arms open | Summary / reveal | Calm open stance |
| `GESTURE-PUSH` | `push` | Both arms forward | Rare demo | Force / mass demos only |
| `GESTURE-REACT` | `react` | Arms raised | Avoid for Gen | Soft surprise max; no slapstick |
| `GESTURE-WRITE` | `write` | Right hand to board | Core Foundation | Sync to whiteboard stroke-reveal |

### Pose keypoint schema

Each gesture pose uses normalized shoulder-relative offsets:

`lx, ly, lhx, lhy, rx, ry, rhx, rhy, brow, lean`

Blending: `GestureBlender` (anticipation + ease + lean follow-through). No snaps.

---

## Planned library slots (PLANNED)

Reserved for Agent 16 implementation. Do not invent alternate keys in scripts.

| Library ID | Gesture key | Intent | Professor Gen |
|------------|-------------|--------|---------------|
| `GESTURE-GREETING` | `greeting` | Calm welcome (not wave spam) | Preferred open |
| `GESTURE-LISTENING` | `listening` | Attentive idle lean | Question intake |
| `GESTURE-CELEBRATING` | `celebrating` | Soft success (not panic) | After clarity |
| `GESTURE-NOD` | `nod` | Affirmation micro-motion | Agreement |
| `GESTURE-SHRUG` | `shrug` | Soft uncertainty | Rare; paradox setup |
| `GESTURE-BOARD-CIRCLE` | `board_circle` | Circle on board emphasis | Board beat |
| `GESTURE-BOARD-UNDERLINE` | `board_underline` | Underline emphasis | Board beat |

---

## Idle catalog

| Idle ID | Description | Code |
|---------|-------------|------|
| `IDLE-PROFESSOR` | Planted stance, slow breath, micro weight shift | `idle` + `fluid_life(..., professor=True)` |
| `IDLE-FACE-AUDIENCE` | Eyes forward, soft smile | `idle` + audience expression |
| `IDLE-BOARD-READY` | Slight lean toward board | `idle` with lean bias (planned) |

---

## Expression catalog (Professor Gen v1)

| Expression ID | Brows | Eyes | Mouth | Use |
|---------------|-------|------|-------|-----|
| `neutral` | soft arch | forward | slight smile | default |
| `curious` | raised | wider | small O | question beat |
| `thinking` | one up | up-left drift | flat / soft | setup |
| `clarity` | soft | forward bright | warm smile | after proof |
| `warm_close` | soft | to camera | smile | close |

Out of range for Gen: `panic`, `shock`, Dash-style chaos.

Implementation note: expression sheet is documented in `expression_sheet.json`; full facial blend system is Agent 16 scope (no phoneme inventing here).

---

## Professor gesture policy

| Rule | Enforcement |
|------|-------------|
| Gestures only when teaching | Choreography plans + QC |
| No decorative loops | `purposeful_gestures` QC |
| No wave spam | `FORBIDDEN_PROFESSOR_GESTURES` in character_systems |
| Prefer `write` / `point` / `think` / `present` / `idle` | Style guide |

---

## Mapping for Agent 16

```
Script beat  →  library gesture key  →  GESTURE_POSES[key]  →  GestureBlender  →  draw_stick_figure(pose=...)
```

When a PLANNED key is requested before implementation, fall back to nearest LOCKED key:

| Planned | Fallback |
|---------|----------|
| `greeting` | `idle` (or brief `present`) |
| `listening` | `idle` |
| `celebrating` | `present` |
| `nod` | `idle` |
| `shrug` | `think` |
| `board_circle` | `point` |
| `board_underline` | `point` |
