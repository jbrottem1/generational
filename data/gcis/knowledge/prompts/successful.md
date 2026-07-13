# Successful Prompts & Teaching Patterns

## Script pattern — Generational Method Short (~20–30s)

```
[HOOK 1 sentence, curiosity or paradox]
[DEMO cue — "Watch…" / "Look…"]
[MECHANISM in plain language, 2–3 sentences]
[REAL-WORLD analogy, 1 sentence]
[TAKEAWAY — one memorable line]
```

## Voice settings that worked
- Provider: OpenAI TTS · Voice: `onyx` · Model: `tts-1`  
- Tone: confident professor + science communicator (not hype YouTuber)

## Demo_id naming
- `bio_*` biology · `bowling_momentum` / `gravity_direction` educator physics  
- Register choreography plan under same id in `teaching_choreography.PLANS`

## Series runner pattern
Copy `scripts/biology_academy_vol1.py`: EPISODES list → TTS → `render_lip_sync_performance(educator_mode=True)` → `unique_path` export → report JSON/MD.
