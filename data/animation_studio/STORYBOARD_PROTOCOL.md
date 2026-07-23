# Storyboard Protocol

**Owner:** Animation Director (Agent 16) · Support: Agents 4, 3  
**Rule:** Convert every script into a storyboard **before** treating frames as final.

---

## Per-sentence / per-beat questions (mandatory)

1. **Who** is on screen?  
2. **What** are they doing?  
3. **What** is moving (character, env, prop, FX)?  
4. **Where** is the camera (preset ID)?  
5. **What emotion** should the audience feel?  
6. **How** does the scene transition?

---

## Beat schema

```json
{
  "beat_id": "B1",
  "t_start": 0.0,
  "t_end": 3.0,
  "narration": "...",
  "who": ["CHAR-DASH"],
  "action": "walk_cycle + talk_bob",
  "moving": ["character", "ENVFX-particle-field"],
  "camera": "push_in",
  "emotion": "curious",
  "transition_out": "hard_cut",
  "environment_fx": ["ENVFX-particle-field"],
  "animation_components": ["walk_cycle", "talk_bob"]
}
```

---

## Density

- Something meaningful changes every **2–4 seconds**  
- No static frame > **3.0 seconds**  
- Host action OR environment FX OR camera verb must be active each beat  

---

## Automation

`services/asset_production/storyboard.py` builds a `storyboard_package` from scene breakdowns and attaches it to the asset before image generation. Human/Animation Director may revise IDs; generators must consume the package.
