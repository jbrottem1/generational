"""Provider Integration & Runtime Engine (Agent 19).

Unified provider abstraction for all AI backends. Engines and the
orchestrator request operations through ProviderRuntime without knowing
which vendor serves them.

    from services.provider_runtime import get_provider_runtime

    runtime = get_provider_runtime()
    result = runtime.generate_image({"prompt": "sunset over mountains"})
"""

from services.provider_runtime.adapter import ProviderAdapter
from services.provider_runtime.capabilities import ALL_CAPABILITIES, OPERATION_CAPABILITIES
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
    ensure_registered,
    get_provider,
    provider_catalog,
    register_provider,
    unregister_provider,
)
from services.provider_runtime.runtime import ProviderRuntime, get_provider_runtime
from services.provider_runtime.selection import ProviderSelectionEngine

__all__ = [
    "ALL_CAPABILITIES",
    "LONGFORM_JOB_TYPE",
    "OPERATION_CAPABILITIES",
    "ProductionCheckpoint",
    "ProviderAdapter",
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
    "all_providers",
    "available_providers",
    "ensure_longform_handler",
    "ensure_registered",
    "get_credential",
    "get_provider",
    "get_provider_runtime",
    "has_credential",
    "load_runtime_config",
    "provider_catalog",
    "register_provider",
    "unregister_provider",
]

# Bootstrap on import — same pattern as providers/asset_generation.
ensure_registered()
