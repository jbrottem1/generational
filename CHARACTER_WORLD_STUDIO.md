# Character & World Studio

**Status:** Production (universe layer)  
**Service:** `services/character_world_studio/`  
**CLI:** `scripts/character_world_studio.py`

Architecture remains frozen.

This is **not** a new renderer.  
This is **not** a pipeline redesign.  
This does **not** replace the Animation Engine.

Visual constitution: **`GENERATIONAL_VISUAL_FOUNDATION_V1.md`** (feature-film cinematic realism — not uncanny photoreal). Studio packages soft-check against `services/visual_foundation`.

Human performance: **`HUMAN_REALISM_FRAMEWORK.md`** — every host inherits shared realism; Doctor is gold standard; each scene binding carries a `performance_plan`.

Facial + world construction: **`FACIAL_PERFORMANCE_AND_ENVIRONMENT_STANDARD.md`** — emotion/attention/gaze/blink/speech plans + layered environment packages. Plans are contracts; **MP4 inspection** is the quality proof.

It evolves Generational from clip assembly into a **living animated universe** — memorable hosts, reusable locations, continuity, and plate assets Animation / true_motion can execute.

---

## Studio position

```
Virtual Film Director
        ↓
Character & World Studio  ★ cast · location · plates · continuity · gate
        ↓
Animation Engine V2 (honors studio hosts + plates)
        ↓
true_motion / assembler
```

Soft-wires:

1. `engines/cinematography.py` — after VFD  
2. Ops `animation` stage — between VFD ensure and Animation package rebuild  

---

## Host cast

| ID | Name | Role |
|----|------|------|
| `CHAR-0001` | **The Doctor** | Lead Scientific Educator — **permanent Studio Asset #0001** |
| `CHAR-ATLAS` | Professor Atlas | Lead educator |
| `CHAR-NOVA` | Nova | Curious AI assistant |
| `CHAR-ORION` | Orion | Explorer / adventurer |
| `CHAR-PIPER` | Piper | Engineer / inventor |
| `CHAR-LUNA` | Luna | Biologist / nature expert |

Each host has biography, personality, voice profile, movement style, facial range, signature clothing, silhouette, palette, recurring environments, and domain affinities.

**The Doctor** is permanent company IP (`data/studio_assets/CHAR-0001-THE-DOCTOR/`). Productions cast this asset — they do not regenerate random presenters. See `STUDIO_ASSET_0001_THE_DOCTOR.md`.

Locked IPs (Dash / Professor Gen stick) remain untouched — this cast is additive for cinematic educational productions.

---

## Locations

**Generational Medical Research Institute (GMRI)** · AI Research Laboratory · Science Museum · Ocean Observatory · Space Station · Ancient Library · Medical Research Center · Engineering Workshop · Rainforest Research Camp · Future City · Historical Village

Every location includes architecture, lighting, textures, furniture, equipment, props, ambient life, weather, environmental animation, background characters, soundscape, and detail dressing.

---

## Outputs

`data/character_world_studio/packages/<topic>_<stamp>/`

- `CHARACTER_WORLD_STUDIO_PACKAGE.json`  
- `STUDIO_NOTES.md`  
- `plates/<char>_plate.png` — expressive stylized faces (not sticks / abstract blobs)  
- Continuity state: `data/character_world_studio/CONTINUITY_STATE.json`  

---

## Soft-attach on candidate

- `studio_cast` / `primary_host` / `studio_location`  
- Per-scene: `studio_character_id`, `studio_expression`, `character_plate_path`, environment life  
- World package enriched with studio ambient / dressing (does not overwrite World Builder cameras)  
- Animation Engine character layer `source=character_world_studio` when hosts are present  

---

## Quality gate

Rejects: empty cast, stick-figure hosts, empty locations, missing plates, expressionless scenes.

Self-review questions:

- Would viewers recognize these characters again?  
- Would they remember this world?  
- Would they want another episode for the characters?  
- Does every scene feel alive?  
- Does it feel like an original series?  

---

## CLI

```bash
./venv/bin/python scripts/character_world_studio.py selftest
./venv/bin/python scripts/character_world_studio.py cast
./venv/bin/python scripts/character_world_studio.py locations
./venv/bin/python scripts/character_world_studio.py place --topic "Your Topic"
```

---

## Honest limit

Plates are stylized 2D host portraits with performance metadata — not full skeletal 3D actors. The studio makes the universe **directed and recognizable**; Animation Engine / true_motion still execute motion. Next quality leaps: multi-joint performance kits and textured environment plates bound to these location bibles.
