"""Production AI provider connectors — real HTTP integrations via ProviderRuntime."""

from services.provider_runtime.connectors.base import ProductionConnector
from services.provider_runtime.connectors.text import (
    AnthropicConnector,
    GoogleGeminiConnector,
    OpenAIConnector,
)
from services.provider_runtime.connectors.image import (
    FluxConnector,
    IdeogramConnector,
    OpenAIImagesConnector,
    StabilityAIConnector,
)
from services.provider_runtime.connectors.video import (
    GoogleVeoConnector,
    KlingConnector,
    LumaConnector,
    PikaConnector,
    RunwayConnector,
)
from services.provider_runtime.connectors.voice import (
    ElevenLabsConnector,
    LocalVoiceCloneConnector,
    OpenAITTSConnector,
)
from services.provider_runtime.connectors.music import FutureMusicConnector
from services.provider_runtime.connectors.platforms import (
    ComfyUIConnector,
    FalConnector,
    OllamaConnector,
    ReplicateConnector,
    XAIConnector,
)
from services.provider_runtime.connectors.publishing import (
    FacebookPublishingConnector,
    InstagramPublishingConnector,
    LinkedInPublishingConnector,
    TikTokPublishingConnector,
    XPublishingConnector,
    YouTubePublishingConnector,
)

PRODUCTION_CONNECTOR_CLASSES = (
    OpenAIConnector,
    AnthropicConnector,
    GoogleGeminiConnector,
    XAIConnector,
    OpenAIImagesConnector,
    FluxConnector,
    IdeogramConnector,
    StabilityAIConnector,
    GoogleVeoConnector,
    RunwayConnector,
    KlingConnector,
    PikaConnector,
    LumaConnector,
    ElevenLabsConnector,
    OpenAITTSConnector,
    LocalVoiceCloneConnector,
    FutureMusicConnector,
    FalConnector,
    ReplicateConnector,
    ComfyUIConnector,
    OllamaConnector,
    YouTubePublishingConnector,
    TikTokPublishingConnector,
    InstagramPublishingConnector,
    FacebookPublishingConnector,
    XPublishingConnector,
    LinkedInPublishingConnector,
)

__all__ = [
    "ProductionConnector",
    "PRODUCTION_CONNECTOR_CLASSES",
    "OpenAIConnector",
    "AnthropicConnector",
    "GoogleGeminiConnector",
    "XAIConnector",
    "OpenAIImagesConnector",
    "FluxConnector",
    "IdeogramConnector",
    "StabilityAIConnector",
    "GoogleVeoConnector",
    "RunwayConnector",
    "KlingConnector",
    "PikaConnector",
    "LumaConnector",
    "ElevenLabsConnector",
    "OpenAITTSConnector",
    "FutureMusicConnector",
    "FalConnector",
    "ReplicateConnector",
    "ComfyUIConnector",
    "OllamaConnector",
    "YouTubePublishingConnector",
    "TikTokPublishingConnector",
    "InstagramPublishingConnector",
    "FacebookPublishingConnector",
    "XPublishingConnector",
    "LinkedInPublishingConnector",
]
