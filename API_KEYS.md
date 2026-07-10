# API Keys

## Where keys live

**Primary:** project-root `.env` (gitignored)

```
/Users/.../Apps/generational/.env
```

Copy from `.env.example` if needed (the app also creates `.env` automatically on first boot when missing).

**Minimum to leave Demo Mode:**

```bash
OPENAI_API_KEY=sk-...
```

Then restart:

```bash
streamlit run app.py
```

## Resolution order

1. Runtime / session overrides (Settings save, SecretManager override)
2. Process environment / project-root `.env` (loaded at startup via `core.env`)
3. Encrypted secrets file (`PROVIDER_SECRETS_PATH` or `data/provider_runtime/secrets.enc.json`)

## Startup validation

On boot the app logs and shows:

- `✓ OPENAI_API_KEY loaded` → Demo Mode off
- `✗ OPENAI_API_KEY missing` → Demo Mode on (explicit warning, not silent)

## Encryption (optional)

```bash
# .env
PROVIDER_SECRETS_PASSPHRASE=choose-a-long-random-passphrase
# optional
PROVIDER_SECRETS_PATH=/secure/path/secrets.enc.json
```

## UI

**Settings → API Keys**

- Shows ✓/✗ load status for each provider env var
- Explains that `.env` is the primary config path
- **Save key** writes into `.env` + process env (and SecretManager when passphrase is set)
- Import JSON `{ "OPENAI_API_KEY": "sk-..." }`
- Validate provider id (format + presence only; never returns the secret)

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
- Never commit `.env`.
