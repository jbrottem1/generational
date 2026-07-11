# Dash Stick Figure Universe — Foundation Charter

**Status:** ACTIVE foundation  
**Series:** Dash Science (`SERIES-DASH-SCIENCE`)  
**Mascot:** Dash (`CHAR-DASH`) v1.0.0 LOCKED  
**Parent:** PROJECT GENERATIONAL VISUAL UNIVERSE  
**Established:** 2026-07-10  

This is the beginning of an expandable faceless animation brand — not a one-off video.

---

## What shipped in this foundation

| Layer | Path | Purpose |
|---|---|---|
| Series bible | `data/universe/series/dash_science/SERIES_BIBLE.md` | Brand, voice, episode formula |
| Production schema | `data/universe/series/dash_science/production_schema.json` | Automation contract |
| Automation hooks | `data/universe/series/dash_science/automation_hooks.md` | Map onto existing pipeline |
| Character lock | `data/universe/characters/CHAR-DASH/` | Design, expressions, prompt lock |
| Animation library | `data/universe/animation/` | 23 reusable motion components |
| Mock episodes (3) | `data/universe/productions/mock_dash_*/` | Full creative packages |

---

## Mock productions

1. **The Ocean Is Secretly Glowing** — `mock_dash_ocean_glow` (40s)  
2. **Your Body Is Constantly Replacing Itself** — `mock_dash_body_replace` (42s)  
3. **Why Fireflies Glow** — `mock_dash_fireflies` (38s)  

Each package includes: script, scenes, timing, camera, backgrounds, character movement, expressions, visual/image prompts, transitions, SFX, music, captions, thumbnail, SEO title/description/hashtags.

---

## Scalability rule

Future episodes must:

1. Reuse `CHAR-DASH` without redesign  
2. Compose motion only from `ANIM-DASH-V1` (extend library via version bump)  
3. Emit a valid `episode_package` JSON  
4. Pass Dash QC gates (on-screen time, no static >3s, no flat full backgrounds)

Thousands of episodes = same host, same motion language, new science.
