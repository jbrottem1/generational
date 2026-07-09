"""Provider Integration & Runtime Engine (Agent 19 + Agent 22 connectors).

Unified provider abstraction for all AI backends. Engines and the
orchestrator request operations through ProviderRuntime without knowing
which vendor serves them.

    from services.provider_runtime import get_provider_runtime

    runtime = get_provider_runtime()
    result = runtime.generate_image({"prompt": "sunset over mountains"})
"""

from services.provider_runtime.adapter import ProviderAdapter
from services.provider_runtime.capabilities import ALL_CAPABILITIES, OPERATION_CAPABILITIES
from services.provider_runtime.cache import ProviderCache
from services.provider_runtime.config import get_credential, has_credential, load_runtime_config
from services.provider_runtime.cost import ProviderCostEstimator
from services.provider_runtime.factory import ProviderFactory
from services.provider_runtime.fallback import ProviderFallbackManager
from services.provider_runtime.health import ProviderHealthMonitor
from services.provider_runtime.longform import (
    LONGFORM_JOB_TYPE,
    ProductionCheckpoint,
    RuntimeExecutionEngine,
    ensure_longform_handler,
)
from services.provider_runtime.models import ProviderProfile, ProviderRequest, ProviderResponse
from services.provider_runtime.parallel import ParallelExecutor
from services.provider_runtime.registry import (
    all_providers,
    available_providers,
    capability_lookup,
    ensure_registered,
    get_provider,
    health_score,
    provider_catalog,
    providers_by_priority,
    register_plugin,
    register_provider,
    set_priority,
    unregister_provider,
)
from services.provider_runtime.runtime import ProviderRuntime, get_provider_runtime
from services.provider_runtime.secrets import SecretManager
from services.provider_runtime.selection import ProviderSelectionEngine
from services.provider_runtime.versioning import VersionManager

__all__ = [
    "ALL_CAPABILITIES",
    "LONGFORM_JOB_TYPE",
    "OPERATION_CAPABILITIES",
    "ProductionCheckpoint",
    "ProviderAdapter",
    "ProviderCache",
    "ProviderCostEstimator",
    "ProviderFactory",
    "ProviderFallbackManager",
    "ProviderHealthMonitor",
    "ProviderProfile",
    "ProviderRequest",
    "ProviderResponse",
    "ProviderRuntime",
    "ProviderSelectionEngine",
    "ParallelExecutor",
    "RuntimeExecutionEngine",
    "SecretManager",
    "VersionManager",
    "all_providers",
    "available_providers",
    "capability_lookup",
    "ensure_longform_handler",
    "ensure_registered",
    "get_credential",
    "get_provider",
    "get_provider_runtime",
    "has_credential",
    "health_score",
    "load_runtime_config",
    "provider_catalog",
    "providers_by_priority",
    "register_plugin",
    "register_provider",
    "set_priority",
    "unregister_provider",
]

# Bootstrap on import — same pattern as providers/asset_generation.
ensure_registered()
