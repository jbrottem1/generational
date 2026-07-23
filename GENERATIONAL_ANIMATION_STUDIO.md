# PROJECT: GENERATIONAL ANIMATION STUDIO

**Status:** ACTIVE — permanent company department  
**Priority:** Equal to production throughput and Visual Universe  
**Established:** 2026-07-10  
**Executive Sponsor:** Agent 0 — Chief of Staff / Executive OS  
**Department:** Animation Studio  
**Animation Director (accountable):** Agent 16  
**Creative alignment / brand veto:** Agent 18 — Creative Director  
**Charter owner:** Executive Office  

Companions: `EXECUTIVE_OS.md` · `GENERATIONAL_VISUAL_UNIVERSE.md` · `DASH_STICK_FIGURE_UNIVERSE.md` · `data/animation_studio/`

---

## 1. Business decision (Agent 0 protocol)

| Lens | Assessment |
|---|---|
| **Objective** | Transition from image-slideshow Shorts to fully animated educational motion pictures |
| **Impact** | Brand recognition, retention, IP compounding, series scalability |
| **Effort** | Multi-quarter program; foundation + gates + library this week |
| **Dependencies** | Existing asset production chain; Visual Story Plans; Dash / universe IP; Agent 16 animation track |
| **ROI** | Highest long-term creative ROI — every episode strengthens reusable motion IP |
| **Do now?** | **YES** — establish department, philosophy, workflow extension, QC gates now |
| **Constraint** | Do **not** redesign Orchestrator. Expand with animation-first packages, storyboard protocol, motion library, and QC gates on existing seams |

---

## 2. Company identity shift

The company is no longer an AI slideshow factory.

**We are an animation studio.**

| Before | After |
|---|---|
| Static stills with light Ken Burns | Directed motion every scene |
| Disposable Midjourney-lottery frames | Reusable characters, cycles, worlds |
| Camera optional | Cinematic camera language required |
| Environments as backdrops | Living environments (particles, weather, machines, light) |
| One-off looks | Recognizable Generational animation identity |

Every production must feel **alive**. Every scene must contain **meaningful motion**. Every character must move **naturally**. Every environment must feel **dynamic**.

---

## 3. Animation Studio Department

### Mandate

Own the motion of Generational media:

- Character animation  
- Motion direction  
- Storyboard direction  
- Camera direction  
- Environment animation  
- Facial / gesture animation  
- Visual storytelling & scene choreography  
- Animation consistency  
- Reusable motion assets  

### Leadership

| Role | Agent | Accountability |
|---|---|---|
| **Animation Director** | **16** | Department outcomes, motion language, animation QC standards, library growth |
| Creative Director (brand veto) | 18 | Style bible, silhouette/IP consistency, series recognition |
| PMO | 0 | Prioritization, dual-track balance, milestone tracking |

### Specialist roster

| Domain | Owner | Support |
|---|---|---|
| Character animation & cycles | 16 | 15 |
| Facial / gesture / emotion libraries | 16 | 15 |
| Storyboard direction | 16 | 4, 3 |
| Camera language | 16 | 4, 18 |
| Environment animation | 16 | 15, 14 |
| Scene choreography | 16 | 18, 4 |
| Motion asset library | 16 | 14 |
| Animation consistency / VU-GATE | 17 | 16, 18 |
| Render execution of motion plans | 6 | 16 |
| Script written for motion | 3 | 16 |

**Primary home:** Agents **16** (Animation Studio). Agent **15** dual-reports Creative Dept + Animation Studio for character continuity. Agent **18** retains creative veto.

---

## 4. Animation philosophy

**Not realism. Timeless, recognizable animation.**

Signature goals:

- Simple · Clean · Highly expressive · Fluid  
- Emotionally engaging · Easy to animate · Easy to recognize  
- Suitable for **thousands of episodes**

Inspired energy (never copy IP): educational clarity, stick/graphic expressiveness, kinetic teaching — original Generational language only.

Canonical flagship host today: **Dash** (`CHAR-DASH`) — see `DASH_STICK_FIGURE_UNIVERSE.md`.

---

## 5. Style requirements

Original visual language rules live in `data/animation_studio/STYLE_LANGUAGE.md`.

Require: clean silhouettes, expressive faces, readable poses, bold color design, strong lighting, smooth motion, cinematic composition, consistent proportions, reusable design rules.

