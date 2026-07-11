# Dash Animation Language

**Library ID:** `ANIM-DASH-V1`  
**Character:** CHAR-DASH  
**Rule:** Prefer composing existing components over inventing new motion per episode.

---

## Motion philosophy

Dash is **never still**. Even “idle” has breath + eye dart + weight shift.  
Every 2–4 seconds: change pose, camera, object, expression, or lighting.

**Easing:** smooth modern (ease-in-out, slight overshoot on jumps/points).  
**No:** hold-frame talking head, slideshow cuts without Dash motion bridge.

---

## Component catalog (v1)

| ID | Name | Loop | Duration | Notes |
|---|---|---|---|---|
| `walk_cycle` | Walk | yes | 0.6s/cycle | Primary teach locomotion |
| `run_cycle` | Run | yes | 0.4s/cycle | Chase / energy spikes |
| `idle_breathe` | Idle | yes | 1.2s | Micro-motion only |
| `talk_bob` | Talking | yes | 0.35s | Head/torso bob synced to VO peaks |
| `point_right` | Point | no | 0.45s | Hold up to 1.2s with micro-wiggle |
| `point_up` | Point up | no | 0.4s | Diagrams / sky |
| `celebrate_jump` | Celebration | no | 0.9s | Payoff |
| `think_scratch` | Thinking | no | 0.8s | Chin/head tilt |
| `shock_recoil` | Shock | no | 0.5s | Lean back + eye pop |
| `question_tilt` | Questioning | no | 0.55s | Head tilt + raised brow |
| `panic_flail` | Panic | loopable | 0.7s | Comedy danger |
| `turn_180` | Turn around | no | 0.55s | Scene reorient |
| `face_audience` | Face camera | no | 0.4s | CTA / direct address |
| `jump_onto` | Jump onto object/text | no | 0.7s | Land with squash |
| `hold_object` | Object hold | yes | — | Prop attach point: right mitt |
| `throw_fact` | Throw label/fact | no | 0.6s | Fact card arcs onto screen |
| `magnify_look` | Magnifying glass | no | 1.0s | Peek + zoom cue |
| `flashlight_sweep` | Flashlight | no | 1.2s | Beam reveals dark areas |
| `microscope_peer` | Microscope | no | 1.0s | Lean in + cut to micro |
| `door_open_transition` | Door into scene | no | 1.1s | Hard scene change softener |
| `climb_up` | Climb | no | 1.0s | Ladder/organ/structure |
| `float_drift` | Float | yes | 1.5s | Zero-G / underwater hover |
| `fall_tumble` | Fall | no | 0.8s | Controlled comedy fall |

Machine specs: `components/*.json` · index: `component_index.json`

---

## Camera verbs (Dash series)

`follow_walk` · `punch_in_eyes` · `orbit_hint` · `parallax_pan` · `reveal_pull_back` · `chase_handheld_energy` · `diagram_lockoff_with_drift`

Never lock camera + character both static >3s.

---

## Retention clock

| Interval | Must change at least one of |
|---|---|
| every 2–4s | movement, zoom, camera, new object, expression, lighting, transition, object anim |
| hard fail | static frame >3.0s |
