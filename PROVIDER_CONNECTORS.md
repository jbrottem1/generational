# Generational — Provider Connectors (Agent 22)

**Status:** LIVE · **Owner:** Agent 22 — Real Provider Integration & Production Connectors  
**Module home:** `services/provider_runtime/connectors/`  
**Runtime:** All calls route through `ProviderRuntime` — never bypass the Orchestrator.

This layer replaces Phase-2 stub adapters with production HTTP connectors while
preserving the provider-agnostic architecture landed by Agent 19.

---

## Architecture

```
Orchestrator / Engines / Workflow Executor / Studio
                    ↓
            ProviderRuntime.generate_*() / publish()
                    ↓
     Selection → Cache → Rate limit → Retry → Fallback
                    ↓
         ProductionConnector (per vendor)
                    ↓
              External AI / Platform APIs
```

Engines and UI never import vendor SDKs. Credentials never appear in source.

---

## Connected providers

### Text
| Provider | Key | Env | Status |
|---|---|---|---|
| OpenAI | `openai` | `OPENAI_API_KEY` | Production |
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` | Production |
| Google Gemini | `google_gemini` | `GOOGLE_API_KEY` | Production |

### Image
| Provider | Key | Env | Status |
|---|---|---|---|
| OpenAI Images | `openai_images` | `OPENAI_API_KEY` | Production |
| Flux (BFL) | `flux` | `BFL_API_KEY` | Production |
| Ideogram | `ideogram` | `IDEOGRAM_API_KEY` | Production |
| Stability AI | `stability_ai` | `STABILITY_API_KEY` | Production |

### Video
| Provider | Key | Env | Status |
|---|---|---|---|
| Google Veo | `google_veo` | `GOOGLE_API_KEY` | Production (async jobs) |
| Runway | `runway` | `RUNWAY_API_KEY` | Production (async jobs) |
| Kling | `kling` | `KLING_API_KEY` | Production (async jobs) |
| Pika | `pika` | `PIKA_API_KEY` | Production (async jobs) |
| Luma | `luma` | `LUMA_API_KEY` | Production (async jobs) |

### Voice
| Provider | Key | Env | Status |
|---|---|---|---|
| ElevenLabs | `elevenlabs` | `ELEVENLABS_API_KEY` | Production |
| OpenAI TTS | `openai_tts` | `OPENAI_API_KEY` | Production |

### Music
| Provider | Key | Env | Status |
|---|---|---|---|
| Future Music | `music_future` | `MUSIC_PROVIDER_API_KEY` + `MUSIC_PROVIDER_ENDPOINT` | Abstraction (partial) |

### Publishing
| Platform | Runtime key | Env | Status |
|---|---|---|---|
| YouTube | `youtube` | `YOUTUBE_ACCESS_TOKEN` | Production |
| TikTok | `tiktok` | `TIKTOK_ACCESS_TOKEN` | Production |
| Instagram | `instagram` | `INSTAGRAM_ACCESS_TOKEN` + `INSTAGRAM_BUSINESS_ACCOUNT_ID` | Production |
| Facebook | `facebook` | `FACEBOOK_ACCESS_TOKEN` + `FACEBOOK_PAGE_ID` | Production |
| X | `x` | `X_ACCESS_TOKEN` | Production |

Legacy publishing adapters under `providers/publishing/` route through
ProviderRuntime when tokens are present; otherwise they keep the mock path.

### Still stubs (local / multi-model platforms)
`ollama`, `local_llm`, `replicate`, `fal_ai`, `comfyui` — registered stubs for
future wiring. `demo` remains the universal offline fallback.

---

## Runtime features

| Feature | Module | Behavior |
|---|---|---|
| Authentication | `connectors/base.py` + env | Bearer / vendor-specific headers |
| API key loading | `config.py`, `secrets.py` | Env → overrides → encrypted file |
| Health checks | `adapter.health_check`, `runtime.health_report` | Probe + circuit breaker |
| Retries | `execution.py` | Per-request `max_retries` |
| Rate limiting | `RateLimiter` | Per-provider RPM |
| Timeouts | `ProviderRequest.timeout_sec` | Passed to HTTP client |
| Fallback | `fallback.py` | Ranked alternates → demo |
| Usage tracking | `cost.py` | Per-call cost + success log |
| Cost estimation | `ProviderProfile.cost_per_unit` | Selection + response |
| Logging | `logging_utils.py` | Structured `provider.*` events |
| Caching | `cache.py` | Content-addressed TTL disk cache |
| Version management | `versioning.py` | Pinned API/model versions |
| Selection helpers | `runtime.best/cheapest/fastest/...` | Optimize for quality/cost/speed |

---

## Provider registry

`services/provider_runtime/registry.py` supports:

- Automatic discovery (`ensure_registered` / `discover_and_register`)
- Capability lookup (`capability_lookup`)
- Health scoring (`record_health_score` / `health_score`)
- Priority ordering (`set_priority` / `providers_by_priority`)
- Dynamic registration (`register_provider`)
- Plugin hooks (`register_plugin` / `run_plugins`)

---

## Security

1. Environment variables (`.env` via python-dotenv) — never commit `.env`
2. Runtime `credential_overrides` for tests / session keys
3. Encrypted secrets file (`PROVIDER_SECRETS_PATH` + `PROVIDER_SECRETS_PASSPHRASE`)
4. Key rotation via `SecretManager.rotate()`
5. No hardcoded credentials in connectors

---

## Usage

```python
from services.provider_runtime import get_provider_runtime

runtime = get_provider_runtime()

runtime.generate_script({"prompt": "Write a 30s hook about focus"})
runtime.generate_image({"prompt": "cinematic thumbnail, 9:16"})
runtime.generate_video({"prompt": "drone shot over mountains"})
runtime.generate_voice({"text": "Welcome to Generational"})
runtime.publish({"package": {"title": "My Short", "video": {"uri": "..."}}})

runtime.best_provider("image_generation")
runtime.cheapest_provider("llm")
runtime.fastest_provider("speech")
runtime.catalog()
runtime.health_report()
runtime.usage_summary()
runtime.versions()
```

---

## Testing

```bash
python -m pytest tests/test_provider_connectors.py tests/test_provider_runtime.py -q
```

Coverage includes mock HTTP transports, integration success paths, failure +
fallback, rate limits, cache, secrets, version pins, and publishing routing.

---

## Remaining integrations

- Poll/complete async video jobs into final `video_url` assets
- Binary upload streams for YouTube/TikTok resumable uploads
- OAuth refresh-token flows for publishing platforms
- Wire `replicate` / `fal_ai` / `comfyui` / `ollama` production connectors
- Migrate remaining engine `core.ai` / legacy `get_*_provider()` call sites
  fully onto `ProviderRuntime.generate_*()` (architecture already supports it)
- Dedicated music vendors (Suno/Udio) behind `music_future`

See also: `PROVIDER_INTEGRATION.md`, `PIPELINE_SPEC.md`, `DATA_CONTRACTS.md`.
