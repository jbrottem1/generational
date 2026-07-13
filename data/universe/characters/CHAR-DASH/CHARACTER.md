# CHAR-DASH — “Dash”

**Character ID:** `CHAR-DASH`  
**Display name:** Dash  
**Series:** Dash Science  
**Version:** 1.0.0  
**Status:** LOCKED for production use  
**Silhouette test:** Must read as Dash at 1080×1920 phone size from 1 meter  

---

## Concept

Dash is a **curious stick-figure explorer** who treats every scientific fact like a place you can walk into. Not a talking head — a kinetic teacher who points, chases, climbs, and panics on cue.

Personality: bright, slightly chaotic, deeply earnest about getting the science right. Humor comes from physical reaction, not punchline spam.

---

## Design lock (do not redesign)

| Part | Spec |
|---|---|
| Outline | Clean black stroke, uniform ~6–8px at 1080 width (scale with resolution) |
| Body fill | Pure white `#FFFFFF` |
| Head | Perfect circle; oversized relative to body (~32–36% of total height) |
| Eyes | Two large oval whites with black pupils; pupils track interest; can dilate on shock |
| Eyebrows | Two short thick black strokes — primary emotion engine |
| Mouth | Simple: smile curve, open O, flat line, frown curve — no teeth detail |
| Torso | Single vertical stick |
| Arms | Two sticks; round mitt-hands with a clear **pointing finger** pose |
| Legs | Two sticks; small oval feet that plant/push for walk cycles |
| Height | Canonical 1.0 unit; head diameter 0.34; eye height at 0.62 of head |
| Forbidden | Color fills on body, clothing, hair, logos, 3D shading on limbs, extra fingers clutter |

**Recognition keys:** big eyes + expressive brows + white fill + constant motion energy.

---

## Expression set (v1)

| ID | Brows | Eyes | Mouth | Use |
|---|---|---|---|---|
| `neutral` | soft arch | forward | slight smile | default teach |
| `curious` | raised | wide, lean forward | small O | questions |
| `excited` | high | bright, pupils up | big smile | discoveries |
| `confused` | asymmetric | squint one | wavy | paradoxes |
| `shock` | max raise | huge pupils | open O | twists |
| `panic` | angled in | darting | open | danger/chaos comedy |
| `celebrate` | high | closed happy arcs | grin | payoff |
| `thinking` | one up | look up-left | flat | processing |
| `audience` | soft | direct to camera | smile | CTA / face audience |

---

## Capability checklist

Walk · run · jump · point · look confused · look excited · panic · celebrate · face audience · turn around · interact with objects · react to narration — **all required in animation library v1**.

---

## Prompt lock (image / frame gen)

Always append the locked prompt block from `prompt_lock.json`. Never invent alternate outfits or proportions.
