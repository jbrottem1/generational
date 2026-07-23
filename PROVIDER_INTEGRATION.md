# Generational — Provider Integration Layer (Agent 19)

**Status:** LIVE · **Owner:** Agent 19 — Provider Integration & Runtime Engine  
**Module home:** `services/provider_runtime/`

The Provider Integration Layer is the permanent foundation for calling external
AI services without coupling engines to any vendor. All communication flows
through documented contracts and the orchestration layer — engines never import
vendor SDKs directly.

---

## Architecture

```
Orchestrator / Engines / Services
            ↓
    ProviderRuntime (generate_* API)
            ↓
  ProviderSelectionEngine → ProviderFallbackManager
            ↓
    ProviderRegistry → ProviderAdapter (per vendor)
            ↓
       External AI APIs
```

### Core components

| Component | Module | Role |
|---|---|---|
| `ProviderAdapter` | `adapter.py` | Universal adapter interface |
| `ProviderRegistry` | `registry.py` | Central catalog, auto-discovery |
| `ProviderFactory` | `factory.py` | Instantiate adapters from classes |
| `ProviderCapabilities` | `capabilities.py` | Capability vocabulary |
| `ProviderRuntime` | `runtime.py` | Unified `generate_*()` surface |
| `ProviderSelectionEngine` | `selection.py` | Capability-based routing |
| `ProviderFallbackManager` | `fallback.py` | Graceful degradation |
| `ProviderHealthMonitor` | `health.py` | Circuit breakers |
| `ProviderCostEstimator` | `cost.py` | Cost tracking + usage logging |
| `RuntimeExecutionEngine` | `longform.py` | Checkpointed long-form jobs |

---

## Public API

```python
from services.provider_runtime import get_provider_runtime

runtime = get_provider_runtime()

# High-level operations — provider selected automatically
runtime.generate_script({"prompt": "...", "system_prompt": "..."})
runtime.generate_image({"prompt": "sunset over mountains"})
runtime.generate_video({"prompt": "cinematic drone shot"})
runtime.generate_voice({"text": "Hello world"})
runtime.generate_music({"mood": "uplifting", "duration_sec": 60})
runtime.generate_thumbnail({"title": "10 Focus Hacks"})
runtime.generate_caption({"script": "..."})
runtime.generate_subtitles({"transcript": "..."})
runtime.generate_metadata({"title": "...", "niche": "psychology"})

# Introspection
runtime.catalog()          # all registered providers
runtime.health_report()    # circuit breaker state
runtime.usage_summary()    # cost + call counts
```

---

## Supported providers

Production connectors (Agent 22) implement real HTTP `execute()` paths.
See `PROVIDER_CONNECTORS.md` for the full catalog, auth, and remaining work.

| Provider | Key | Capabilities | Env var | Status |
|---|---|---|---|---|
| OpenAI | `openai` | LLM, script, image | `OPENAI_API_KEY` | Production |
| OpenAI Images | `openai_images` | Image, thumbnail | `OPENAI_API_KEY` | Production |
| OpenAI TTS | `openai_tts` | Speech | `OPENAI_API_KEY` | Production |
| Anthropic | `anthropic` | LLM, reasoning | `ANTHROPIC_API_KEY` | Production |
| Google Gemini | `google_gemini` | LLM, image | `GOOGLE_API_KEY` | Production |
| Google Veo | `google_veo` | Video, animation | `GOOGLE_API_KEY` | Production |
| Runway | `runway` | Video, animation, lip sync | `RUNWAY_API_KEY` | Production |
| ElevenLabs | `elevenlabs` | Speech, voice clone, SFX, music | `ELEVENLABS_API_KEY` | Production |
| Flux | `flux` | Image generation | `BFL_API_KEY` | Production |
| Ideogram | `ideogram` | Image, thumbnail | `IDEOGRAM_API_KEY` | Production |
| Pika | `pika` | Video, animation | `PIKA_API_KEY` | Production |
| Kling | `kling` | Video, animation | `KLING_API_KEY` | Production |
| Luma | `luma` | Video, 3D | `LUMA_API_KEY` | Production |
| Stability AI | `stability_ai` | Image, upscaling | `STABILITY_API_KEY` | Production |
| YouTube / TikTok / IG / FB / X | `youtube`… | Publish | platform tokens | Production |
| Future Music | `music_future` | Music | `MUSIC_PROVIDER_*` | Partial |
| Replicate | `replicate` | Image, video, upscaling | `REPLICATE_API_TOKEN` | Production |
| Fal.ai | `fal_ai` | Image, video, lip sync | `FAL_KEY` | Production |
| ComfyUI | `comfyui` | Local image/video | `COMFYUI_ENDPOINT` | Production |
| Ollama | `ollama` | Local LLM | `OLLAMA_HOST` | Production |
| xAI | `xai` | LLM, reasoning | `XAI_API_KEY` | Production |
| Local LLM | `local_llm` | Local LLM | `LOCAL_LLM_ENDPOINT` | Stub |
| Demo | `demo` | All (deterministic fallback) | — | Always |

