"""Output library — aggregates completed assets across projects."""

from __future__ import annotations

from core import storage


def collect_output_library() -> dict:
    """Collect completed outputs from projects, asset registry, and knowledge."""
    library = {
        "videos": [],
        "audio": [],
        "images": [],
        "assets": [],
        "scripts": [],
        "projects": [],
        "characters": [],
        "worlds": [],
        "brand_packs": [],
    }

    for project in storage.list_projects():
        if project.get("archived"):
            continue
        library["projects"].append({
            "name": project.get("name", ""),
            "platform": project.get("platform", ""),
            "niche": project.get("niche", ""),
            "idea_count": len(project.get("ideas", [])),
            "updated_at": project.get("updated_at", ""),
        })

        for idea in project.get("ideas", []):
            if idea.get("script"):
                library["scripts"].append({
                    "project": project["name"],
                    "title": idea.get("title", ""),
                    "hook": idea.get("hook", ""),
                })
            visual = idea.get("visual_package", {})
            for panel in visual.get("storyboard", []):
                library["images"].append({
                    "project": project["name"],
                    "type": "storyboard",
                    "label": panel.get("purpose", ""),
                })

        for pkg in project.get("production_packages", []):
            _collect_from_package(pkg, project["name"], library)

    _collect_from_asset_registry(library)
    _collect_from_knowledge(library)

    return library


def _collect_from_package(pkg: dict, project_name: str, library: dict) -> None:
    render = pkg.get("render_package", {})
    if render:
        library["videos"].append({
            "project": project_name,
            "status": render.get("status", ""),
            "duration_sec": render.get("duration_sec", 0),
        })

    voice = pkg.get("voice_assets", {}) or pkg.get("audio_package", {})
    if voice:
        library["audio"].append({
            "project": project_name,
            "type": "voice",
            "duration_sec": voice.get("duration_sec", 0),
        })

    music = pkg.get("music_assets", {})
    if music:
        library["audio"].append({
            "project": project_name,
            "type": "music",
            "mood": music.get("mood", ""),
        })

    creative = pkg.get("creative_package", {})
    for char in creative.get("characters", []):
        library["characters"].append({
            "project": project_name,
            "name": char.get("name", char.get("character_id", "")),
            "role": char.get("role", ""),
        })
    for env in creative.get("environments", []):
        library["worlds"].append({
            "project": project_name,
            "name": env.get("name", env.get("environment_id", "")),
        })

    asset_pkg = pkg.get("asset_package", {})
    for asset in asset_pkg.get("assets", []):
        library["assets"].append({
            "project": project_name,
            "asset_id": asset.get("asset_id", ""),
            "type": asset.get("asset_type", ""),
        })

    if pkg.get("brand") or pkg.get("brand_id"):
        library["brand_packs"].append({
            "project": project_name,
            "brand": pkg.get("brand", pkg.get("brand_id", "")),
        })


def _collect_from_asset_registry(library: dict) -> None:
    try:
        from services.asset_generation.registry import AssetRegistry
        registry = AssetRegistry()
        data = registry._read()  # noqa: SLF001 — read-only introspection
        for asset_id, asset in data.get("assets", {}).items():
            library["assets"].append({
                "asset_id": asset_id,
                "type": asset.get("asset_type", ""),
                "project": asset.get("project_id", ""),
            })
    except (ImportError, OSError, AttributeError):
        pass


def _collect_from_knowledge(library: dict) -> None:
    try:
        from services.knowledge import CATEGORY, get_knowledge_base
        kb = get_knowledge_base()
        for entry in kb.list_entries(CATEGORY.SCRIPTS):
            if not any(s["title"] == entry.get("content", "")[:40] for s in library["scripts"]):
                library["scripts"].append({
                    "project": entry.get("metadata", {}).get("niche", "knowledge"),
                    "title": str(entry.get("content", ""))[:80],
                    "hook": "",
                })
    except (ImportError, OSError, AttributeError):
        pass
