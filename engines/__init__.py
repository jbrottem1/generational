"""Engine plugins.

Importing this package registers every engine — live and planned — into the
registry. To add a new engine: create a module here with an `Engine`
subclass and register an instance below.
"""

from __future__ import annotations

from engines import registry
from engines.analytics import AnalyticsEngine
from engines.asset_manager import AssetManagerEngine
from engines.base import Engine, PlannedEngine
from engines.critic import CriticEngine
from engines.ideation import IdeationEngine
from engines.image import ImageEngine
from engines.learning import LearningEngine
from engines.narration import NarrationEngine
from engines.psychology import PsychologyEngine
from engines.publishing import PublishingEngine
from engines.publishing_queue import PublishingQueueEngine
from engines.quality import QualityEngine
from engines.ranking import RankingEngine
from engines.render_package import RenderPackageEngine
from engines.research import ResearchEngine
from engines.revision import RevisionEngine
from engines.scene_planning import ScenePlanningEngine
from engines.script import ScriptEngine
from engines.seo import SeoEngine
from engines.subtitle import SubtitleEngine
from engines.timeline import TimelineEngine
from engines.video import VideoEngine
from engines.visual_planning import VisualPlanningEngine
from engines.voice import VoiceEngine

__all__ = ["Engine", "PlannedEngine", "registry"]

for _engine_class in (
    ResearchEngine,
    IdeationEngine,
    PsychologyEngine,
    RankingEngine,
    ScriptEngine,
    CriticEngine,
    RevisionEngine,
    SeoEngine,
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
    PublishingEngine,
    AnalyticsEngine,
    LearningEngine,
):
    if registry.get_engine(_engine_class.key) is None:
        registry.register(_engine_class())
