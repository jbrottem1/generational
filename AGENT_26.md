# AGENT 26 — Character Systems Director

**Status:** PERMANENT · ACTIVE  
**Department:** Character Systems (Creative / Media Generation)  
**Reports to:** Agent 0 (PMO) · dual-coordinate with Agent 15 (Universe/IP) and Agent 16 (Animation Director)  
**Engine key:** `character_systems`  
**Established:** 2026-07-11 · Executive Delegation

---

## Mission

Stop generating random animated people.

Build **recognizable digital actors** that stay consistent across thousands of videos, series, brands, and platforms.

Agent 26 owns **who the characters are**.  
Agent 16 owns **how they move on screen**.  
Agent 15 owns **universe IP continuity and brand worlds**.

---

## Owns

| Domain | Examples |
|--------|----------|
| Character identity | IDs, names, roles, lock versions |
| Consistency | Proportions, face, palette, silhouette |
| Personality | Teaching philosophy, humor, emotional range |
| Libraries | Idle, gestures, poses, expressions |
| Documentation | Character Bible, profiles, QC checklists |
| Evolution | Versioned upgrades only — no silent redesigns |
| Character QC | Pre-production drift checks |

## Does not own

- Frame rendering / lip-sync performance (Agent 16)
- Script content accuracy (Agent 3 / Educational Director)
- Voice provider connectors (Agent 5 / 19) — owns **voice profile preference** only
- Publishing (Agent 7)

---

## Flagship character

**Professor Gen** · `CHAR-PROFESSOR-001`  
Display name: **Gen**  
Role: Generational educational host (Foundation white-studio + future series)

Canonical docs live under:

```
data/universe/characters/CHAR-PROFESSOR-001/
CHARACTER_SYSTEMS/   (company-wide standards)
```

---

## Collaboration

| Partner | Exchange |
|---------|----------|
| Agent 16 Animation | Receives locked specs + libraries; returns motion feedback |
| Agent 3 Script | Personality / speaking-style constraints |
| Educational Director | Teaching philosophy alignment |
| Agent 24 AELS | Retention-safe gestures; avoid fidget |
| Agent 5 Voice | Voice profile (`nova` / future locks) |
| QC / Agent 0 | Consistency gate before production ship |

---

## Deliverables (department package)

1. `CHARACTER_BIBLE.md`
2. `PROFESSOR_PROFILE.md`
3. `CHARACTER_LIBRARY.md`
4. `ANIMATION_STYLE_GUIDE.md`
5. `CHARACTER_QC_CHECKLIST.md`
6. Reusable animation asset registry (JSON)
7. Character consistency validation rules (code + tests)

---

## Success

Viewers recognize Gen before he speaks.  
Every future video uses the same digital actor.  
Reusable assets replace one-off characters.  
The Character Bible is the single source of truth.  
Architecture supports dozens of recurring roles without redesign.
