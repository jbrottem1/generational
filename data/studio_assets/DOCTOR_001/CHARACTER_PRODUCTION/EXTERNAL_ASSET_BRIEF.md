# DOCTOR_001 — External Asset Brief

Use this brief only if replacing the procedural `production_v1` mesh with an authored studio mesh. **Do not change bone names, scale, or runtime paths.**

## Install

- Directory: `data/studio_assets/DOCTOR_001/RUNTIME/`
- Primary file: `DOCTOR_001_SKINNED.blend` (also refresh `CHARACTER_PRODUCTION/DOCTOR_001_PRODUCTION.blend`)
- Keep sidecars: `RIG_BONE_MAP.json`, `FACIAL_CHANNEL_MAP.json`, `VISEME_MAP.json`, `ASSET_ORIGIN.json`

## Scale / orientation

- Units: meters
- Height: 1.85 m (6'1")
- Up: +Z
- Face forward: **−Y** (toward lab doorway cameras)
- Origin: world floor under feet (root at world origin)

## Topology targets

- Hero body: 40k–120k tris (subdivision-friendly quads preferred)
- Face: edge loops for lids, lips, nasolabial, brow
- Eyes: separate sclera/iris/pupil/cornea (or equivalent materials)
- Hands: full fingers, grasp-ready
- Coat: separate garment mesh, non-intersecting torso at bind pose

## Rig requirements

Bind to existing armature bone names in `RIG_BONE_MAP.json` (41 bones).  
Must include: root, pelvis, spine_01/02, chest, neck, head, jaw, eye_L/R, lid_*, clavicles, arms, hands, fingers, legs, feet, toes, coat_L/R/hem.

## Facial blendshape names

Exact names in `FACIAL_CHANNEL_MAP.json` / `FACIAL_SHAPE_KEYS` (jaw_open, smile, concern, blink_L/R, viseme_*, etc.).

## Materials / textures

Slots: shell, face, navy, metal, coat, coat_trim, insignia, sclera, iris, pupil, cornea, lid.  
Maps: base color, roughness, metallic, normal, AO, emissive mask. Consistent texel density; no stretched UVs on face/hands.

## Export

- Blender 4.x `.blend` with armature + meshes + shape keys
- Optional `.glb` to `DOCTOR_001_SKINNED.glb` for inspection only
- Apply transforms; freeze scale = 1

## Validation command

```bash
python3 scripts/build_doctor_001.py --skip-validate   # if only packaging authored mesh, update RUNTIME manually then:
python3 scripts/golden_motion_production.py
```

Confirm eyes readable in close-up, coat non-clipping walk/reach, grasp of SAMPLE_CONTAINER_001, dialogue line intact.
