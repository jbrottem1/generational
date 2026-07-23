# DOCTOR_001 — Honest Limitations Report

## Native capabilities (working now)

- Full-body skeletal animation on canonical 41-bone armature
- Skinned mesh + separate coat mesh through BlenderRuntime
- Separate eye geometry (sclera/iris/pupil/cornea/lids) with gaze bones
- Facial shape-key set including expression + viseme channels
- Floor contact / locomotion / grasp path via existing Golden Motion
- Ceramic/navy/teal PBR materials (procedural)
- Permanent package under `data/studio_assets/DOCTOR_001/`

## Approximated capabilities

- “Cloth” = coat bones + secondary motion, not production cloth sim
- Lip sync = shape-key visemes, not scanned FACS / muscle sim
- Hands = palm + finger stubs (expressive enough for grasp, not hero finger acting)
- Materials = procedural PBR, not authored texture maps / texel-locked UVs
- LOD = single production mesh (no separate hero/background meshes yet)

## Incomplete capabilities

- Film-sculpt organic face topology (still primitive-assembled volumes)
- Production UV atlas + normal/roughness/AO texture sets
- Corrective blendshapes for shoulder/elbow candy-wrapper at extreme poses
- Asymmetric micro-expressions beyond shape-key math
- Tongue mesh for extreme close-up speech

## Unavailable without external artist / provider

- Pixar/Feature-level sculpted character mesh
- Photogrammetry / high-end concept sculpt pipeline
- Hand-painted hero textures and grooming
- Studio cloth and facial capture performance

## Quality gate honesty

This asset **is no longer a featureless greybox sphere**: eyes, nose, mouth, brow, coat, and materials are present and readable in close-ups. It is **still a stylized procedural hero**, not animated-feature final. Do not claim Pixar-level modeling.

## Golden Motion re-run (2026-07-18)

- Production dir: `data/animation_runtime/golden_motion/GOLDEN_MOTION_20260718T164914Z/`
- Final MP4: `GOLDEN_MOTION_FINAL.mp4` (14.0s) — ok
- Preview MP4: `GOLDEN_MOTION_PREVIEW.mp4` — ok
- `asset_source`: `doctor_001_production_v1`
- Facial validation: mouth/eyes/blinks keyframed (pass)
- Contact validation: feet, grasp, doorway (pass / approximated coat)
- Dialogue unchanged: “Real discovery begins when we look a little closer.”

Pipeline preserved. No Ken Burns. Permanent asset package under `CHARACTER_PRODUCTION/`.

