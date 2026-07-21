"""Facial rig + eye system — reusable expressive controls."""

from __future__ import annotations

from typing import Any

from services.character_rig_studio.models import EYE_CAPABILITIES, FACIAL_EMOTIONS, FACIAL_REGIONS


def build_facial_rig(
    character_id: str,
    *,
    existing_face_rig: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cid = str(character_id).upper()
    if existing_face_rig:
        base = dict(existing_face_rig)
        base["character_id"] = cid
        base["regions_supported"] = list(FACIAL_REGIONS)
        base["emotions_supported"] = list(FACIAL_EMOTIONS)
        base["reusable"] = True
        base["source"] = "composed_existing_FACE_RIG_PROFILE"
        return base

    from services.character_performance.face_rig import face_rig_profile

    profile = face_rig_profile(cid)
    return {
        **profile,
        "regions_supported": list(FACIAL_REGIONS),
        "emotions_supported": list(FACIAL_EMOTIONS),
        "micro_expressions": True,
        "speech_ready": True,
        "reusable": True,
        "source": "character_performance.face_rig_profile",
    }


def build_eye_system(character_id: str) -> dict[str, Any]:
    return {
        "character_id": str(character_id).upper(),
        "capabilities": list(EYE_CAPABILITIES),
        "default_blink_interval_sec": [2.2, 5.5],
        "pupil_dilation_range": [0.15, 0.95],
        "gaze_modes": [
            "conversation",
            "environment_scan",
            "reading",
            "camera_address",
            "task_focus",
        ],
        "saccade_enabled": True,
        "vergence_enabled": True,
        "forbid_dead_stare": True,
        "forbid_unsynced_eyes": True,
        "reusable": True,
    }
