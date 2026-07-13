"""Standard production pipeline — every stage explicit, traceable."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from services.generational_os.layers import ExecutionLayer


class ProductionStage(str, Enum):
    IDEA = "idea"
    RESEARCH = "research"
    SCIENTIFIC_VERIFICATION = "scientific_verification"
    SEO_ANALYSIS = "seo_analysis"
    SCRIPT = "script"
    STORYBOARD = "storyboard"
    VISUAL_PLANNING = "visual_planning"
    RENDER_PACKAGE = "render_package"
    LOCAL_PRODUCTION = "local_production"
    QUALITY_CONTROL = "quality_control"
    EXPORT = "export"
    ARCHIVE = "archive"
    PUBLISHING_PACKAGE = "publishing_package"
    ANALYTICS = "analytics"


@dataclass(frozen=True)
class StageSpec:
    stage: ProductionStage
    layer: ExecutionLayer
    owner: str
    artifact: str
    bypass_requires: str = "executive_approval"


PIPELINE_STAGES: tuple[StageSpec, ...] = (
    StageSpec(ProductionStage.IDEA, ExecutionLayer.INTELLIGENCE, "Agent 0 / Trend Intel", "idea.json"),
    StageSpec(ProductionStage.RESEARCH, ExecutionLayer.INTELLIGENCE, "Agent 14", "research notes"),
    StageSpec(ProductionStage.SCIENTIFIC_VERIFICATION, ExecutionLayer.INTELLIGENCE, "Agent 14", "sources[]"),
    StageSpec(ProductionStage.SEO_ANALYSIS, ExecutionLayer.INTELLIGENCE, "Agent 12", "seo package"),
    StageSpec(ProductionStage.SCRIPT, ExecutionLayer.PRE_PRODUCTION, "Agent 5", "script.json"),
    StageSpec(ProductionStage.STORYBOARD, ExecutionLayer.PRE_PRODUCTION, "Agent 16", "storyboard"),
    StageSpec(ProductionStage.VISUAL_PLANNING, ExecutionLayer.PRE_PRODUCTION, "Knowledge Atlas", "visual plan"),
    StageSpec(ProductionStage.RENDER_PACKAGE, ExecutionLayer.PRE_PRODUCTION, "Agent 6", "RENDER_PACKAGE.json"),
    StageSpec(ProductionStage.LOCAL_PRODUCTION, ExecutionLayer.LOCAL_PRODUCTION, "Local Mac", "episode.mp4"),
    StageSpec(ProductionStage.QUALITY_CONTROL, ExecutionLayer.POST_PRODUCTION, "Agent 28", "QC report"),
    StageSpec(ProductionStage.EXPORT, ExecutionLayer.LOCAL_PRODUCTION, "Local Mac", "Desktop MP4"),
    StageSpec(ProductionStage.ARCHIVE, ExecutionLayer.POST_PRODUCTION, "Agent 27", "manifest + archive"),
    StageSpec(ProductionStage.PUBLISHING_PACKAGE, ExecutionLayer.POST_PRODUCTION, "Agent 18", "READY_TO_PUBLISH/"),
    StageSpec(ProductionStage.ANALYTICS, ExecutionLayer.POST_PRODUCTION, "Agent 19", "analytics log"),
)

STAGE_LAYER_MAP = {spec.stage.value: spec.layer for spec in PIPELINE_STAGES}
STAGE_ORDER = [spec.stage.value for spec in PIPELINE_STAGES]


def next_stage(current: str) -> str | None:
    try:
        idx = STAGE_ORDER.index(current)
    except ValueError:
        return STAGE_ORDER[0] if STAGE_ORDER else None
    if idx + 1 >= len(STAGE_ORDER):
        return None
    return STAGE_ORDER[idx + 1]
