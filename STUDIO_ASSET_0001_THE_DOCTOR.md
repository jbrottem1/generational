# Studio Asset #0001 — The Doctor

**Status:** Permanent Generational IP  
**Character ID:** `CHAR-0001` (legacy)  
**Canonical Studio Character:** [`DOCTOR_001`](STUDIO_CHARACTER_DOCTOR_001.md)  
**Version:** `1.1.0`  
**Path:** `data/studio_assets/CHAR-0001-THE-DOCTOR/` (compat) · `data/studio_assets/DOCTOR_001/` (canonical)  
**Service:** `services/studio_assets/the_doctor/` · `services/studio_assets/doctor_001/`  
**CLI:** `scripts/studio_asset_the_doctor.py` · `scripts/studio_character_doctor_001.py`  
**Human Realism:** gold-standard reference for [`HUMAN_REALISM_FRAMEWORK.md`](HUMAN_REALISM_FRAMEWORK.md)

Architecture remains frozen. This is not a new renderer and not a pipeline redesign.

> Prefer **`DOCTOR_001`** for all new productions. `CHAR-0001` remains a compatibility alias.

---

## Mission

The Doctor is the official face of scientific education in the Generational Universe — a reusable, version-controlled Studio Asset every future science production may cast. Audiences should recognize this character across hundreds of videos.

## Design lock

Humanoid cyborg · clean white medical chassis · premium titanium · warm blue illuminated accents · friendly expressive face · intelligent eyes · athletic approachable human proportions · professional posture.

Communicates: trust, intelligence, curiosity, compassion.  
Forbids: generic robot look, uncanny horror, random palette drift, regenerate-from-scratch.

## Permanent outputs

| Output | Location |
|--------|----------|
| Character profile | `CHARACTER_PROFILE.json` |
| Model guide (MD + PDF) | `CHARACTER_MODEL_GUIDE.md` / `.pdf` |
| Expressions | `CHARACTER_EXPRESSIONS/` |
| Poses | `POSE_LIBRARY/` |
| Animations | `ANIMATION_LIBRARY/` |
| Voice | `VOICE_PROFILE.json` |
| Personality / bio | `PERSONALITY_GUIDE.md` · `BIOGRAPHY.md` |
| World | `WORLD_GUIDE.md` · `ENVIRONMENT_PACKAGE/` (GMRI) |
| Lighting / color | `LIGHTING_PRESETS/` · `COLOR_GUIDE.md` |
| Props / objects | `PROP_LIBRARY/` · `REUSABLE_OBJECTS/` |
| Continuity | `CONTINUITY_RULES.md` · `CHARACTER_CONTINUITY_RULES.md` |
| Human Realism V1 | `HUMAN_REALISM/` + root `*_PROFILE.json` (inherits shared framework) |

## Home world

**The Generational Medical Research Institute** (`LOC-GMRI`) — reception through emergency response center; warm cinematic science facility filled with life.

## Pipeline position (soft)

```
Virtual Film Director
        ↓
Character & World Studio  ★ casts CHAR-0001 from permanent asset
        ↓
Animation Engine V2 / true_motion
```

Productions reference the asset. They do not invent a new presenter.

## Continuity law

1. Always reference this Studio Asset.  
2. Never regenerate The Doctor from scratch.  
3. Changes only via intentional version upgrades.  
4. Color system is locked in `COLOR_GUIDE.md`.

## CLI

```bash
./venv/bin/python scripts/studio_asset_the_doctor.py ensure
./venv/bin/python scripts/studio_asset_the_doctor.py status
./venv/bin/python scripts/studio_asset_the_doctor.py selftest
```

Use `--force` only when intentionally rebuilding procedural plate libraries for a version upgrade.
