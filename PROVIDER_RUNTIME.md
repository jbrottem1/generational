# Provider Runtime

ProviderRuntime is the sole AI/publishing execution gateway for engines.

## Location

`services/provider_runtime/`

## Responsibilities

- Adapter registry & catalog
- Selection / fallback / parallel race
- Retries, rate limits, circuit breakers
- Cost estimation & usage summary
- Health monitoring
- Secret resolution
- Long-form checkpoints
- Chunked / resumable uploads
- OAuth token refresh helper

## Public entry

```python
from services.provider_runtime import get_provider_runtime

runtime = get_provider_runtime()
runtime.catalog()
runtime.health_report()
runtime.usage_summary()
runtime.generate_text(...)
```

Engines must call `services.provider_runtime.engine_api` — never vendor SDKs.

## Management layer

Operator configuration lives in `services/provider_integration/` and the Settings UI.
Runtime executes; Integration Management configures and monitors.

Full connector catalog: [PROVIDER_CONNECTORS.md](PROVIDER_CONNECTORS.md).
