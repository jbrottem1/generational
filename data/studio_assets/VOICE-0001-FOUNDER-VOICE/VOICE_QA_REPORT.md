# Voice QA Report — Founder Voice (VOICE_ASSET_0001)

**Generated:** 2026-07-15T23:45:16.691546+00:00
**Production ready:** YES

## Checks

- ✓ `elevenlabs_api_key_loaded` — ELEVENLABS_API_KEY
- ✓ `elevenlabs_api_connected` — AUTHENTICATED
- ✓ `api_healthy` — voices/live narration ready
- ✓ `voice_id_exists` — id_suffix=…HiD3SP
- ✓ `voice_available` — cloned Founder Voice listed
- ✓ `audio_generated_successfully` — provider=elevenlabs
- ✓ `quota_available` — tts_probe
- ✓ `reject_fallback_when_available` — ELEVENLABS_ALLOW_FALLBACK=0 recommended

## Failover policy

- If ElevenLabs unavailable: pause, reconnect, retry.
- Fallback only if user sets `ELEVENLABS_ALLOW_FALLBACK=1` or production is test mode.
- Never silently replace Founder Voice.
