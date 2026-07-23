# Studio Voice Asset #0001 — Founder Voice

**Status:** Permanent Generational IP · **Default:** TRUE  
**Asset ID:** `VOICE-0001`  
**Provider:** ElevenLabs (cloned)  
**Path:** `data/studio_assets/VOICE-0001-FOUNDER-VOICE/`  
**Service:** `services/studio_assets/founder_voice/`  
**CLI:** `scripts/studio_asset_founder_voice.py`

Architecture remains frozen. Not a new voice engine. Uses existing ElevenLabs + Voice Studio.

---

## Behavior

| Case | Voice |
|------|--------|
| Narrator unspecified | **Founder Voice** (`VOICE-0001`) |
| Explicit `voice_id` / production override | Requested voice |
| Intentional `ELEVENLABS_VOICE_*` env (non-founder) | That profile override |

## Outputs

- `VOICE_PROFILE.json`  
- `VOICE_ASSET.json`  
- `VOICE_DEFAULT_CONFIG.json`  
- `VOICE_QA_REPORT.md`  

## Failover

1. Pause if ElevenLabs unavailable  
2. Reconnect + retry  
3. Fallback **only** if `ELEVENLABS_ALLOW_FALLBACK=1` or test mode  
4. Never silently replace Founder Voice  

## CLI

```bash
./venv/bin/python scripts/studio_asset_founder_voice.py ensure
./venv/bin/python scripts/studio_asset_founder_voice.py qa
./venv/bin/python scripts/studio_asset_founder_voice.py selftest
```
