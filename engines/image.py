"""Image engine — the asset-resolution half of the render stage (Agent 6).

Resolves every visual asset an idea needs (AI images/video, stock footage,
brand assets; user/avatar/reaction slots reserved) through the swappable
fulfillers in `engines.render.assets`. Real providers persist on-disk media;
when AI image generation fails, an approved photographic fallback is used.
Missing media is reported and must stop render — never silent color beds.
"""

from __future__ import annotations

from engines.contracts import ContractEngine
from engines.render.engine import normalize_scenes, resolve_idea_assets
from engines.render.models import RENDER_ENGINE_VERSION


class ImageEngine(ContractEngine):
    key = "image"
    label = "Image"
    icon = "🖼️"
    description = "Resolve on-disk visual assets (AI images + approved photographic fallback)."
    version = RENDER_ENGINE_VERSION
    input_contract = ["ideas"]
    output_contract = ["render_assets_summary"]
    dependencies = ["visual_intelligence"]
    capabilities = ["render", "assets", "image", "video-assets"]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        ideas = context.get("ideas") or context.get("selected_ideas") or context.get("candidates") or []
        if not ideas:
            return {
                "render_assets_summary": {
                    "status": "SKIPPED",
                    "reason": "No ideas in context — nothing to resolve.",
                    "resolved": 0,
                    "missing": 0,
                }
            }
        resolved = 0
        missing = 0
        for idea in ideas:
            assets = resolve_idea_assets(idea)
            idea["render_assets"] = assets
            scenes, _ = normalize_scenes(idea)
            by_scene = {
                a.get("scene_number"): a
                for a in assets.get("assets", [])
                if isinstance(a, dict)
            }
            for scene in scenes:
                asset = by_scene.get(scene.get("scene_number"))
                if asset:
                    scene["resolved_asset"] = asset
            if scenes:
                visual_package = dict(idea.get("visual_package") or {})
                visual_package["scenes"] = scenes
                idea["visual_package"] = visual_package
            resolved += sum(
                1
                for a in assets.get("assets", [])
                if a.get("path") and not a.get("placeholder")
            )
            missing += len(assets.get("missing_assets", []))
        return {
            "ideas": ideas,
            "render_assets_summary": {
                "status": "FAILED" if missing else "SUCCESS",
                "resolved": resolved,
                "missing": missing,
            },
        }
