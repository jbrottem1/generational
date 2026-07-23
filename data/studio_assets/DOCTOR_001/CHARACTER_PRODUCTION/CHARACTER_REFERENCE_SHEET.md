# DOCTOR_001 — Character Reference Sheet

**Character:** DOCTOR_001 (The Doctor)  
**Asset version:** production_v1  
**Height:** 1.85 m (6'1")  
**Forward (face):** −Y (toward laboratory doorway / hero cameras)  
**Up:** +Z  

## Identity

Advanced humanoid medical android. Intelligent, compassionate, calm, reassuring. White ceramic-composite shell, navy technical underlayer, subtle cyan accents, separate medical coat with Generational insignia.

## Package paths

| Asset | Path |
|-------|------|
| Production blend | `CHARACTER_PRODUCTION/DOCTOR_001_PRODUCTION.blend` |
| Runtime blend | `RUNTIME/DOCTOR_001_SKINNED.blend` |
| Rig map | `RUNTIME/RIG_BONE_MAP.json` |
| Facial channels | `CHARACTER_PRODUCTION/FACIAL_CHANNEL_MAP.json` |
| Visemes | `CHARACTER_PRODUCTION/VISEME_MAP.json` |
| Validation sheet | `CHARACTER_PRODUCTION/VALIDATION_RENDERS/` |

## Canonical skeleton

41 bones including root, spine chain, limbs, fingers, jaw, eyes, lids, coat_L/R/hem. Compatible with existing Golden Motion animation packages.

## Validation views

See `VALIDATION_SHEET_INDEX.json` and PNGs 01–20 (full-body, profiles, facial expressions, gaze, grasp, walk, coat, lab hero).

## Rebuild

```bash
python3 scripts/build_doctor_001.py
```
