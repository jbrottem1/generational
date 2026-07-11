# Dash Science — Series Bible

**Series ID:** `SERIES-DASH-SCIENCE`  
**Mascot:** Dash (`CHAR-DASH`)  
**Status:** Foundation locked for mock productions  
**Format:** Vertical Shorts 9:16 · 30–60s  
**Owner:** Agent 18 (Creative) · Agent 15 (Character) · Agent 16 (Animation)  
**Parent program:** PROJECT GENERATIONAL VISUAL UNIVERSE  

---

## Brand promise

A curious stick-figure host who **lives inside** the science — walking through oceans, organs, and night skies — so every episode feels like the same show after one glance.

Viewers should recognize Dash within **2–3 episodes** by silhouette, eye shape, motion energy, and the way facts get “thrown” onto screen.

---

## Creative north stars (inspired, never copied)

| Reference energy | What we take | What we never copy |
|---|---|---|
| Kurzgesagt | Clarity, educational warmth | Birds, palette, narration cadence |
| XKCD | Stick simplicity, wit | Line art style, comic format |
| Alan Becker | Alive stick motion, physical comedy | Stick Fight IP, combat framing |
| MinutePhysics | Diagram clarity, hand-drawn teaching | Whiteboard look, host likeness |

**Ours:** white-body black-outline stick host + soft gradient worlds + constant kinetic teaching.

---

## Voice

- Energetic, curious, fast-paced, intelligent  
- Occasional dry humor (never cringe meme voice)  
- Never robotic, never condescending  
- Speaks *with* Dash’s body language — if Dash panics, the line lands panicked  

**Pacing:** ~2.8–3.2 words/sec · hook in first 2 seconds · beat change every 2–4 seconds  

---

## Visual rules (non-negotiable)

1. Dash is always on screen ≥70% of runtime (exceptions: 0.5s cutaways max).  
2. No static frame >3 seconds.  
3. No flat solid-color full-frame backgrounds.  
4. Dash interacts with science objects (points, holds, chases, opens doors into scenes).  
5. Every narration beat has a visual job for Dash **or** a diagram Dash is using.  
6. Character design is locked — no redesign without registry version bump.  

---

## Episode formula (scalable)

```
0.0–2.5s   HOOK (Dash in motion + surprising claim)
2.5–8s     SETUP (Dash walks into the world of the topic)
8s–end-6s  TEACH LOOP (walk/point/react + object reveals every 2–4s)
last 6s    PAYOFF + CTA (celebrate / look to camera / soft follow ask)
```

Reusable beat tags: `hook` · `walk_explain` · `point_diagram` · `object_reveal` · `react` · `transition_door` · `payoff` · `cta`

---

## Automation readiness

Machine packages live beside this bible:

| File | Purpose |
|---|---|
| `production_schema.json` | Episode JSON contract for generators |
| `../../characters/CHAR-DASH/` | Locked character + expressions + prompts |
| `../../animation/component_index.json` | Reusable motion library |
| `../../productions/mock_*/package.json` | Episode packages (script → timing → SEO) |

Future episodes = fill schema + pull animation components + render. No new style invention per video.
