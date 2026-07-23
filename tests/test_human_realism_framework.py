"""Human Realism Framework — inheritance + PerformancePlan bindings."""

from __future__ import annotations

from pathlib import Path

from services.character_world_studio import studio_place_candidate
from services.human_realism import (
    GOLD_STANDARD_CHARACTER_ID,
    attach_performance_plans,
    list_character_ids,
    materialize_framework,
    resolve_character,
    validate_performance_plan,
)


ROOT = Path(__file__).resolve().parents[1]


def test_framework_materializes_all_hosts():
    index = materialize_framework(include_characters=True)
    assert index["gold_standard"] == "DOCTOR_001"
    for cid in list_character_ids():
        assert (ROOT / "data" / "human_realism" / "characters" / cid / "CHARACTER_IDENTITY.json").is_file()
        assert (ROOT / "data" / "human_realism" / "characters" / cid / "SKELETON_PROFILE.json").is_file()


def test_inheritance_shares_skeleton_keeps_identity():
    doctor = resolve_character(GOLD_STANDARD_CHARACTER_ID)
    atlas = resolve_character("CHAR-ATLAS")
    assert doctor["is_gold_standard"] is True
    assert atlas["reference_implementation"] == GOLD_STANDARD_CHARACTER_ID
    assert doctor["skeleton"]["hierarchy"] == atlas["skeleton"]["hierarchy"]
    assert doctor["visual_identity"]["silhouette"] != atlas["visual_identity"]["silhouette"]


def test_doctor_gold_standard_written_into_studio_asset():
    materialize_framework(include_characters=True)
    asset = ROOT / "data" / "studio_assets" / "DOCTOR_001"
    assert (asset / "CHARACTER_IDENTITY.json").is_file()
    assert (asset / "HUMAN_REALISM" / "RESOLVED_PACKAGE.json").is_file()
    assert (asset / "CHARACTER_CONTINUITY_RULES.md").is_file()


def test_cws_attaches_performance_plans():
    out = studio_place_candidate(
        {
            "topic": "How Vaccines Train Your Immune System",
            "visual_package": {
                "scenes": [
                    {
                        "scene_number": 1,
                        "narration": "Let's carefully learn how vaccines keep people safe.",
                        "length_sec": 3.0,
                    },
                    {
                        "scene_number": 2,
                        "narration": "Your immune memory becomes the quiet hero.",
                        "length_sec": 3.0,
                    },
                ]
            },
        },
        write=False,
    )
    pkg = out["CHARACTER_WORLD_STUDIO_PACKAGE"]
    scenes = pkg["scene_bindings"]
    assert scenes
    for s in scenes:
        assert s.get("performance_plan")
        assert s["performance_plan"]["character_id"]
        assert s["performance_plan"]["emotion"]["primary"]
        assert s["performance_plan"]["gaze"]["target"]
        assert s["performance_plan"]["foot_contact_required"] is True
    # Propagated onto visual package scenes
    for s in out["visual_package"]["scenes"]:
        assert s.get("performance_plan")
    assert pkg.get("human_realism", {}).get("performance_plans_attached") is True


def test_validate_performance_plan():
    plans = attach_performance_plans(
        [{"scene_number": 1, "studio_character_id": "CHAR-LUNA", "narration": "Gently observe the leaf."}]
    )
    review = validate_performance_plan(plans[0]["performance_plan"])
    assert review["ok"] is True
