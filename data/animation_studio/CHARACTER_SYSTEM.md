# Character Animation System

**Owner:** Animation Director (Agent 16) · Continuity: Agent 15  
**Goal:** Reusable characters with locked design + expandable motion kits.

---

## Required package per character

| Asset | Required |
|---|---|
| Turnaround views (front / 3/4 / side / back) | yes |
| Expression library | yes |
| Emotion library | yes |
| Idle animation | yes |
| Walk cycle | yes |
| Run cycle | yes |
| Talk cycle | yes |
| Pointing | yes |
| Thinking | yes |
| Celebrating | yes |
| Looking / gaze | yes |
| Gestures pack | yes |
| Transitions (enter/exit/turn) | yes |
| Reaction animations | yes |

---

## Flagship: CHAR-DASH

Design lock: `data/universe/characters/CHAR-DASH/`  
Motion kit: `data/universe/animation/` (`ANIM-DASH-V1`, 23 components)  
Studio index: `library/registry.json` → `characters.CHAR-DASH`

### Expression / emotion IDs

`neutral` · `curious` · `excited` · `confused` · `shock` · `panic` · `celebrate` · `thinking` · `audience`

### Core cycles (must remain available)

`walk_cycle` · `run_cycle` · `idle_breathe` · `talk_bob` · `point_right` · `point_up` · `celebrate_jump` · `think_scratch` · `shock_recoil` · `question_tilt` · `panic_flail` · `turn_180` · `face_audience`

---

## Continuity rules

1. No redesign without version bump + Creative Director approval  
2. New gestures extend the library — they do not replace proportions  
3. Series episodes may only reference registered animation IDs  
4. On-screen time for series host ≥ 70% unless storyboard marks cutaway  

---

## Future cast

Additional characters follow the same package template under `data/universe/characters/` and register here.
