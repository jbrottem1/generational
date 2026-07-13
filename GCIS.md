# Generational Continuous Improvement System (GCIS)

**Status:** ACTIVE — permanent company operating system  
**Owner:** Agent 0 (Chief of Staff / Executive OS)  
**Established:** 2026-07-10  
**Companions:** `EXECUTIVE_OS.md` · `AGENT_REGISTRY.md` · `GENERATIONAL_METHOD.md` · `data/gcis/` · `services/knowledge.py`

---

## Law

> Every completed project must make the company better.  
> Every finished video must improve the next video.  
> Every sprint must leave reusable knowledge, not just exports.

GCIS is how Generational learns as an organization — not only as a codebase.

---

## What GCIS is

A permanent loop across all departments:

```
Produce → Review → Capture knowledge → Standardize → Reuse → Measure → Improve
```

It does **not** redesign the Orchestrator or production pipeline.  
It wraps completed work with review, shared memory, and measurable next actions.

---

## Operating loop (mandatory)

### 1. Before work
- Review `data/gcis/knowledge/` for prior lessons
- Reuse proven templates / demos / choreography / prompts
- Avoid solved mistakes listed in `lessons_learned.md`

### 2. During work
- Prefer reusable components over one-off hacks
- If a discovery benefits other agents, record it immediately

### 3. After every production (post-production review)
Fill `data/gcis/templates/post_production_review.md` → save under `data/gcis/reviews/`.

Score (1–10): teaching clarity · animation · scientific accuracy · SEO · render · pacing · audio · visual storytelling · workflow efficiency.

Capture: what worked · what failed · new standards · next concrete improvement.

### 4. After every major sprint
Publish an Executive Report using `data/gcis/templates/sprint_executive_report.md`.

### 5. Continuous optimization
Promote repeated wins into:
- reusable demos / animation assets
- teaching structures (Generational Method)
- prompts, SEO packs, camera presets, QC checks
- scripts under `scripts/` that encode the pattern

Automate only when it improves consistency, speed, or quality without reducing accuracy.

### 6. Self-improvement policy
Before changing systems: review existing implementations · avoid duplication · estimate impact.  
After changing: verify · measure · keep wins · revert regressions.

---

## Shared knowledge (central)

| Path | Purpose |
|---|---|
| `data/gcis/knowledge/lessons_learned.md` | Solved mistakes + durable wins |
| `data/gcis/knowledge/standards.md` | Locked practices |
| `data/gcis/knowledge/reusable_assets.md` | Inventory of reusable components |
| `data/gcis/knowledge/prompts/` | Successful / failed prompts |
| `data/knowledge/` | Content memory (hooks, titles, SEO) via `services/knowledge.py` |
| `data/gcis/dashboard.json` | Live company improvement metrics |
| `data/gcis/department_review.json` | Department health snapshot |
| `data/gcis/agent_performance.json` | Agent cards |

---

## Collaboration rules

Agents must:
- Share discoveries that affect other departments
- Review peer outputs when asked
- Flag duplicated work and propose reuse
- Coordinate through Agent 0 when cross-department

If one agent invents an improvement others need, **document + apply** — do not leave it tribal.

---

## Executive dashboard metrics

Maintained in `data/gcis/dashboard.json` (refresh via `scripts/gcis_refresh_dashboard.py`):

- Production readiness · videos completed · avg production / render time  
- Avg QC / purposeful-gesture pass rate · educational quality proxy  
- Automation rate · reusable asset count · open / resolved issues · tech debt band  

---

## Success definition

Quality ↑ · Efficiency ↑ · Consistency ↑ · Educational value ↑  
while the production platform stays stable and scalable.
