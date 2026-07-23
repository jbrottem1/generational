# Production Asset Studio — Phase II

Architecture is **frozen**. This studio upgrades assets only.

It does **not** redesign or replace Scene Director, Character Performance Engine,
Character Rig Studio, Stage & World Simulation, Physics & Interaction,
Cinematic Direction Studio, Animation Runtime, BlenderRuntime, or the Golden Motion pipeline.

## Mission

Replace greybox / placeholder assets with production-quality characters, environments,
props, materials, lighting, facial performance, animation clips, and visual storytelling
layers — while remaining fully compatible with the existing skeletal runtime.

## Departments

1. Character Studio
2. Environment Studio
3. Prop Studio
4. Material Studio
5. Lighting Studio
6. Facial Performance Studio
7. Animation Library
8. Visual Storytelling

## Commands

```bash
python scripts/production_asset_studio.py --list-departments
python scripts/production_asset_studio.py --catalog-only
python scripts/production_asset_studio.py --bootstrap
python scripts/golden_motion_production.py
```

## Runtime contract (unchanged paths)

- `data/studio_assets/DOCTOR_001/RUNTIME/DOCTOR_001_SKINNED.blend`
- `data/studio_assets/DOCTOR_001/RUNTIME/GENERATIONAL_MEDICAL_LAB.blend`
- `data/studio_assets/DOCTOR_001/RUNTIME/SAMPLE_CONTAINER_001.blend`
- `data/studio_assets/DOCTOR_001/RUNTIME/RIG_BONE_MAP.json`

## Soft-wire

`golden_motion_blender.py` prefers Phase II `production_builders` when present.
The AnimationRuntime interface is unchanged.
