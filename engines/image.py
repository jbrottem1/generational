"""Image engine — the asset-resolution half of the render stage (Agent 6).

Resolves every visual asset an idea needs (AI images/video, stock footage,
brand assets; user/avatar/reaction slots reserved) through the swappable
fulfillers in `engines.render.assets`. Today every asset is a mock
placeholder; real providers plug in behind `providers/` without touching
this engine. Runs first in the render stage so the Video engine assembles
against resolved assets.
"""

from __future__ import annotations

from engines.contracts import ContractEngine
from engines.render.engine import resolve_idea_assets
from engines.render.models import RENDER_ENGINE_VERSION


class ImageEngine(ContractEngine):
    key = "image"
    label = "Image"
    icon = "🖼️"
    description = "Resolve visual assets (mock placeholders until real providers land)."
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
            resolved += len(assets.get("assets", []))
            missing += len(assets.get("missing_assets", []))
        return {
            "ideas": ideas,
            "render_assets_summary": {
                "status": "WARNING" if missing else "SUCCESS",
                "resolved": resolved,
                "missing": missing,
            },
        }
