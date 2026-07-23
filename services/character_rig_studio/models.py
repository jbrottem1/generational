"""Frozen vocabulary — Character Rig Studio (permanent digital actors).

Not a renderer. Not an image generator. Not a video generator.
Scenes reference actors; scenes never recreate actors.
"""

from __future__ import annotations

PACKAGE_TYPE = "CHARACTER_RIG_PACKAGE"
PACKAGE_VERSION = "1.0.0"
ENGINE_ID = "character_rig_studio"
LIBRARY_VERSION = "1.0.0"

# Full skeletal hierarchy — reusable across all Generational actors
SKELETON_HIERARCHY = (
    "root",
    "pelvis",
    "spine_01",
    "spine_02",
    "spine_03",
    "chest",
    "neck",
    "head",
    "jaw",
    "tongue",
    "eye_left",
    "eye_right",
    "eyelid_upper_left",
    "eyelid_upper_right",
    "eyelid_lower_left",
    "eyelid_lower_right",
    "clavicle_left",
    "shoulder_left",
    "upper_arm_left",
    "elbow_left",
    "forearm_left",
    "wrist_left",
    "hand_left",
    "thumb_01_left",
    "thumb_02_left",
    "thumb_03_left",
    "index_01_left",
    "index_02_left",
    "index_03_left",
    "middle_01_left",
    "middle_02_left",
    "middle_03_left",
    "ring_01_left",
    "ring_02_left",
    "ring_03_left",
    "pinky_01_left",
    "pinky_02_left",
    "pinky_03_left",
    "clavicle_right",
    "shoulder_right",
    "upper_arm_right",
    "elbow_right",
    "forearm_right",
    "wrist_right",
    "hand_right",
    "thumb_01_right",
    "thumb_02_right",
    "thumb_03_right",
    "index_01_right",
    "index_02_right",
    "index_03_right",
    "middle_01_right",
    "middle_02_right",
    "middle_03_right",
    "ring_01_right",
    "ring_02_right",
    "ring_03_right",
    "pinky_01_right",
    "pinky_02_right",
    "pinky_03_right",
    "hip_left",
    "thigh_left",
    "knee_left",
    "shin_left",
    "ankle_left",
    "foot_left",
    "toes_left",
    "hip_right",
    "thigh_right",
    "knee_right",
    "shin_right",
    "ankle_right",
    "foot_right",
    "toes_right",
)

BODY_CAPABILITIES = (
    "walking",
    "running",
    "turning",
    "sitting",
    "standing",
    "jumping",
    "pointing",
    "lifting",
    "reaching",
    "natural_balance",
    "weight_shifting",
)

PERFORMANCE_CLIPS = (
    "idle",
    "thinking",
    "teaching",
    "listening",
    "greeting",
    "walking",
    "turning",
    "explaining",
    "laughing",
    "typing",
    "writing",
    "pointing",
    "looking_around",
    "picking_up_objects",
    "opening_doors",
    "sitting",
    "standing",
    "reacting",
)

FACIAL_EMOTIONS = (
    "smiles",
    "frowns",
    "concern",
    "joy",
    "curiosity",
    "surprise",
    "determination",
    "empathy",
    "speech",
)

FACIAL_REGIONS = (
    "eye_movement",
    "eyelids",
    "eyebrows",
    "forehead",
    "cheeks",
    "nose",
    "jaw",
    "lips",
    "tongue",
    "neck_tension",
    "micro_expressions",
)

HAND_CAPABILITIES = (
    "individual_finger_movement",
    "natural_grip",
    "object_interaction",
    "gesture_libraries",
    "medical_demonstrations",
    "writing",
    "touching_holograms",
    "holding_books",
    "holding_tools",
)

EYE_CAPABILITIES = (
    "focus_targets",
    "eye_tracking",
    "attention_shifts",
    "blink_timing",
    "pupil_dilation",
    "conversation_gaze",
    "environment_scanning",
    "reading",
    "camera_awareness",
)

MECHANICS_FORBID = (
    "foot_sliding",
    "floating",
    "teleporting_poses",
    "broken_joints",
    "weightless_movement",
)

MECHANICS_ENSURE = (
    "foot_planting",
    "hip_rotation",
    "natural_momentum",
    "secondary_motion",
    "balanced_posture",
)

REJECT_REASONS = (
    "appearance_changes_between_scenes",
    "inconsistent_proportions",
    "cannot_perform_natural_walking",
    "cannot_perform_expressive_facial_acting",
    "cannot_interact_with_objects",
    "cannot_maintain_eye_contact",
    "cannot_support_reusable_animation_clips",
)

# Permanent cast slots (library IDs)
CAST_LIBRARY_IDS = (
    "DOCTOR_001",
    "FOUNDER_001",
    "TEACHER_001",
    "HISTORIAN_001",
    "ENGINEER_001",
    "NURSE_001",
    "PATIENT_CHILD_001",
)
