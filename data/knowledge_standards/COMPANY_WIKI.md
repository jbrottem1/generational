# Generational Company Wiki

**Owner:** Agent 27 — Knowledge & Standards Director  
**Status:** ACTIVE · operating manual hub  
**Rule:** Index and elevate — do not fork conflicting copies of GCIS or Character Systems content.

This wiki is the ramp path for new agents and the map of where truth lives.

---

## How we produce

1. **Doctrine** — [Generational Method](../../GENERATIONAL_METHOD.md) (hook → demo → explain → real-world → takeaway → bridge).
2. **Foundation mode** (current educator Shorts) — [PROJECT_FOUNDATION.md](../../PROJECT_FOUNDATION.md): white studio, whiteboard, Gen, one question per Short.
3. **Coordination** — [ECHOER_PROTOCOL.md](../../ECHOER_PROTOCOL.md) (ECP v1) for task handoffs between agents.
4. **Animation path** — `render_lip_sync_performance(educator_mode=True)` via Agent 16; Fluid Motion easing in `services/animation/fluid_motion.py`.
5. **Ship gate (Foundation)** — `services/animation/foundation_gate.py` fail-closed on educator exports.
6. **Post-production** — GCIS review after every series/sprint batch (`data/gcis/`).

Primary departments: Agent 0 (PMO) · 16 (Animation) · 26 (Character) · 24 (AELS) · 27 (Knowledge).

---

## Standards

| Source | Use when |
|--------|----------|
| [PRODUCTION_STANDARDS.md](PRODUCTION_STANDARDS.md) | Living LOCKED / ASPIRATIONAL production rules |
| [BEST_PRACTICES.md](BEST_PRACTICES.md) | Validated required practices |
| [GCIS standards.md](../gcis/knowledge/standards.md) | Operational locked STD-* table |
| [PROJECT_FOUNDATION.md](../../PROJECT_FOUNDATION.md) | White-studio educator lock |
| [foundation_gate](../../services/animation/foundation_gate.py) | Export gate code |

---

## Characters

| Source | Use when |
|--------|----------|
| [Agent 26](../../AGENT_26.md) | Character Systems Director charter |
| [Character Bible](../character_systems/CHARACTER_BIBLE.md) | Single source of truth for Gen |
| [STYLE_GUIDES.md](STYLE_GUIDES.md) | Index only — no restated style rules |

Flagship: **Professor Gen** (`CHAR-PROFESSOR-001`) · attire `none` · Foundation white studio.

---

## Knowledge capture

After every production, answer the Agent 27 capture loop (worked / failed / exceeded / slowed / reuse / never-repeat), then:

| Asset | Path |
|-------|------|
| Full lessons log (canonical) | [data/gcis/knowledge/lessons_learned.md](../gcis/knowledge/lessons_learned.md) |
| Lessons index (this dept) | [LESSONS_LEARNED.md](LESSONS_LEARNED.md) |
| Experiments | [EXPERIMENT_REGISTRY.md](EXPERIMENT_REGISTRY.md) · [experiments.json](experiments.json) |
| Prompts | [PROMPT_LIBRARY.md](PROMPT_LIBRARY.md) · GCIS [successful](../gcis/knowledge/prompts/successful.md) / [failed](../gcis/knowledge/prompts/failed.md) |
| Capture API | `services/knowledge_standards/capture.py` |

---

## Where to look

| Need | Go here |
|------|---------|
| This wiki (canonical) | `data/knowledge_standards/COMPANY_WIKI.md` |
| Agent 27 charter | [AGENT_27.md](../../AGENT_27.md) |
| Agent 26 charter | [AGENT_26.md](../../AGENT_26.md) |
| GCIS knowledge index | [data/gcis/knowledge/INDEX.md](../gcis/knowledge/INDEX.md) |
| Animation Studio | [GENERATIONAL_ANIMATION_STUDIO.md](../../GENERATIONAL_ANIMATION_STUDIO.md) |
| Fluid Motion | [PROJECT_FLUID_MOTION.md](../../PROJECT_FLUID_MOTION.md) |
| MacroCenter (deferred under Foundation) | [PROJECT_MACROCENTER.md](../../PROJECT_MACROCENTER.md) |
| Sprint ES001 report | [EXECUTIVE_SPRINT_001_REPORT.md](../../EXECUTIVE_SPRINT_001_REPORT.md) |
| Sprint 6h30 | [SPRINT_6H30.md](../../SPRINT_6H30.md) · [final report](../productions/_validation/sprint_6h30/SPRINT_6H30_FINAL_REPORT.md) |
| Asset manifest | [registry.json](registry.json) |

---

## Sections quick map

- **How we produce** — Method + Foundation + Echoer + gates  
- **Standards** — PRODUCTION_STANDARDS + GCIS STD table  
- **Characters** — Agent 26 / Character Bible  
- **Knowledge capture** — lessons · experiments · prompts  
- **Where to look** — links above  
