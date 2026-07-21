"""Director review — rewrite shot plan before animation if the sequence fails."""

from __future__ import annotations

from typing import Any

from services.virtual_film_director.models import SHOT_LANGUAGE


def review_shot_plan(shots: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Ask:
      Would a professional film director approve this sequence?
      Does every scene have purpose?
      Does every camera move communicate something?
      Does pacing feel cinematic?
      Would visuals alone keep the audience?
    If NO → rewrite guidance before animation begins.
    """
    failures: list[str] = []
    warnings: list[str] = []
    rewrite_scenes: list[Any] = []

    if not shots:
        return {
            "approved": False,
            "decision": "REWRITE",
            "failures": ["empty_shot_plan"],
            "warnings": [],
            "rewrite_scenes": [],
            "questions": {},
        }

    languages = [str(s.get("shot_language") or "") for s in shots]
    emotions = [str(s.get("emotional_beat") or s.get("emotion") or "") for s in shots]

    purpose_ok = all(bool(s.get("scene_objective")) for s in shots)
    camera_ok = all(
        bool((s.get("animation_seed") or {}).get("narrative_purpose") or s.get("camera_begin"))
        for s in shots
    )
    ready_ok = all(bool(s.get("ready")) for s in shots)
    muted_ok = all(bool(s.get("muted_story_test") or s.get("cinematic_payoff")) for s in shots)

    # Emotional flatness
    unique_emotions = {e for e in emotions if e}
    if len(shots) >= 3 and len(unique_emotions) < 2:
        failures.append("emotional_flatness")
        rewrite_scenes.extend([s.get("scene_number") for s in shots])

    # Repeated identical shot language
    for i in range(1, len(languages)):
        if languages[i] and languages[i] == languages[i - 1]:
            warnings.append(f"repeated_shot_language_scenes_{shots[i-1].get('scene_number')}_{shots[i].get('scene_number')}")
            rewrite_scenes.append(shots[i].get("scene_number"))

    if not purpose_ok:
        failures.append("scenes_without_purpose")
    if not camera_ok:
        failures.append("unmotivated_camera_moves")
    if not ready_ok:
        failures.append("director_questions_unclear")
        for s in shots:
            if not s.get("ready"):
                rewrite_scenes.append(s.get("scene_number"))
    if not muted_ok:
        failures.append("fails_muted_story_test")

    # Variety floor
    if len(set(languages)) < min(3, len(shots)) and len(shots) >= 3:
        warnings.append("insufficient_shot_variety")

    approved = not failures
    questions = {
        "professional_director_would_approve": approved,
        "every_scene_has_purpose": purpose_ok,
        "every_camera_communicates": camera_ok,
        "pacing_feels_cinematic": "emotional_flatness" not in failures,
        "visuals_alone_engaging": muted_ok and approved,
    }

    unique_rewrite: list[Any] = []
    seen: set[Any] = set()
    for s in rewrite_scenes:
        if s is None or s in seen:
            continue
        seen.add(s)
        unique_rewrite.append(s)

    return {
        "approved": approved,
        "decision": "APPROVE" if approved else "REWRITE",
        "failures": failures,
        "warnings": warnings,
        "rewrite_scenes": unique_rewrite,
        "questions": questions,
        "metrics": {
            "shot_count": len(shots),
            "unique_shot_languages": len(set(languages)),
            "unique_emotional_beats": len(unique_emotions),
            "known_shot_language_rate": round(
                sum(1 for L in languages if L in SHOT_LANGUAGE) / max(1, len(languages)), 3
            ),
        },
    }


def rewrite_shot_plan(shots: list[dict[str, Any]], review: dict[str, Any]) -> list[dict[str, Any]]:
    """One-pass rewrite for variety / emotion issues — still direction only."""
    if review.get("approved"):
        return shots
    out = [dict(s) for s in shots]
    used: set[str] = set()
    alt = list(SHOT_LANGUAGE)
    for i, shot in enumerate(out):
        lang = str(shot.get("shot_language") or "")
        if lang in used or (i and lang == str(out[i - 1].get("shot_language") or "")):
            pick = next((a for a in alt if a not in used), alt[i % len(alt)])
            shot["shot_language"] = pick
            shot["camera_movement"] = pick
            seed = dict(shot.get("animation_seed") or {})
            from services.virtual_film_director.models import (
                SHOT_SIZE_FROM_LANGUAGE,
                SHOT_TO_AE_CAMERA,
                SHOT_TO_TRUE_MOTION,
            )

            seed["true_motion_camera"] = SHOT_TO_TRUE_MOTION.get(pick, "push_in")
            seed["ae_camera_move"] = SHOT_TO_AE_CAMERA.get(pick, "slow_cinematic_push")
            seed["shot_size"] = SHOT_SIZE_FROM_LANGUAGE.get(pick, "dynamic_medium")
            shot["animation_seed"] = seed
            shot["shot_size"] = seed["shot_size"]
            lang = pick
        used.add(lang)
        # Force emotional diversity mid-sequence
        if i > 0 and i < len(out) - 1:
            beats = ["discovery", "explanation", "wonder", "scale", "surprise"]
            shot["emotional_beat"] = beats[i % len(beats)]
        shot["ready"] = True
        out[i] = shot
    return out
