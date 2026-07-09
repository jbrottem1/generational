"""Live preview extraction from pipeline results and production packages."""

from __future__ import annotations


def extract_previews(result: "dict | None" = None) -> dict:
    """Extract previewable assets from a studio result dict."""
    if not result:
        return _empty_previews()

    ideas = result.get("ideas", [])
    packages = result.get("production_packages", []) or result.get("unified_packages", [])

    previews = _empty_previews()
    previews["scripts"] = [
        {
            "title": idea.get("title", ""),
            "hook": idea.get("hook", ""),
            "script": idea.get("script", ""),
            "cta": idea.get("cta", ""),
        }
        for idea in ideas
    ]

    for idea in ideas:
        if idea.get("thumbnail_concept"):
            previews["thumbnails"].append({
                "title": idea.get("title", ""),
                "concept": idea["thumbnail_concept"],
            })
        if idea.get("title"):
            previews["titles"].append(idea["title"])
        if idea.get("description"):
            previews["descriptions"].append(idea["description"])
        if idea.get("hashtags"):
            previews["captions"].append({
                "title": idea.get("title", ""),
                "hashtags": idea["hashtags"],
            })

        visual = idea.get("visual_package", {})
        for panel in visual.get("storyboard", []):
            previews["images"].append({
                "type": "storyboard",
                "label": panel.get("purpose", ""),
                "description": panel.get("description", ""),
            })
        for concept in visual.get("thumbnails", []):
            previews["thumbnails"].append({
                "title": idea.get("title", ""),
                "concept": concept.get("description", concept.get("label", "")),
                "score": concept.get("overall", 0),
            })

    for pkg in packages:
        _extract_package_previews(pkg, previews)

    research = result.get("research", {})
    if research.get("summary"):
        previews["scripts"].insert(0, {
            "title": "Research Summary",
            "hook": "",
            "script": research["summary"],
            "cta": "",
        })

    return previews


def _extract_package_previews(pkg: dict, previews: dict) -> None:
    if isinstance(pkg, dict) and "to_dict" in dir(pkg):
        pkg = pkg.to_dict() if hasattr(pkg, "to_dict") else pkg

    script = pkg.get("script", "")
    if script and not any(s.get("script") == script for s in previews["scripts"]):
        previews["scripts"].append({
            "title": pkg.get("topic", pkg.get("title", "Package")),
            "hook": pkg.get("hook", ""),
            "script": script,
            "cta": "",
        })

    creative = pkg.get("creative_package", {})
    for scene in creative.get("storyboard", []):
        previews["images"].append({
            "type": "creative",
            "label": scene.get("purpose", scene.get("scene_id", "")),
            "description": scene.get("visual_description", ""),
        })
        previews["animation"].append({
            "scene": scene.get("scene_id", ""),
            "motion": scene.get("motion_instructions", ""),
            "camera": scene.get("camera_movement", ""),
        })

    asset_pkg = pkg.get("asset_package", {})
    for asset in asset_pkg.get("assets", []):
        previews["images"].append({
            "type": asset.get("asset_type", "asset"),
            "label": asset.get("asset_id", ""),
            "description": asset.get("prompt", asset.get("description", "")),
        })

    voice = pkg.get("voice_assets", {}) or pkg.get("audio_package", {})
    if voice:
        previews["voice"].append({
            "profile": voice.get("voice_profile", voice.get("narrator", "")),
            "duration_sec": voice.get("duration_sec", 0),
            "status": voice.get("status", "planned"),
        })

    music = pkg.get("music_assets", {})
    if music:
        previews["music"].append({
            "mood": music.get("mood", music.get("style", "")),
            "duration_sec": music.get("duration_sec", 0),
            "status": music.get("status", "planned"),
        })

    render = pkg.get("render_package", {})
    if render:
        previews["videos"].append({
            "status": render.get("status", "planned"),
            "duration_sec": render.get("duration_sec", 0),
            "format": render.get("format", "mp4"),
        })

    post = pkg.get("post_production_package", {})
    for caption in post.get("captions", []):
        previews["captions"].append(caption)
    for subtitle in post.get("subtitles", []):
        previews["subtitles"].append(subtitle)

    seo = pkg.get("seo_package", {})
    for title in seo.get("title_variants", []):
        previews["titles"].append(title)
    for desc in seo.get("description_variants", []):
        previews["descriptions"].append(desc)


def _empty_previews() -> dict:
    return {
        "scripts": [],
        "images": [],
        "animation": [],
        "voice": [],
        "music": [],
        "videos": [],
        "thumbnails": [],
        "titles": [],
        "descriptions": [],
        "captions": [],
        "subtitles": [],
    }
