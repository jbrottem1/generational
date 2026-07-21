# Generational Cinematic Direction Studio

**Status:** Permanent studio system  
**Architecture:** Frozen — not an animation engine, not a renderer  
**Service:** `services/cinematic_direction_studio/`  
**CLI:** `scripts/cinematic_direction_studio.py`  
**Storage:** `data/cinematic_direction_studio/packages/`

---

## Mission

Every scene must feel intentionally directed.

Every shot has a purpose.

Every movement supports the story.

---

## DIRECTOR_PACKAGE

Each scene contains:

| Objective | Role |
|-----------|------|
| story_objective | Why this beat exists |
| emotional_objective | Audience feeling |
| actor_objective | Performance goal |
| camera_objective | Motivated camera language |
| lighting_objective | Emotional light |
| editing_objective | Cuts / transitions / ending |
| music_objective | Score timing |

Plus: shot design · camera language · actor direction beats · pacing · lighting intent · editing plan · emotional timeline (episode)

---

## Camera language (emotion → move)

| Emotion | Camera |
|---------|--------|
| Hope | slow push-in |
| Discovery | orbit reveal |
| Conversation | over-the-shoulder |
| Reflection | slow dolly |
| Teaching | tracking walk-and-talk |

---

## Actor direction

Example beat language:

> Walk to microscope → stop → look down → pause → breathe → turn to viewer → smile → explain → return to work

Mechanical loops are rejected.

---

## Pipeline (frozen compose)

```
Virtual Film Director
→ Cinematic Direction Studio (DIRECTOR_PACKAGE)
→ Character & World Studio / Performance / Physics
→ Animation Engine (honors animation_seed)
→ Renderer records
```

Soft-wired into `direct_candidate`, CWS casting, Animation Engine, Shot Assembly.

---

## Quality gates

Reject: purposeless camera · mechanical acting · random editing · unclear emotion · repeating shots · identical framing every scene

JSON plans are not proof — inspect the final MP4.

---

## CLI

```bash
python3 scripts/cinematic_direction_studio.py direct
python3 scripts/cinematic_direction_studio.py selftest
```
