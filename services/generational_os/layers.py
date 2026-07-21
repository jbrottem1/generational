"""Four execution layers — clear ownership and handoffs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExecutionLayer(str, Enum):
    INTELLIGENCE = "intelligence"
    PRE_PRODUCTION = "pre_production"
    LOCAL_PRODUCTION = "local_production"
    POST_PRODUCTION = "post_production"


@dataclass(frozen=True)
class LayerSpec:
    layer: ExecutionLayer
    owner: str
    responsibilities: tuple[str, ...]
    output_artifact: str
    runs_on: str  # local (production is local-first)


LAYER_SPECS: tuple[LayerSpec, ...] = (
    LayerSpec(
        layer=ExecutionLayer.INTELLIGENCE,
        owner="Agent 14 · Research / Agent 12 · SEO",
        responsibilities=(
            "SEO research",
            "Trend discovery",
            "Scientific verification",
            "Educational research",
            "Topic generation",
            "Viewer psychology",
            "Retention optimization",
            "Hook generation",
            "Thumbnail planning",
            "Educational accuracy",
            "Audience targeting",
            "Source validation",
        ),
        output_artifact="PRODUCTION_BRIEF.json",
        runs_on="local",
    ),
    LayerSpec(
        layer=ExecutionLayer.PRE_PRODUCTION,
        owner="Agent 6 · Render / Agent 16 · Animation",
        responsibilities=(
            "Script generation",
            "Storyboarding",
            "Scene timing",
            "Camera planning",
            "Character choreography",
            "Whiteboard planning",
            "Visual asset planning",
            "Narration timing",
            "Animation planning",
            "Real image planning",
            "Sound design planning",
        ),
        output_artifact="RENDER_PACKAGE.json",
        runs_on="local",
    ),
    LayerSpec(
        layer=ExecutionLayer.LOCAL_PRODUCTION,
        owner="Local Workstation · Agent 6 executor",
        responsibilities=(
            "Download approved assets",
            "Local asset cache",
            "Character animation",
            "Lip synchronization",
            "Whiteboard animation",
            "Motion graphics",
            "FFmpeg assembly",
            "Rendering",
            "Final MP4 creation",
        ),
        output_artifact="verified MP4 + manifest update",
        runs_on="local",
    ),
    LayerSpec(
        layer=ExecutionLayer.POST_PRODUCTION,
        owner="Agent 28 · Release / Agent 27 · Standards",
        responsibilities=(
            "Final QC",
            "Caption verification",
            "Metadata generation",
            "Thumbnail generation",
            "Platform optimization",
            "Archive management",
            "Analytics logging",
            "Publishing preparation",
        ),
        output_artifact="READY_TO_PUBLISH/",
        runs_on="both",
    ),
)

LAYER_OWNERS = {spec.layer.value: spec.owner for spec in LAYER_SPECS}


def layer_for_stage(stage: str) -> ExecutionLayer:
    from services.generational_os.pipeline import STAGE_LAYER_MAP

    return STAGE_LAYER_MAP.get(stage, ExecutionLayer.INTELLIGENCE)
