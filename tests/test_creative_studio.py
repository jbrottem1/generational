"""Tests for the Creative Studio service layer (Agent 12).

Proves: the Creative Director makes deterministic creative decisions,
storyboards carry the full professional scene contract, characters stay
visually consistent across scenes, the style/environment/production-type
libraries select correctly and expand at runtime, continuity tracking
detects breaks, and quality control reports warnings without ever raising.
"""

from __future__ import annotations

from services.creative_studio import (
    ASSET_REQUIREMENT_FIELDS,
    CREATIVE_BLUEPRINT_FIELDS,
    SHOT_LIST_ENTRY_FIELDS,
    STORYBOARD_SCENE_FIELDS,
    build_asset_requirements,
    build_blueprint,
    build_creative_package,
    build_shot_list,
    build_storyboard,
    cast_characters,
    character_prompt_fragment,
    create_character,
    get_production_type,
    get_style,
    interpret_script,
    register_environment,
    register_production_type,
    register_style,
    select_environments,
    select_production_type,
    select_style,
    track_continuity,
    validate_package,
)
from services.creative_studio.models import ReadinessStatus


def make_item(**overrides):
    """One canonical ContentPackage-style dict entering the studio."""
    item = {
        "project_id": "proj1",
        "topic": "deep sea creatures",
        "niche": "science",
        "title": "The Ocean Mystery",
        "hook": "What if the ocean disappeared tomorrow?",
        "script": (
            "The ocean vanishes overnight. Cities panic as the tides stop. "
            "Scientists trace the cause to a rift. The rift is growing. "
            "Humanity must act before dawn."
        ),
        "keywords": ["ocean", "science"],
        "opportunity_score": 70,
        "quality_score": 75,
    }
    item.update(overrides)
    return item


# ----------------------------------------------------------- creative director


def test_director_blueprint_carries_every_creative_decision():
    blueprint = build_blueprint(make_item())
    for field in CREATIVE_BLUEPRINT_FIELDS:
        assert field in blueprint, field
    assert blueprint["production_type"] == "science_visualization"
    assert blueprint["visual_style"] == "scientific"
    assert blueprint["pacing"]["tempo"] in ("slow", "measured", "dynamic", "rapid")
    assert blueprint["cinematic_language"]["camera_grammar"]
    assert blueprint["recommended_techniques"]
    assert blueprint["target_duration_sec"] > 0


def test_director_is_deterministic():
    assert build_blueprint(make_item()) == build_blueprint(make_item())


def test_script_interpretation_finds_arc_and_key_moments():
    interpretation = interpret_script(make_item())
    assert interpretation["beats"] == 5
    assert interpretation["arc"] == "hook → escalation → revelation → payoff"
    positions = [moment["position"] for moment in interpretation["key_moments"]]
    assert positions == ["hook", "midpoint", "payoff"]


def test_high_scoring_opportunities_are_promoted_in_complexity():
    baseline = build_blueprint(make_item(opportunity_score=50, quality_score=50))
    flagship = build_blueprint(make_item(opportunity_score=95))
    assert baseline["production_complexity"] == "advanced"  # medium baseline
    assert flagship["production_complexity"] == "flagship"


def test_explicit_creative_requests_override_selection():
    blueprint = build_blueprint(
        make_item(production_type="whiteboard", visual_style="luxury", pacing="rapid")
    )
    assert blueprint["production_type"] == "whiteboard"
    assert blueprint["visual_style"] == "luxury"
    assert blueprint["pacing"]["tempo"] == "rapid"


# ------------------------------------------------------------ production types


def test_production_type_selection_matches_content_signals():
    assert select_production_type(make_item())["type_id"] == "science_visualization"
    assert select_production_type({"topic": "abc song for toddlers"})["type_id"] == "kids_educational"
    assert select_production_type({"topic": "the fall of the roman empire"})["type_id"] == "historical_reconstruction"
    # No signal → AI cinematic video default.
    assert select_production_type({"topic": "xyzzy"})["type_id"] == "cinematic_video"


