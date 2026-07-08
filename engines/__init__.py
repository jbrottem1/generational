"""Engine plugins.

Importing this package registers every engine — live and planned — into the
registry. To add a new engine: create a module here with an `Engine`
subclass and register an instance below.
"""

from __future__ import annotations

from engines import registry
from engines.analytics import AnalyticsEngine
from engines.base import Engine, PlannedEngine
from engines.ideation import IdeationEngine
from engines.image import ImageEngine
from engines.learning import LearningEngine
from engines.publishing import PublishingEngine
from engines.research import ResearchEngine
from engines.script import ScriptEngine
from engines.seo import SeoEngine
from engines.video import VideoEngine
from engines.voice import VoiceEngine

__all__ = ["Engine", "PlannedEngine", "registry"]

for _engine_class in (
    IdeationEngine,
    ResearchEngine,
    SeoEngine,
    ScriptEngine,
    VoiceEngine,
    ImageEngine,
    VideoEngine,
    PublishingEngine,
    AnalyticsEngine,
    LearningEngine,
):
    if registry.get_engine(_engine_class.key) is None:
        registry.register(_engine_class())
