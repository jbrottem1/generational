"""Write CHARACTER_RIG packages under data/studio_assets/{ID}/CHARACTER_RIG/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def materialize_character_rig(package: dict[str, Any]) -> dict[str, str]:
    cid = str(package.get("character_id") or "UNKNOWN").upper()
    identity = package.get("identity") or {}
    rel = str(identity.get("studio_asset_path") or f"data/studio_assets/{cid}/")
    root = Path(rel) if Path(rel).is_absolute() else ROOT / rel
    rig_dir = root / "CHARACTER_RIG"
    rig_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, str] = {}

    def write(name: str, data: Any) -> None:
        p = rig_dir / name
        p.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")
        paths[name] = str(p)

    write("CHARACTER_RIG_PACKAGE.json", package)
    write("IDENTITY.json", package.get("identity") or {})
    write("BODY_RIG.json", package.get("body_rig") or {})
    write("FACIAL_RIG.json", package.get("facial_rig") or {})
    write("EYE_SYSTEM.json", package.get("eye_system") or {})
    write("HAND_SYSTEM.json", package.get("hand_system") or {})
    write("BODY_MECHANICS.json", package.get("body_mechanics") or {})
    write("WARDROBE.json", package.get("wardrobe") or {})
    write("MATERIALS.json", package.get("materials") or {})
    write("PERFORMANCE_SYSTEM.json", package.get("performance_system") or {})
    write("PERSONALITY.json", package.get("personality") or {})
    write("VALIDATION.json", package.get("validation") or {})

    # Lightweight README for humans
    readme = rig_dir / "README.md"
    readme.write_text(
        f"# {cid} — Character Rig\n\n"
        f"Permanent digital actor. Scenes reference this package; "
        f"scenes never recreate the actor.\n\n"
        f"- Package: `CHARACTER_RIG_PACKAGE.json`\n"
        f"- Continuity: `{identity.get('continuity_version')}`\n"
        f"- Engine: Character Rig Studio\n",
        encoding="utf-8",
    )
    paths["README.md"] = str(readme)

    # Also mirror index under data/character_rig_studio/actors/
    mirror = ROOT / "data" / "character_rig_studio" / "actors" / cid
    mirror.mkdir(parents=True, exist_ok=True)
    mirror_pkg = mirror / "CHARACTER_RIG_PACKAGE.json"
    mirror_pkg.write_text(
        json.dumps(package, indent=2, default=str) + "\n", encoding="utf-8"
    )
    paths["library_mirror"] = str(mirror_pkg)

    return paths
