"""Persist WORLD_PACKAGE under data/world_simulation/ and studio home worlds."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def materialize_world_package(package: dict[str, Any]) -> dict[str, str]:
    world_id = str(package.get("world_id") or "WORLD-UNKNOWN").upper()
    lib_dir = ROOT / "data" / "world_simulation" / "library" / world_id
    lib_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    def write(directory: Path, name: str, data: Any) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        p = directory / name
        p.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")
        paths[name if directory == lib_dir else f"{directory.name}/{name}"] = str(p)

    write(lib_dir, "WORLD_PACKAGE.json", package)
    write(lib_dir, "GEOMETRY.json", package.get("geometry") or {})
    write(lib_dir, "NAVIGATION.json", package.get("navigation") or {})
    write(lib_dir, "INTERACTION_POINTS.json", package.get("interaction_points") or {})
    write(lib_dir, "LIVING_WORLD.json", package.get("living_world") or {})
    write(lib_dir, "CAMERA.json", package.get("camera") or {})
    write(lib_dir, "VALIDATION.json", package.get("validation") or {})

    readme = lib_dir / "README.md"
    readme.write_text(
        f"# {package.get('display_name') or world_id}\n\n"
        f"Persistent Generational stage. Actors navigate this world; "
        f"they do not stand in front of photographs.\n\n"
        f"- Package: `WORLD_PACKAGE.json`\n"
        f"- Engine: Stage & World Simulation\n",
        encoding="utf-8",
    )
    paths["README.md"] = str(readme)

    # Home-world mirror for DOCTOR_001 medical lab
    if world_id == "WORLD-GMRI-MEDICAL-LAB":
        home = ROOT / "data" / "studio_assets" / "DOCTOR_001" / "WORLD_PACKAGE"
        home.mkdir(parents=True, exist_ok=True)
        home_pkg = home / "WORLD_PACKAGE.json"
        home_pkg.write_text(
            json.dumps(package, indent=2, default=str) + "\n", encoding="utf-8"
        )
        paths["doctor_home_world"] = str(home_pkg)

    return paths
