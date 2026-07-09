"""Video engine — the assembly half of the render stage (Agent 6).

Builds the complete render package for every idea (timeline, scene render
plans, caption render plan, audio mix plan, validation, mock render) via
the Render Engine modules in `engines/render/`. Runs after the Image
engine so assets are already resolved; resolves them itself if not.
"""

from __future__ import annotations

from engines.contracts import ContractEngine
from engines.render.engine import render_ideas
from engines.render.models import RENDER_ENGINE_VERSION


class VideoEngine(ContractEngine):
    key = "video"
    label = "Video"
    icon = "🎬"
    description = "Assemble render-ready 9:16 video packages (mock render until real backends land)."
    version = RENDER_ENGINE_VERSION
    input_contract = ["ideas"]
    output_contract = ["render_summary"]
    dependencies = ["image", "visual_intelligence", "voice_audio"]
    capabilities = ["render", "timeline", "captions", "audio-mix", "mock-render", "vertical-video"]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        return render_ideas(context)
