# API Keys

## Resolution order

1. Runtime / session overrides  
2. Environment variables / `.env`  
3. Encrypted secrets file (`PROVIDER_SECRETS_PATH` or `data/provider_runtime/secrets.enc.json`)

## Encryption

```bash
# .env
PROVIDER_SECRETS_PASSPHRASE=choose-a-long-random-passphrase
# optional
PROVIDER_SECRETS_PATH=/secure/path/secrets.enc.json
```

Without a passphrase, Settings still accepts keys as in-memory overrides for the
process, but they will not persist encrypted on disk.

## UI

**Settings → API Keys**

- Add / update (password field)
- Delete
- Import JSON `{ "OPENAI_API_KEY": "sk-..." }`
- Validate provider id (format + presence only)

## Programmatic

```python
from services.provider_integration import set_api_key, delete_api_key, list_api_keys

set_api_key("OPENAI_API_KEY", "sk-...")
print(list_api_keys())  # masked only
delete_api_key("OPENAI_API_KEY")
```

## Rules

- Never log raw secrets.
- Never return raw secrets from list/inventory APIs.
- Rotate with `rotate_api_key(env_var, new_value)`.
