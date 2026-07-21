# Voice Configuration

Narrator profiles for Generational production TTS (ElevenLabs).

Managed by **Voice Studio** (`VOICE_STUDIO.md`). Permanent default narrator is **Founder Voice** (`VOICE_ASSET_0001_FOUNDER_VOICE.md` / `VOICE-0001`) — cloned ElevenLabs. Voice IDs live in `.env` or `data/voice_studio/PROFILE_VOICES.json` — never commit API keys.

## Profiles

| Profile key | Label | Typical use | Env override |
| --- | --- | --- | --- |
| `professor` | Professor | Educational explainers | `ELEVENLABS_VOICE_PROFESSOR` |
| `documentary` | Documentary | Calm cinematic | `ELEVENLABS_VOICE_DOCUMENTARY` |
| `storyteller` | Storyteller | Narrative | `ELEVENLABS_VOICE_STORYTELLER` |
| `science_educator` | Science Educator | Science topics | `ELEVENLABS_VOICE_SCIENCE` |
| `technology_explainer` | Technology Explainer | Tech / AI | `ELEVENLABS_VOICE_TECH` |
| `history_narrator` | History Narrator | History | `ELEVENLABS_VOICE_HISTORY` |
| `calm_instructor` | Calm Instructor | Soft classroom | `ELEVENLABS_VOICE_CALM` |
| `energetic_presenter` | Energetic Presenter | High-energy Shorts | `ELEVENLABS_VOICE_ENERGETIC` |

Legacy aliases: `energetic_explainer`, `calm_educator` still resolve.

## Resolution order

For a narrator request, voice ID is chosen as:

1. Explicit `provider_voice_id` / `voice_id` on the voice profile
2. Profile-specific env (`ELEVENLABS_VOICE_*`)
3. `ELEVENLABS_DEFAULT_VOICE_ID`
4. Built-in public default voice ID (Rachel) — replace via env for branded VO

Model ID always comes from `ELEVENLABS_MODEL_ID` (default `eleven_multilingual_v2`).

Stability / similarity boosts are profile defaults in `services/elevenlabs/voices.py` and can be adjusted there without hardcoding API keys.

## Studio brief

`StudioBrief.narrator` flows into ops context as `narrator` / `narration_style`, then into `VoiceEngine` → `synthesize_voice(..., narrator=...)`.

Example:

```python
brief.narrator = "professor"  # or "Professor"
```

## Finding voice IDs

```bash
python scripts/elevenlabs_verify.py voices
```

Copy a `voice_id` into `.env`:

```env
ELEVENLABS_DEFAULT_VOICE_ID=21m00Tcm4TlvDq8ikWAM
ELEVENLABS_VOICE_PROFESSOR=your_professor_voice_id
```

## Fallback policy

| `ELEVENLABS_ALLOW_FALLBACK` | Behavior |
| --- | --- |
| `1` (default) | On ElevenLabs failure, ProviderRuntime may use OpenAI TTS / local bed |
| `0` | Fail narration; production package still records the error |

The final package always reports which provider produced audio (`voice_package.provider`).

## Voice cloning (future)

Map a cloned ElevenLabs voice ID to a profile env key. Prefer a dedicated profile over inventing a second synthesis module.
