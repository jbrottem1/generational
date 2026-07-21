"""Environment identity / definition — recurring worlds are never regenerated from scratch."""

from __future__ import annotations

from typing import Any


def environment_definition(
    *,
    environment_id: str,
    name: str,
    world_id: str,
    function: str,
    width: float,
    depth: float,
    height: float,
    architectural_style: str,
    time_of_day: str = "morning",
    weather: str = "clear",
    continuity_version: str = "1.0.0",
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "environment_id": environment_id,
        "name": name,
        "world_id": world_id,
        "function": function,
        "dimensions_meters": {"width": width, "depth": depth, "height": height},
        "architectural_style": architectural_style,
        "time_of_day": time_of_day,
        "weather": weather,
        "continuity_version": continuity_version,
        "forbid_regenerate_from_scratch": True,
        **(extras or {}),
    }


# Canonical Generational environments (extend via identity overrides, not regen).
GMRI_LAB_A = environment_definition(
    environment_id="doctor_medical_institute_lab_a",
    name="Primary Diagnostic Laboratory",
    world_id="generational_medical_research_institute",
    function="diagnosis_and_teaching",
    width=18.0,
    depth=25.0,
    height=6.0,
    architectural_style="cinematic_futurist_medical",
    time_of_day="morning",
    weather="clear",
    extras={
        "home_of": "DOCTOR_001",
        "location_alias": "LOC-GMRI",
        "memorable_feature": "warm-blue holographic teaching column at center",
    },
)

ENVIRONMENT_CATALOG: dict[str, dict[str, Any]] = {
    GMRI_LAB_A["environment_id"]: GMRI_LAB_A,
    "LOC-GMRI": {**GMRI_LAB_A, "alias_of": "doctor_medical_institute_lab_a"},
    "LOC-SCIENCE-MUSEUM": environment_definition(
        environment_id="generational_science_museum_main",
        name="Science Museum Main Hall",
        world_id="generational_science_museum",
        function="public_education",
        width=40.0,
        depth=55.0,
        height=12.0,
        architectural_style="cinematic_civic_museum",
    ),
    "LOC-AI-LAB": environment_definition(
        environment_id="generational_ai_lab",
        name="AI Research Laboratory",
        world_id="generational_tech_campus",
        function="research_and_demo",
        width=16.0,
        depth=22.0,
        height=5.5,
        architectural_style="cinematic_tech_lab",
    ),
}


def resolve_environment(location_or_id: str | dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(location_or_id, dict):
        loc_id = str(location_or_id.get("id") or location_or_id.get("environment_id") or "")
        base = ENVIRONMENT_CATALOG.get(loc_id) or ENVIRONMENT_CATALOG.get("LOC-GMRI")
        out = dict(base or GMRI_LAB_A)
        out["studio_location"] = {
            "id": location_or_id.get("id"),
            "name": location_or_id.get("name"),
            "ambient_life": location_or_id.get("ambient_life"),
            "environmental_animation": location_or_id.get("environmental_animation"),
            "detail_dressing": location_or_id.get("detail_dressing"),
        }
        return out
    key = str(location_or_id or "LOC-GMRI")
    return dict(ENVIRONMENT_CATALOG.get(key) or GMRI_LAB_A)
