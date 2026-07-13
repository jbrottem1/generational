# Animation Quality Gate

**Owner:** Animation Director (Agent 16) · Enforcement: Agent 17  
**Code:** `services/asset_production/animation_qc.py`  
**Wiring:** Asset production `quality` stage (additive checks)  
**Law:** `TRUE_ANIMATION_TRANSITION.md` — Ken Burns-only is not animation  

---

## Hard rejects

| Check ID | Fail when |
|---|---|
| `no_color_bed` | Color-bed / blank frames |
| `has_visuals` | visual_count < 1 |
| `no_placeholder_visuals` | Placeholder images/scenes |
| `motion_density` | Any scene duration >3s without motion/camera/env intent |
| `storyboard_present` | Missing storyboard_package on animation-first runs |
| `camera_intent` | No camera verb on majority of beats |
| `character_consistency` | Unregistered character redesign flags |
| `env_life` | Zero environment FX across all beats (warn→error for series) |
| `not_slideshow` | All scene effects are ken_burns / static zoom-only |
| `true_motion_or_video` | No layered true-motion and no real video clips (when gate enforced) |

---

## Soft warns

- Host on-screen ratio < 0.7  
- Repeated identical animation component >3 consecutive beats  
- Flat solid background language in prompts  

---

## Pass definition

All hard checks `ok=true` and production QC already passed. Export only after both gates.

**True Animation Transition:** A production that is Ken Burns-only fails `not_slideshow` unless `true_motion.motion_class` is `true_layered_animation` or scene visuals include video clips.