Forbid: copying studios/creators; random style lottery; inconsistent redesigns; static slideshow sequences.

---

## 6. Animation-first workflow (pipeline expansion — not redesign)

Existing chain remains: Studio → Workflow Executor → Orchestrator → Engines → ProviderRuntime → asset production.

**Added packages / gates (additive):**

```
Script
  → Storyboard Package (who / doing / moving / camera / emotion / transition)
  → Visual Story Plan (existing)
  → Animation Direction Package (cycles, gestures, env FX, camera presets)
  → Asset generation + motion library reuse
  → Multi-scene cinematic assembly (existing)
  → Production QC + Animation QC Gate
  → Ready-to-post export
```

Machine contract: `data/animation_studio/workflow/animation_first_workflow.json`  
Storyboard protocol: `data/animation_studio/STORYBOARD_PROTOCOL.md`  
Implementation hooks: `services/asset_production/storyboard.py`, `animation_qc.py`

Optional Orchestrator stage `animation` / slot `animation_package` already reserved — Animation Studio fills it without changing Orchestrator topology.

---

## 7. Systems (canonical paths)

| System | Path |
|---|---|
| Style language | `data/animation_studio/STYLE_LANGUAGE.md` |
| Camera language | `data/animation_studio/CAMERA_LANGUAGE.md` |
| Environment animation | `data/animation_studio/ENVIRONMENT_ANIMATION.md` |
| Character system | `data/animation_studio/CHARACTER_SYSTEM.md` |
| Storyboard protocol | `data/animation_studio/STORYBOARD_PROTOCOL.md` |
| Animation library | `data/animation_studio/ANIMATION_LIBRARY.md` + `library/registry.json` |
| Quality gate | `data/animation_studio/QUALITY_GATE.md` + `services/asset_production/animation_qc.py` |
| Series production | `data/animation_studio/SERIES_PRODUCTION.md` |
| Department dashboard | `data/animation_studio/dashboard.json` |

Universe IP continues under `data/universe/` (Dash, environments, props). Animation Studio **directs motion**; Visual Universe **owns identity**.

---

## 8. Quality gate (non-negotiable)

Reject productions with:

- Static slideshow sequences  
- Blank / color-bed screens  
- Minimal movement  
- Repeated placeholder animation  
- Unnatural / broken motion  
- Inconsistent character designs  
- Inconsistent environments  

Every export must feel like a **professionally directed animated short**.

---

## 9. Series production

Design for recurring series with locked:

Characters · Worlds · Animation language · Props · Color · Motion · Camera · Storytelling

Audiences must recognize Generational across episodes. Flagship series: **Dash Science**.

---

## 10. Long-term objective

Build a scalable Animation Studio capable of **thousands** of animated educational Shorts while expanding an original universe.

Every production creates reusable IP that strengthens the next.

**Outcome:** an original animation ecosystem — recognizable artistic identity, smooth motion, memorable characters, high-quality educational storytelling that improves over time.

---

## 11. Milestone board

| ID | Milestone | Owner | Priority | Status |
|---|---|---|---|---|
| GAS-001 | Department charter + Animation Director | Agent 0 / 16 | P0 | **DONE** |
| GAS-002 | Style + camera + env + character system docs | 16 / 18 | P0 | **DONE** |
| GAS-003 | Storyboard protocol + animation-first workflow JSON | 16 / 4 | P0 | **DONE** |
| GAS-004 | Animation QC gate wired into asset production QC | 16 / 17 | P0 | **DONE** |
| GAS-005 | Library registry seeded from Dash ANIM-DASH-V1 | 16 / 15 | P0 | **DONE** |
| GAS-006 | Storyboard package auto-build on scene plans | 16 | P1 | **DONE** (v1) |
| GAS-007 | First series pack under Animation Studio standards | 16 / 18 | P1 | Ready |
| GAS-008 | Agent 16 worktree merge plan under Agent 1 | 1 / 16 | P1 | Planned |
| GAS-009 | Operating studio: reuse ≥ 30% motion assets | 16 | P2 | Planned |

---

## Approval

| Role | Agent | Sign-off |
|---|---|---|
| PMO | 0 | Department established |
| Animation Director | 16 | Accountable for motion outcomes |
| Creative Director | 18 | Brand / style veto retained |
| Engineering | 1 | No Orchestrator redesign; additive packages only |
