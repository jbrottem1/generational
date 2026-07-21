# Implementation — Iteration 001

## Files touched (facial only)

- `services/production_asset_studio/blender/scripts/doctor_production_mesh.py`
  - Eye materials/proportions/lids
  - Face topology accents (cheeks, lips, brows, mouth gap)
  - Shape-key deltas + resting expression
- `services/animation_runtime/blender/scripts/golden_motion_blender.py`
  - Facial channel intensities, blink asymmetry, eye gaze bones, head during speak
  - Walk / grasp / camera plan timing unchanged in structure
- `services/production_asset_studio/blender/scripts/build_doctor_001_asset.py`
  - Validation resting expression defaults

## Not touched

Coat geometry, limb proportions, lab, lighting setup, materials for coat/trim (except face DOC_*).
