# ElevenLabs Integration

Official production narration provider for Generational.

ElevenLabs is wired into the **existing** voice path — not a parallel demo system.

```
Research → Psychology → Script → Scene Builder → Media
  → Voice (ElevenLabs) → Music → Captions → Rendering → QA → Export
```

## Architecture (reuse, don't duplicate)

| Layer | Module | Role |
| --- | --- | --- |
| Config | `services/elevenlabs/config.py` | Env-only keys, model, fallbacks |
| Voices | `services/elevenlabs/voices.py` | Narrator profiles → voice IDs |
| Auth | `services/elevenlabs/auth.py` | Live verification |
| Audio QA | `services/elevenlabs/validation.py` | File / duration / renderer checks |
| Facade | `services/media_production/voice.py` | `synthesize_voice()` |
| Connector | `services/provider_runtime/connectors/voice.py` | HTTP + official SDK TTS |
| Engine | `engines/voice.py` | Ops stage `voice_generation` |

Engines never import `elevenlabs` directly (architecture rule). The SDK lives under `services/`.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Copy env template and set secrets (project root `.env` — never commit):

```bash
cp .env.example .env
```

3. Required / recommended variables:

| Variable | Required | Purpose |
| --- | --- | --- |
| `ELEVENLABS_API_KEY` | Yes | Authentication (never commit) |
| `ELEVENLABS_DEFAULT_VOICE_ID` | Recommended | Default voice when profile unset |
| `ELEVENLABS_MODEL_ID` | Optional | Default `eleven_multilingual_v2` |
| `ELEVENLABS_OUTPUT_FORMAT` | Optional | Default `mp3_44100_128` |
| `ELEVENLABS_REQUEST_TIMEOUT` | Optional | Default `90` seconds |
| `ELEVENLABS_MAX_RETRIES` | Optional | Default `2` |
| `ELEVENLABS_VOICE_PROFESSOR` etc. | Optional | Per-narrator overrides |
| `ELEVENLABS_ALLOW_FALLBACK` | Optional | `1` (default) allows OpenAI/local fallback |
| `ELEVENLABS_USE_SDK` | Optional | `1` (default) prefer official SDK |

Auth health uses `/voices` (TTS-capable keys may lack `user_read` on `/user`).

See [VOICE_CONFIGURATION.md](VOICE_CONFIGURATION.md).

## Verification commands

```bash
# Health / auth
python scripts/elevenlabs_verify.py health

# List account voices
python scripts/elevenlabs_verify.py voices

# Narration clip (Professor by default)
python scripts/elevenlabs_verify.py narrate --narrator professor

# Same facade the ops voice stage uses
python scripts/elevenlabs_verify.py pipeline --topic "What Artificial Intelligence Actually Is"

# Full live proof gate
python scripts/elevenlabs_verify.py e2e
```

## Production behavior

- When `ELEVENLABS_API_KEY` is set, `synthesize_voice` prefers ElevenLabs.
- Studio brief `narrator` (e.g. Professor) maps to a configurable voice ID.
- Generated `voice_package` includes:
  - `provider` / `official_narration_provider`
  - `narrator_profile`, `voice_id`, `model_id`
  - `audio_qa`, timing for captions
- If ElevenLabs fails and `ELEVENLABS_ALLOW_FALLBACK=0`, the job fails clearly instead of silent local TTS.
- ProviderRuntime already retries and rate-limits connector calls.

## Tests

```bash
pytest tests/test_elevenlabs_integration.py -q
# Live integration (requires API key):
pytest tests/test_elevenlabs_integration.py -q -m integration
```

## Live proof artifact

Successful runs write under:

`data/productions/_validation/elevenlabs/`

- `E2E_VOICE_VERIFICATION.json`
- `PIPELINE_NARRATION_TEST.json`
- `NARRATION_TEST.json`

## Future: voice cloning

Capability already declared on `ElevenLabsConnector` (`VOICE_CLONING`). Cloning support should:

1. Add env `ELEVENLABS_CLONE_VOICE_ID` / managed clone IDs
2. Extend `resolve_narrator_profile` with a `custom_clone` profile
3. Keep engines thin — only pass `provider_voice_id` through `synthesize_voice`

Do not add a second TTS pipeline when cloning lands.
