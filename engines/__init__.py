"""Engine plugins.

Importing this package registers every engine — live and planned — into the
registry. To add a new engine: create a module here with an `Engine`
subclass and register an instance below.
"""

from __future__ import annotations

from engines import registry
from engines.ai_director import AiDirectorEngine
from engines.analytics import AnalyticsEngine
from engines.asset_manager import AssetManagerEngine
from engines.attention_graph import AttentionGraphEngine
from engines.base import Engine, PlannedEngine
from engines.citation import CitationEngine
from engines.contracts import ContractEngine, FutureEngine
from engines.future_stubs import (
    AnimationEngine,
    BrandManagementEngine,
    CharacterUniverseEngine,
    OptimizationLabEngine,
)
from engines.critic import CriticEngine
from engines.ideation import IdeationEngine
from engines.image import ImageEngine
from engines.learning import LearningEngine
from engines.narration import NarrationEngine
from engines.opportunity_ranking import OpportunityRankingEngine
from engines.psychology import PsychologyEngine
from engines.publishing import PublishingEngine, SchedulerEngine
from engines.publishing_queue import PublishingQueueEngine
from engines.quality import QualityEngine
from engines.ranking import RankingEngine
from engines.render import RenderEngine
from engines.render_package import RenderPackageEngine
from engines.research import ResearchEngine
from engines.revision import RevisionEngine
from engines.scene_planning import ScenePlanningEngine
from engines.script import ScriptEngine
from engines.script_generation import ScriptGenerationEngine
from engines.seo import SeoEngine
from engines.seo_optimization import SeoOptimizationEngine
from engines.subtitle import SubtitleEngine
from engines.threat_detection import ThreatDetectionEngine
from engines.timeline import TimelineEngine
from engines.market_intelligence import MarketIntelligenceEngine
from engines.asset_generation import AssetGenerationEngine
from engines.creative_studio import CreativeStudioEngine
from engines.post_production import PostProductionEngine
from engines.trend_discovery import TrendDiscoveryEngine
from engines.trend_forecasting import TrendForecastingEngine
from engines.video import VideoEngine
from engines.visual_intelligence import VisualIntelligenceEngine
from engines.visual_planning import VisualPlanningEngine
from engines.voice import VoiceEngine
from engines.voice_audio import VoiceAudioEngine

__all__ = ["Engine", "PlannedEngine", "ContractEngine", "FutureEngine", "registry"]

for _engine_class in (
    TrendDiscoveryEngine,
    OpportunityRankingEngine,
    TrendForecastingEngine,
    MarketIntelligenceEngine,
    AiDirectorEngine,
    AssetGenerationEngine,
    CreativeStudioEngine,
    PostProductionEngine,
    ResearchEngine,
    IdeationEngine,
    PsychologyEngine,
    ScriptGenerationEngine,
    VisualIntelligenceEngine,
    VoiceAudioEngine,
    AttentionGraphEngine,
    RankingEngine,
    ScriptEngine,
    CriticEngine,
    RevisionEngine,
    CitationEngine,
    SeoEngine,
    ThreatDetectionEngine,
    QualityEngine,
    ScenePlanningEngine,
    NarrationEngine,
    VisualPlanningEngine,
    AssetManagerEngine,
    SubtitleEngine,
    TimelineEngine,
    RenderPackageEngine,
    PublishingQueueEngine,
    VoiceEngine,
    ImageEngine,
    VideoEngine,
    RenderEngine,
    PublishingEngine,
    AnalyticsEngine,
    LearningEngine,
    SeoOptimizationEngine,
    SchedulerEngine,
    BrandManagementEngine,
    OptimizationLabEngine,
    CharacterUniverseEngine,
    AnimationEngine,
):
    if registry.get_engine(_engine_class.key) is None:
        registry.register(_engine_class())
