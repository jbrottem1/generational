"""Provider Integration Management — operator control plane over ProviderRuntime.

New providers install via one adapter + registration + catalog entry.
This package never hardcodes credentials and never returns secret values to UI.
"""

from services.provider_integration.catalog import (
    PROVIDER_CATEGORIES,
    MODEL_ROLES,
    OAUTH_PLATFORMS,
    catalog_by_category,
    list_registered_providers,
    register_catalog_entry,
)
from services.provider_integration.credentials import (
    delete_api_key,
    import_api_keys,
    list_api_keys,
    rotate_api_key,
    set_api_key,
    validate_api_key,
)
from services.provider_integration.management import (
    disable_provider,
    enable_provider,
    get_integration_dashboard,
    get_model_defaults,
    set_model_defaults,
    run_provider_connection_test,
)
from services.provider_integration.oauth import (
    disconnect_oauth,
    list_oauth_connections,
    save_oauth_tokens,
    run_oauth_connection_test,
)
from services.provider_integration.costs import get_cost_dashboard
from services.provider_integration.health import get_health_dashboard

__all__ = [
    "PROVIDER_CATEGORIES",
    "MODEL_ROLES",
    "OAUTH_PLATFORMS",
    "catalog_by_category",
    "list_registered_providers",
    "register_catalog_entry",
    "delete_api_key",
    "import_api_keys",
    "list_api_keys",
    "rotate_api_key",
    "set_api_key",
    "validate_api_key",
    "disable_provider",
    "enable_provider",
    "get_integration_dashboard",
    "get_model_defaults",
    "set_model_defaults",
    "run_provider_connection_test",
    "disconnect_oauth",
    "list_oauth_connections",
    "save_oauth_tokens",
    "run_oauth_connection_test",
    "get_cost_dashboard",
    "get_health_dashboard",
]
