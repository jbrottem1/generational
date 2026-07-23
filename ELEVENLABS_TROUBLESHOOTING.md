# ElevenLabs Troubleshooting

## Authentication failures

**Symptom:** `api_key_loads` false / health exits non-zero

1. Confirm project-root `.env` has a non-empty `ELEVENLABS_API_KEY=...`
2. Restart the process after editing `.env` (env loads once at startup)
3. Do not put the key in committed files or chat logs
4. Run:

```bash
python scripts/elevenlabs_verify.py health
```

**Symptom:** Key loads but `authentication_succeeds` false

- Key revoked or wrong product key
- Account suspended / API disabled
- Network blocked to `https://api.elevenlabs.io`

## Voices list empty

```bash
python scripts/elevenlabs_verify.py voices
```

- If SDK errors but HTTP works, set `ELEVENLABS_USE_SDK=0` temporarily
- Confirm the key has voice-read permission on the plan

## Default voice missing

Set an ID that exists on your account:

```env
ELEVENLABS_DEFAULT_VOICE_ID=<id from voices command>
```

## Invalid voice ID

**Symptoms:** TTS 404 / empty audio / `ElevenLabs TTS error`

- Run `voices` and paste a valid `voice_id`
- Clear stale overrides (`ELEVENLABS_VOICE_PROFESSOR=...`)

## Rate limits / quota

**Symptoms:** `429`, `Rate limit exceeded`, quota messages

- ProviderRuntime retries with backoff; wait and re-run
- Lower concurrent production jobs
- Check ElevenLabs usage dashboard
- Optionally set `ELEVENLABS_ALLOW_FALLBACK=1` so jobs continue with OpenAI/local (package still labels the real provider)

## Timeouts / network

- Increase job timeout upstream if scripts are very long
- Check firewall / DNS / VPN
- SDK failures automatically fall through to the HTTP connector path

## Audio QA failures

`validate_narration_audio` rejects:

| Hard fail | Meaning |
| --- | --- |
| `missing_path` / `file_missing` | Persist step did not write a file |
| `file_too_small` | Corrupt / empty payload |
| `zero_or_short_duration` | Silent or truncated |
| `not_renderer_compatible` | No readable audio stream for ffmpeg |

Install `ffmpeg` / `ffprobe` for accurate duration and stream checks.

## Captions out of sync

- Prefer timestamped TTS (`with_timestamps`) — enabled by default for ElevenLabs
- Ensure `voice_package.timing` is present before the caption stage
- Re-run narration if duration was estimated because audio was empty

## Wrong provider in package

If package shows OpenAI/local instead of ElevenLabs:

1. Confirm `ELEVENLABS_API_KEY` is set
2. Check errors on the first attempt (quota/auth)
3. Set `ELEVENLABS_ALLOW_FALLBACK=0` to force fail-closed during debugging

## Architecture mistakes to avoid

- Do not import `elevenlabs` from `engines/`
- Do not create a second TTS pipeline beside `synthesize_voice`
- Do not hardcode API keys in adapters or docs
