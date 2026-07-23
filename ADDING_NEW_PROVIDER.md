# Adding a New Provider

No architecture changes required. Follow the plugin surface:

## 1. Adapter

Create a connector under `services/provider_runtime/connectors/` implementing
`ProviderAdapter` / `ProductionConnector`:

- `name`, `label`, `capabilities`, `api_key_env`
- `execute(request) -> ProviderResponse`
- optional `health_check()`

## 2. Registration

Add the class to `PRODUCTION_CONNECTOR_CLASSES` in
`services/provider_runtime/connectors/__init__.py` (or register via
`ProviderFactory.register_class` / `register_plugin`).

## 3. Configuration entry

Document the env var in [API_KEYS.md](API_KEYS.md) and optionally extend
`PROVIDER_PERMISSIONS` in `services/provider_runtime/security.py` for validation.

For providers not yet implemented, register metadata only:

```python
from services.provider_integration import register_catalog_entry

register_catalog_entry({
    "name": "my_provider",
    "label": "My Provider",
    "category": "text",
    "api_key_env": "MY_PROVIDER_API_KEY",
    "capabilities": ["llm"],
    "status": "planned",
})
```

## 4. Verify

1. Settings → Providers shows the new entry.  
2. Save an API key under the declared env var.  
3. Click **Test**.  
4. Add unit tests under `tests/test_provider_*.py`.

## Do not

- Hardcode credentials
- Import vendor SDKs from engines
- Bypass ProviderRuntime from Studio / Orchestrator paths
