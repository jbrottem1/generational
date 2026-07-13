# Generational — Provider Connectors (Agent 22)

**Status:** LIVE · **Owner:** Agent 22 — Real Provider Integration & Production Connectors  
**Module home:** `services/provider_runtime/connectors/`  
**Runtime:** All calls route through `ProviderRuntime` — never bypass the Orchestrator.  
**Version:** 9.15.0

Engines call `services.provider_runtime.engine_api` helpers — never `core.ai`
or vendor SDKs. ProviderRuntime is the sole gateway to external AI services.

---

## Architecture

```
Orchestrator / Engines / Workflow Executor / Studio
                    ↓
         engine_api / ProviderRuntime.generate_*() / publish()
                    ↓
  Selection (weights/health) → Cache → Rate limit → Retry → Fallback
                    ↓
         ProductionConnector (per vendor)
                    ↓
              External AI / Platform APIs
```

---

## Connected providers

### Text / LLM
| Provider | Key | Env | Status |
|---|---|---|---|
| OpenAI | `openai` | `OPENAI_API_KEY` | Production (+ streaming) |
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` | Production |
| Google Gemini | `google_gemini` | `GOOGLE_API_KEY` | Production |
| xAI (Grok) | `xai` | `XAI_API_KEY` | Production |
| Ollama | `ollama` | `OLLAMA_HOST` | Production (local) |

### Image
| Provider | Key | Env | Status |
|---|---|---|---|
| OpenAI Images | `openai_images` | `OPENAI_API_KEY` | Production |
| Flux (BFL) | `flux` | `BFL_API_KEY` | Production |
| Ideogram | `ideogram` | `IDEOGRAM_API_KEY` | Production |
| Stability AI | `stability_ai` | `STABILITY_API_KEY` | Production |
| Fal.ai | `fal_ai` | `FAL_KEY` | Production |
| Replicate | `replicate` | `REPLICATE_API_TOKEN` | Production |
| ComfyUI | `comfyui` | `COMFYUI_ENDPOINT` | Production (local) |

### Video
| Provider | Key | Env | Status |
|---|---|---|---|
| Google Veo / Runway / Kling / Pika / Luma | respective keys | API keys | Production (async submit) |

### Voice
| Provider | Key | Env | Status |
|---|---|---|---|
| ElevenLabs | `elevenlabs` | `ELEVENLABS_API_KEY` | Production |
| OpenAI TTS | `openai_tts` | `OPENAI_API_KEY` | Production |

### Music
| Provider | Key | Status |
|---|---|---|
| Future Music | `music_future` | Abstraction (partial) |

### Publishing
| Platform | Key | Features |
|---|---|---|
| YouTube / TikTok / Instagram / Facebook / X / LinkedIn | platform tokens | OAuth refresh, chunked resume (YT), status poll, schedule |

### Still stub
`local_llm`, `demo` (offline fallback).

---

## Engine migration (complete)

| Former call | Runtime path |
|---|---|
| `core.ai.get_provider().generate_json` | `runtime_generate_json` |
| `get_image_provider().generate` | `runtime_generate_image` |
| `get_video_provider().generate` | `runtime_generate_video` |
| `get_voice_provider().synthesize` | `runtime_synthesize_voice` |

Engines: `ideation`, `script`, `script_generation`, `seo`, `narration`, `render/assets`.

---

## Runtime features

Auth, retries, rate limits, timeouts, fallback, health/circuit breakers, weighting,
blacklist/recovery, latency, caching, version pins, streaming, chunked uploads,
OAuth refresh, credential validation, audit log, analytics metrics bridge, cost/usage.

```python
runtime = get_provider_runtime()
runtime.metrics_summary()
runtime.validate_credentials()
runtime.blacklist_provider("runway", ttl_sec=300)
runtime.recover_provider("openai")
```

---

## Configuration

1. Copy `.env.example` → `.env` (never commit)
2. Optional `data/provider_runtime/config.json`
3. Optional `PROVIDER_SECRETS_PATH` + `PROVIDER_SECRETS_PASSPHRASE`

### Deployment checklist
- [ ] Keys for target modalities
- [ ] OAuth refresh for publishing
- [ ] Secrets passphrase in vault
- [ ] Rate limits tuned
- [ ] Analytics store writable
- [ ] Demo fallback OK for CI

---

## Testing

```bash
python -m pytest tests/test_provider_connectors.py \
  tests/test_provider_production.py \
  tests/test_provider_runtime.py -q
```

## Remaining blockers
1. Async video completion → final `video_url`
2. OAuth consent UI / token vault
3. Dedicated music vendors
4. Live load testing

See `PROVIDER_INTEGRATION.md`, `PRODUCTION_READINESS.md`.
