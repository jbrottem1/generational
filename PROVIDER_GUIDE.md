# Provider Guide

Generational routes every external AI, publishing, and analytics system through
**ProviderRuntime** plus the **Provider Integration Management** control plane.

## Architecture

```
Settings UI ──► services/provider_integration ──► ProviderRuntime ──► connectors
                         │                              │
                         ├─ SecretManager (encrypted)   ├─ health / fallback
                         ├─ OAuth token map             ├─ cost / usage
                         └─ model defaults config       └─ retries / cache
```

## Categories

| Category | Examples |
|---|---|
| Text | OpenAI, Anthropic, Gemini, xAI, Ollama, OpenRouter (planned) |
| Image | Flux, Ideogram, OpenAI Images, Stability, Fal, Replicate |
| Video | Runway, Kling, Pika, Luma, Veo, ComfyUI |
| Voice | ElevenLabs, OpenAI TTS, Cartesia/PlayHT (planned) |
| Music | Suno/Udio (planned), music_future stub |
| Publishing | YouTube, TikTok, Instagram, Facebook, LinkedIn, X, Pinterest (planned) |
| Analytics | YouTube Analytics (registered), GA/Meta/TikTok/LinkedIn (planned) |

## Operator workflow

1. Open **Settings → API Keys** (or OAuth for platforms).
2. Set `PROVIDER_SECRETS_PASSPHRASE` in `.env` for encryption at rest.
3. Save keys — UI shows masked values only.
4. **Settings → Providers** → Test / Enable / Disable.
5. Set model defaults per role (text, image, video, …).
6. Monitor **Health** and **Costs**.

## Programmatic API

```python
from services.provider_integration import (
    set_api_key,
    list_registered_providers,
    run_provider_connection_test,
    get_model_defaults,
)

set_api_key("OPENAI_API_KEY", "sk-...")
print(run_provider_connection_test("openai"))
```

See also: [SETTINGS_GUIDE.md](SETTINGS_GUIDE.md), [ADDING_NEW_PROVIDER.md](ADDING_NEW_PROVIDER.md),
[PROVIDER_RUNTIME.md](PROVIDER_RUNTIME.md), [PROVIDER_INTEGRATION.md](PROVIDER_INTEGRATION.md).
