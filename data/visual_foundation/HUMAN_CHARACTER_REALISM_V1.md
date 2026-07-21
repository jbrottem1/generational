# Human Character Realism Standard — V1

Companion to `GENERATIONAL_VISUAL_FOUNDATION_V1.md`.  
**Operational framework:** [`HUMAN_REALISM_FRAMEWORK.md`](../../HUMAN_REALISM_FRAMEWORK.md) · `services/human_realism/`

Architecture frozen — specification + inherited schemas + soft PerformancePlans.  
Not a mandate to ship a new skeletal renderer today.

**Default style_mode:** `cinematic_realism`  
**Gold standard:** `CHAR-0001` The Doctor  

---

## Purpose

Produce believable, emotionally readable, anatomically coherent performances.

Characters appear to possess skeleton, muscle, weight, balance, breath, intention, emotion, and environmental awareness.

Reject stick figures, mannequins, floating heads, expressionless dolls, and weightless puppets (except locked Dash Science IP under its own bible).

---

## Inheritance (required)

```
BASE_HUMAN_REALISM ← character identity overrides
```

Do not duplicate anatomy / locomotion / face systems per host.  
Override only visual identity, personality, voice, clothing, role, gait flavor, and signature gestures.

Materialized packages:

- `data/human_realism/FRAMEWORK_V1.json`
- `data/human_realism/characters/<CHAR-ID>/`

---

## Canonical model (required for permanent hosts)

Each recurring character stores at minimum:

| Artifact | Intent |
|----------|--------|
| `CHARACTER_IDENTITY.json` | ID, height, build, wardrobe, palette, silhouette |
| `SKELETON_PROFILE.json` | Proportions, joint limits (when scripting motion) |
| `FACE_RIG_PROFILE.json` | Controllable facial regions / expression vocab |
| `GAIT_PROFILE.json` | Walk / run personality |
| `GESTURE_LIBRARY.json` | Motivated teaching / listening gestures |
| `EMOTION_LIBRARY.json` | Full-body emotional mappings |
| `HAIR_PROFILE.json` / `WARDROBE_PROFILE.json` | Material response intent |
| `CHARACTER_CONTINUITY_RULES.md` | Never regenerate from scratch |

Never rebuild identity per scene. Reference the permanent Studio Asset / Human Realism package.

---

## Skeleton & motion principles

- Movement originates from the skeleton; weight through hips/pelvis.  
- Walking: heel strike → roll → toe-off; opposite arm swing; head relatively stable.  
- Turning: eyes → head → shoulders → pelvis → feet (never rigid spin).  
- Hands fully articulate; gestures motivated and timed to meaning.  
- Joint limits respected; no collapsing elbows/knees or sliding feet.  

### Suggested hierarchy (future-compatible)

```
root → pelvis → spine → chest → neck → head (jaw, eyes)
                → clavicles → arms → hands → fingers
                → thighs → shins → feet → toes
```

---

## Face, eyes, breath

- Eyes: focus, track, blink irregularly, precede head turns, rarely stare at camera unless address.  
- Expressions blend; micro-expressions before speech.  
- Breath affects chest/abdomen subtly by state (rest, speak, walk, fear, calm).  

---

## Emotion = full body

Joy, sadness, fear, curiosity, confidence, compassion, anger each change gaze, face, breath, posture, gesture, timing, and interpersonal distance. Use anticipation → peak → recovery.

---

## Clothing & hair

Fabric and hair respond to gravity, motion, and shared world wind — never painted stills when motion systems run. Avoid clipping and helmet-hair.

---

## Performance plan (per shot)

```json
{
  "character_id": "CHAR-0001",
  "scene_id": "scene_004",
  "objective": "reassure the audience",
  "emotion": {
    "primary": "compassion",
    "intensity": 0.65,
    "transition_from": "concern",
    "transition_duration_seconds": 0.7
  },
  "gaze": { "target": "camera", "duration_seconds": 1.4 },
  "posture": { "stance": "open" },
  "gesture": { "type": "open_palm_reassurance", "start_time": 0.6 },
  "breathing": { "mode": "calm" },
  "foot_contact_required": true
}
```

---

## Validation (reject if)

Anatomy changes · sliding feet · unreadable emotion · lifeless eyes · floating character · purposeless motion · identity drift from canonical asset.

**Final standard:** not “the figure moved,” but “the character delivered a believable performance.”
