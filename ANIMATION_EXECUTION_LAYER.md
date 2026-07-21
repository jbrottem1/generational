# Generational Real-Time Animation Execution Layer

**Status:** Adapter + honest capability gate  
**Architecture:** Frozen — not a new planning framework  
**Service:** `services/animation_execution/`  
**CLI:** `scripts/golden_motion_validation.py`

---

## Purpose

Convert existing structured packages into an `EXECUTABLE_ANIMATION_SCENE` and drive a **skeletal** animation runtime:

```
DIRECTOR_PACKAGE
+ CHARACTER_PERFORMANCE_PACKAGE
+ CHARACTER_RIG_PACKAGE
+ WORLD_PACKAGE
+ INTERACTION_PACKAGE
= EXECUTABLE_ANIMATION_SCENE
→ AnimationExecutionAdapter → MP4
```

---

## Honest capability check (current environment)

| Feature | Available? |
|---------|------------|
| skeletal animation | **No** |
| joint transforms | **No** |
| IK / foot planting | **No** |
| facial blendshapes/bones | **No** |
| lip sync to mesh | **No** |
| object constraints | **No** |
| persistent 3D environments | **No** |
| animated cameras (2D crop/pan) | Yes (true_motion only) |

**true_motion** (`services/media_production/true_motion.py`) is an **ffmpeg layered still compositor**. It moves plates and cameras. It is **insufficient** for Golden Motion.

There are **no** `.glb` / `.fbx` / `.blend` skinned meshes for DOCTOR_001, and **no** Blender / Godot / Unreal / Unity runtime wired.

---

## Adapter interface

`AnimationExecutionAdapter` requires:

`load_world` · `load_actor` · `place_actor` · `apply_animation_clip` · `apply_joint_keyframes` · `apply_facial_performance` · `apply_gaze_target` · `apply_lip_sync` · `attach_object` · `execute_interaction` · `apply_physics` · `apply_camera` · `apply_lighting` · `render_frames` · `encode_mp4`

Current implementation: `InsufficientRuntimeAdapter` — records planned ops and **refuses** a misleading MP4.

---

## Golden Motion Validation

```bash
python3 scripts/golden_motion_validation.py audit
python3 scripts/golden_motion_validation.py golden
python3 scripts/golden_motion_validation.py selftest
```

Artifacts under `data/animation_execution/golden_motion/LATEST/`:

- `EXECUTABLE_ANIMATION_SCENE.json`
- `EXECUTION_MANIFEST.json`
- `FRAME_CONTACT_REPORT.json`
- `MOTION_PROOF_CONTACT_SHEET.json`
- `HONEST_CAPABILITY_REPORT.json`
- `CAPABILITY_GAP_REPORT.json`
- `GOLDEN_MOTION_REPORT.md`

Until a skeletal runtime + skinned mesh exist, **Golden Motion fails by design** (no fake success).

---

## Required integration to pass

1. Permanent DOCTOR_001 skinned mesh + face blendshapes/bones bound to Character Rig Studio hierarchy  
2. External runtime: Blender (recommended), Godot, Unreal, or Unity  
3. Implement concrete adapter (e.g. `BlenderAdapter`) behind the interface  
4. Re-run Golden Motion Validation  

Planning packages remain unchanged. The adapter is the integration seam.