def test_production_types_are_modular_and_expandable():
    registered = register_production_type(
        {
            "type_id": "interactive_experience",
            "label": "Interactive Visual Experience",
            "keywords": ["interactive", "choose"],
            "default_style": "cyberpunk",
        }
    )
    try:
        assert get_production_type("interactive_experience") == registered
        selected = select_production_type({"topic": "an interactive choose your path story"})
        assert selected["type_id"] == "interactive_experience"
    finally:
        from services.creative_studio.production_types import _TYPES

        _TYPES.pop("interactive_experience", None)


# -------------------------------------------------------------------- styles


def test_style_selection_prefers_request_then_type_default():
    production_type = get_production_type("science_visualization")
    assert select_style({"visual_style": "luxury"}, production_type)["style_id"] == "luxury"
    assert select_style({"topic": "unmatched"}, production_type)["style_id"] == "scientific"


def test_style_library_expands_at_runtime():
    register_style({"style_id": "vaporwave", "label": "Vaporwave", "mood": "nostalgic"})
    try:
        assert get_style("vaporwave")["label"] == "Vaporwave"
    finally:
        from services.creative_studio.styles import _STYLES

        _STYLES.pop("vaporwave", None)


# -------------------------------------------------------------- environments


def test_environment_selection_casts_matching_locations():
    environments = select_environments(make_item())
    ids = [environment["environment_id"] for environment in environments]
    assert "nature" in ids or "laboratory" in ids
    # No signal → the neutral studio, never an empty stage.
    assert select_environments({"topic": "xyzzy"})[0]["environment_id"] == "studio"


def test_environment_system_expands_at_runtime():
    register_environment(
        {"environment_id": "underwater_city", "label": "Underwater City", "keywords": ["atlantis"]}
    )
    try:
        selected = select_environments({"topic": "the secrets of atlantis"})
        assert selected[0]["environment_id"] == "underwater_city"
    finally:
        from services.creative_studio.environments import _ENVIRONMENTS

        _ENVIRONMENTS.pop("underwater_city", None)


# ---------------------------------------------------------------- characters


def test_character_consistency_comes_from_the_visual_signature():
    character = create_character(
        {
            "name": "Captain Coral",
            "role": "original",
            "description": "A weathered deep-sea explorer",
            "visual_signature": "weathered deep-sea explorer, silver beard, brass diving suit",
            "wardrobe": "brass diving suit",
            "color_anchor": "brass gold",
        }
    )
    fragment = character_prompt_fragment(character["character_id"])
    assert "silver beard, brass diving suit" in fragment
    assert "signature color brass gold" in fragment
    # The same fragment every time — that IS the consistency mechanism.
    assert fragment == character_prompt_fragment(character["character_id"])


def test_casting_matches_the_production_medium():
    narrator_only = cast_characters({}, get_production_type("science_visualization"))
    assert [c["role"] for c in narrator_only] == ["narrator"]
    presenter = cast_characters({}, get_production_type("ai_presenter"))
    assert "ai_avatar" in [c["role"] for c in presenter]
    kids = cast_characters({}, get_production_type("kids_educational"))
    assert "mascot" in [c["role"] for c in kids]


def test_characters_recur_identically_across_scenes_and_productions():
    item = make_item()
    blueprint = build_blueprint(item)
    characters = cast_characters(item, get_production_type(blueprint["production_type"]))
    storyboard = build_storyboard(item, blueprint, characters)
    cast_ids = [character["character_id"] for character in characters]
    for scene in storyboard:
        assert scene["characters"] == cast_ids

    # A second production casts the same house characters — same ids, same
    # signatures — so their look carries across productions.
    second = build_storyboard(make_item(project_id="proj2"), blueprint, characters)
    assert second[0]["characters"] == cast_ids


# ---------------------------------------------------------------- storyboard


