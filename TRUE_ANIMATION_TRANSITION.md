# True Animation Transition — Executive Decision

**Status:** ACTIVE  
**Owner:** Agent 0 (PMO) · **Animation Director:** Agent 16  
**Date:** 2026-07-10  
**Constraint:** Expand existing architecture — do not replace Orchestrator / ProviderRuntime  

Companions: `GENERATIONAL_ANIMATION_STUDIO.md` · `services/media_production/true_motion.py`

---

## 1. Honest diagnosis

| Current reality | Verdict |
|---|---|
| Script → image prompt → still → FFmpeg zoompan → MP4 | **Narrated slideshow** |
| MotionPlanner vocabulary | Mostly Ken Burns / pan / zoom on a **single still** |
| Benchmark V1 | Premium stills + camera drift — **not** true character performance |

**Decision:** Still+KenBurns is **no longer an acceptable finished scene**. Motion itself is the primary production asset.

---

## 2. Target pipeline (animation-first)

```
Research → Script → Storyboard → Shot List
  → Character Blocking → Environment Blocking → Animation Planning
  → Character Animation → Environment Animation → Camera Animation
  → VFX → Lighting → Scene Rendering → Final Film
```

Mapped onto existing seams (additive packages, no Orchestrator redesign):

| New stage | Package / module | Existing hook |
|---|---|---|
| Storyboard | `storyboard_package` | scenes stage |
| Shot list / blocking | `animation_package.shots` | Animation Director |
| Animation planning | `animation_package.plan` | optional `animation` orch stage |
| Character / env / camera anim | `true_motion` compositor | render / ffmpeg assembly |
| VFX / lighting / particles | true_motion layers + FX IDs | library registry |
| Animation QC | `animation_qc` | quality stage |

---

## 3. Technology evaluation

### A. Layered FFmpeg puppet motion (SHIP NOW)

| | |
|---|---|
| **What** | Separate BG / character / FX layers; animate position, bob, drift, camera, particles in FFmpeg |
| **Benefits** | Works offline with current stack; deterministic; cheap; exceeds slideshow immediately |
| **Limits** | Not full skeletal performance; character art still a still unless multi-pose |
| **Integration** | `services/media_production/true_motion.py` → assembler / benchmark |
| **Cost** | ~$0 compute; image gen only for layer plates |
| **Effort** | Low–medium (done in this mission) |

### B. Image-to-video providers (NEXT — recommended)

| Provider | Benefit | Limit | Effort | Cost (approx) |
|---|---|---|---|---|
| **Runway Gen-3** | Strong motion, cinematic | API key; latency; consistency | Low (ProviderRuntime already has `runway`) | ~$0.05–0.25/sec |
| **Kling** | Good character motion | Key; style drift | Low (`kling` versioned) | usage-based |
| **Luma Ray** | Smooth camera | Key; queue | Low (`luma`) | usage-based |
| **Fal video models** | Fast iteration | Key (`FAL_KEY`) | Low (`fal_ai`) | often cheaper |

**Recommendation:** Enable **image-to-video** as the hero-beat path when credentials exist; keep layered FFmpeg as default/fallback so production never blocks.

### C. Deterministic 2D runtime (QUARTER)

| Option | Benefit | Limit | Effort | Cost |
|---|---|---|---|---|
| **Rive / Lottie** | Real cycles, tiny files, brand-consistent | Art pipeline needed | Medium | Free–pro seats |
| **Remotion** | Code-driven film, perfect repeatability | React skill; render farm | Medium–high | compute |
| **Spine / DragonBones** | Game-quality characters | Specialist rigging | High | licenses |

**Recommendation:** Adopt **Rive or Lottie** for Dash walk/talk/idle cycles as permanent IP once layered motion is stable.

### D. What we will NOT do

- Replace Orchestrator with a new monolith  
- Depend solely on one closed video API  
- Ship Ken Burns-only as “animation”  

---

## 4. Quality law (effective immediately)

Reject if:

- Still-image slideshow  
- Ken Burns-only movement across all scenes  
- Static AI artwork as the sole motion  
- Color beds / blank screens  
- Minimal motion  

Pass requires **layered or video motion**: character performance OR env life OR camera path **plus** non-KenBurns primary motion class.

---

## 5. Animation Director

Agent **16** remains Animation Director — owns storyboard, motion planning, performance, camera, blocking, timing, transitions, animation QC.

---

## 6. Benchmark gate

Produce a **15–20s** true-motion scene proving character + environment + camera + lighting + particles + science storytelling. Iterate until it clearly exceeds slideshow quality.
