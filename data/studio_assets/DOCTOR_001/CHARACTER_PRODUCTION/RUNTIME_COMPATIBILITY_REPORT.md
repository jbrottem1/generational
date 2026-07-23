# DOCTOR_001 — Runtime Compatibility Report

| AnimationRuntime / BlenderRuntime call | Status |
|----------------------------------------|--------|
| load_character() | Compatible — RUNTIME/DOCTOR_001_SKINNED.blend |
| bind_skeleton() | Compatible — DOCTOR_001_RIG, RIG_BONE_MAP.json |
| apply_animation_clip() | Compatible — canonical bone names |
| apply_joint_keyframes() | Compatible |
| apply_root_motion() | Compatible — root bone |
| apply_inverse_kinematics() | Compatible (existing GM path) |
| apply_facial_animation() | Compatible — shape keys listed in map |
| apply_gaze() | Compatible — eye_L / eye_R |
| apply_blinking() | Compatible — blink_L / blink_R |
| apply_lip_sync() | Compatible — viseme_* keys |
| create_object_constraint() | Compatible — hand grasp props |
| apply_cloth_motion() | Approximated — coat bones, not full cloth sim |
| render_frame_range() | Compatible — existing BlenderRuntime |

Adapter not bypassed. Asset origin: `doctor_001_production_v1`.