Legacy adapters from `providers/asset_generation/` are bridged automatically.

---

## Credential loading

Priority order:

1. Runtime credential overrides (`ProviderRuntime(credential_overrides={...})`)
2. Environment variables
3. `.env` file (via `python-dotenv` at startup)
4. Encrypted secrets (`PROVIDER_SECRETS_PATH` + `PROVIDER_SECRETS_PASSPHRASE`)
5. Optional JSON config (`PROVIDER_CONFIG_PATH` or `data/provider_runtime/config.json`)

**Never hardcode API keys.** See `PROVIDER_CONNECTORS.md` for rotation helpers.

---

## Error recovery

- Automatic retries (`max_retries` on `ProviderRequest`)
- Timeout handling (`timeout_sec`)
- Rate limiting (`RateLimiter`, configurable RPM)
- Provider fallback chain (`ProviderFallbackManager`)
- Circuit breakers (`ProviderHealthMonitor`)
- Cost estimation and usage logging (`ProviderCostEstimator`)
- Graceful degradation to demo provider

---

## Parallel execution

```python
runtime.generate_image(
    {"prompt": "..."},
    parallel_candidates=3,
    optimize_for="quality",  # quality | speed | cost
)
```

Runs up to N providers in parallel; selects best result by optimization goal.

---

## Long-form content

`RuntimeExecutionEngine` supports multi-hour productions with checkpoints:

```python
from services.provider_runtime import RuntimeExecutionEngine

engine = RuntimeExecutionEngine()
result = engine.run(
    "Create a 45-minute documentary about quantum computing",
    production_type="documentary",
    options={"count": 1},
)

# Resume after interruption
result = engine.run("", resume_job_id=result["job_id"])
```

Checkpoints persist to `data/provider_runtime/checkpoints/`. Job queue type:
`longform_pipeline` (register via `ensure_runtime_handlers(queue)`).

---

## Adding a new provider

1. Subclass `ProviderAdapter` or `StubAdapter` in `services/provider_runtime/adapters/`
2. Declare `name`, `capabilities`, `api_key_env`, and `profile`
3. Register via `ProviderFactory.register_class()` in `adapters/vendors.py`
4. Implement `execute()` with real API calls when ready

No engine or orchestrator changes required.

---

## Integration points

| Consumer | Integration |
|---|---|
| Orchestrator | `ensure_runtime_handlers(queue)` for long-form jobs |
| Asset Generation | Bridged via `bridge.py` from `providers/asset_generation/` |
| LLM engines | Bridged via `core.ai` → `_LegacyLLMBridge` |
| Future engines | Call `get_provider_runtime().generate_*()` |

---

## Tests

`tests/test_provider_runtime.py` — registration, selection, fallback, retry,
health, cost, runtime execution, config loading, mock providers, long-form
checkpoints.