def test_storyboard_scenes_carry_the_full_professional_contract():
    item = make_item()
    blueprint = build_blueprint(item)
    characters = cast_characters(item, get_production_type(blueprint["production_type"]))
    storyboard = build_storyboard(item, blueprint, characters)

    assert len(storyboard) == 5  # one scene per narration beat
    for scene in storyboard:
        for field in STORYBOARD_SCENE_FIELDS:
            assert field in scene, field
        assert scene["narration"]
        assert scene["camera_angle"] and scene["camera_movement"]
        assert scene["estimated_duration_sec"] > 0
        assert scene["transitions"]["in"] is not None

    assert storyboard[0]["purpose"] == "hook"
    assert storyboard[-1]["purpose"] == "payoff"
    assert storyboard[0]["overlay_graphics"] == ["hook text overlay"]
    assert storyboard[-1]["transitions"]["out"] == "fade to brand endcard"


def test_shot_list_and_asset_requirements_derive_from_the_board():
    item = make_item()
    blueprint = build_blueprint(item)
    characters = cast_characters(item, get_production_type(blueprint["production_type"]))
    storyboard = build_storyboard(item, blueprint, characters)

    shots = build_shot_list(storyboard)
    assert len(shots) == len(storyboard)
    for shot in shots:
        for field in SHOT_LIST_ENTRY_FIELDS:
            assert field in shot, field

    requirements = build_asset_requirements(storyboard, blueprint, characters)
    assert len(requirements) >= len(storyboard)
    for requirement in requirements:
        for field in ASSET_REQUIREMENT_FIELDS:
            assert field in requirement, field
        assert requirement["prompt"]
        assert requirement["style"] == blueprint["visual_style"]


def test_on_screen_characters_get_reusable_reference_assets():
    item = make_item(production_type="ai_presenter")
    blueprint = build_blueprint(item)
    characters = cast_characters(item, get_production_type("ai_presenter"))
    storyboard = build_storyboard(item, blueprint, characters)
    requirements = build_asset_requirements(storyboard, blueprint, characters)

    references = [req for req in requirements if req["reusable"]]
    assert references, "on-screen characters need reusable reference sheets"
    assert any("Nova" in req["description"] for req in references)


# ---------------------------------------------------------------- continuity


def _designed(item=None):
    item = item or make_item()
    blueprint = build_blueprint(item)
    characters = cast_characters(item, get_production_type(blueprint["production_type"]))
    storyboard = build_storyboard(item, blueprint, characters)
    return blueprint, characters, storyboard


def test_continuity_is_clean_for_a_designed_board():
    blueprint, characters, storyboard = _designed()
    report = track_continuity(storyboard, blueprint, characters)
    assert report["breaks"] == []
    assert report["continuity_score"] == 100
    assert report["brand_consistency"]["consistent"] is True


def test_continuity_detects_breaks_and_degrades_score():
    blueprint, characters, storyboard = _designed()
    storyboard[1]["characters"] = []                       # cast break
    storyboard[2]["animation_style"] = "different_medium"  # medium break
    storyboard[3]["camera_angle"] = ""                     # camera break
    report = track_continuity(storyboard, blueprint, characters)
    assert len(report["breaks"]) >= 3
    assert report["continuity_score"] < 100
    assert report["brand_consistency"]["consistent"] is False


# ----------------------------------------------------------- quality control


def test_quality_control_passes_a_complete_package():
    package = build_creative_package(make_item())
    assert package["validation"]["status"] == "SUCCESS"
    assert package["production_readiness"]["status"] == ReadinessStatus.READY
    assert package["production_readiness"]["score"] >= 80


def test_quality_control_reports_problems_gracefully():
    package = build_creative_package(make_item())
    package["storyboard"][0]["narration"] = ""            # incomplete scene
    package["storyboard"][1]["asset_requirements"] = ["asset_ghost"]  # missing asset
    package["storyboard"][2]["estimated_duration_sec"] = 500.0        # broken timing
    validation = validate_package(package)
    assert validation["status"] == "WARNING"
    assert any("asset_ghost" in warning for warning in validation["warnings"])
    assert any("out of bounds" in warning for warning in validation["warnings"])
    assert validation["blockers"] == []                   # warnings, not failures


def test_empty_storyboard_is_a_blocker_never_an_exception():
    package = build_creative_package(make_item())
    package["storyboard"] = []
    validation = validate_package(package)
    assert validation["status"] == "FAILED"
    assert validation["blockers"]
