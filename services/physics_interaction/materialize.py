"""Persist physics profiles and sample interaction packages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def materialize_physics_profile(profile: dict[str, Any]) -> dict[str, str]:
    cid = str(profile.get("character_id") or "UNKNOWN").upper()
    base = ROOT / "data" / "physics_interaction" / "profiles" / cid
    base.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    def write(name: str, data: Any) -> None:
        p = base / name
        p.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")
        paths[name] = str(p)

    write("PHYSICS_PROFILE.json", profile)
    write("HAND_PHYSICS.json", profile.get("hand_physics") or {})
    write("FOOT_PHYSICS.json", profile.get("foot_physics") or {})
    write("BODY_PHYSICS.json", profile.get("body_physics") or {})
    write("COLLISION.json", profile.get("collision") or {})
    write("CLOTHING_PHYSICS.json", profile.get("clothing_physics") or {})
    write("HAIR_PHYSICS.json", profile.get("hair_physics") or {})
    write("ENVIRONMENTAL_PHYSICS.json", profile.get("environmental_physics") or {})
    write("OBJECTS.json", {"objects": profile.get("objects") or []})
    write("INTERACTIONS.json", {"interactions": profile.get("interactions") or []})
    write("VALIDATION.json", profile.get("validation") or {})

    # Mirror under character studio asset when DOCTOR_001
    if cid == "DOCTOR_001":
        home = ROOT / "data" / "studio_assets" / "DOCTOR_001" / "PHYSICS"
        home.mkdir(parents=True, exist_ok=True)
        home_pkg = home / "PHYSICS_PROFILE.json"
        home_pkg.write_text(
            json.dumps(profile, indent=2, default=str) + "\n", encoding="utf-8"
        )
        paths["doctor_home"] = str(home_pkg)

    readme = base / "README.md"
    readme.write_text(
        f"# {cid} — Physics Profile\n\n"
        f"Nothing floats. Nothing clips. Nothing teleports.\n\n"
        f"Engine: Physics & Interaction\n",
        encoding="utf-8",
    )
    paths["README.md"] = str(readme)
    return paths


def materialize_interaction(package: dict[str, Any]) -> str:
    iid = str(package.get("interaction_id") or "interaction")
    out = ROOT / "data" / "physics_interaction" / "interactions" / f"{iid}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(package, indent=2, default=str) + "\n", encoding="utf-8")
    return str(out)
