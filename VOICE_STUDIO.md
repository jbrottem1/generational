# Voice Studio

Configurable narrator profiles and ElevenLabs voice comparison for Generational.

Voice Studio **does not** modify the production pipeline or renderer. It reuses:

- `services.media_production.voice.synthesize_voice`
- `services.elevenlabs` auth / voices / validation
- Profile resolution already used by narration

## Narrator profiles

| Profile | Env override |
| --- | --- |
| Professor | `ELEVENLABS_VOICE_PROFESSOR` |
| Documentary | `ELEVENLABS_VOICE_DOCUMENTARY` |
| Storyteller | `ELEVENLABS_VOICE_STORYTELLER` |
| Science Educator | `ELEVENLABS_VOICE_SCIENCE` |
| Technology Explainer | `ELEVENLABS_VOICE_TECH` |
| History Narrator | `ELEVENLABS_VOICE_HISTORY` |
| Calm Instructor | `ELEVENLABS_VOICE_CALM` |
| Energetic Presenter | `ELEVENLABS_VOICE_ENERGETIC` |

Voice IDs are stored only in:

1. `.env` (`ELEVENLABS_VOICE_*` / `ELEVENLABS_DEFAULT_VOICE_ID`)
2. `data/voice_studio/PROFILE_VOICES.json`

Never hardcoded in source.

Content-type routing (automatic profile choice) lives in `services/voice_studio/content_routing.py`.

## Commands

```bash
# 1. List account voices + profiles
python scripts/voice_studio.py list

# 2. Generate ~15s samples for every voice (optional --play on macOS)
python scripts/voice_studio.py sample
python scripts/voice_studio.py sample --play

# 3. Score voices (clarity, educational tone, energy, professionalism, long-form)
python scripts/voice_studio.py score

# 4. Recommend best voice per profile (+ optional write to PROFILE_VOICES.json)
python scripts/voice_studio.py recommend --apply

# 5. Change default / profile voice via configuration only
python scripts/voice_studio.py set-default --voice-id YOUR_VOICE_ID
python scripts/voice_studio.py set-default --profile professor --voice-id YOUR_VOICE_ID --also-default

# Select profile from content type
python scripts/voice_studio.py select --content-type science

# Full comparison report (same text, every voice)
python scripts/voice_studio.py compare
```

## Comparison

Default comparison text:

> Artificial intelligence is not a machine that thinks like a human. It is a system that learns patterns from data and uses those patterns to make useful predictions.

Outputs:

- `data/voice_studio/comparisons/run_*/`
- `data/voice_studio/comparisons/LATEST_COMPARISON_REPORT.json`
- `VOICE_COMPARISON_REPORT.md`

Publishing is disabled; only comparison assets and docs are produced.

## Changing the default voice

Preferred (runtime):

```env
ELEVENLABS_DEFAULT_VOICE_ID=your_voice_id
ELEVENLABS_VOICE_PROFESSOR=your_voice_id
```

Or edit `data/voice_studio/PROFILE_VOICES.json` / run `set-default`.
