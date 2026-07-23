"""Production-ready vendor adapters.

Real connectors live in `services.provider_runtime.connectors`. Only the
local-LLM stub and always-on demo remain as non-production adapters.
"""

from __future__ import annotations

from services.provider_runtime import capabilities as cap
from services.provider_runtime.adapters.stub import DemoAdapter, StubAdapter
from services.provider_runtime.connectors import PRODUCTION_CONNECTOR_CLASSES
from services.provider_runtime.factory import ProviderFactory
from services.provider_runtime.models import ProviderProfile


class LocalLLMAdapter(StubAdapter):
    name = "local_llm"
    label = "Local LLM"
    api_key_env = "LOCAL_LLM_ENDPOINT"
    offline = True
    local = True
    capabilities = (cap.LLM, cap.REASONING, cap.SCRIPT)
    profile = ProviderProfile(quality=65, cost_per_unit=0.0, speed=55, consistency=70, latency_ms=10000)


class RuntimeDemoAdapter(DemoAdapter):
    capabilities = tuple(cap.ALL_CAPABILITIES)


STUB_ADAPTER_CLASSES = (
    LocalLLMAdapter,
    RuntimeDemoAdapter,
)

VENDOR_ADAPTER_CLASSES = PRODUCTION_CONNECTOR_CLASSES + STUB_ADAPTER_CLASSES


def register_vendor_adapters() -> int:
    count = 0
    for adapter_class in VENDOR_ADAPTER_CLASSES:
        ProviderFactory.register_class(adapter_class)
        count += 1
    return count
