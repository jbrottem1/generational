# AI Studio Director V5.0

The Studio Director is the creative brain of the Generational AI Media Operating System.

Before any video is produced, it builds a **Production Blueprint** from topic, audience, platform, goals, and historical performance — then applies that unified vision so every downstream engine works toward the same creative direction.

Engine key: `ai_director`  
Version: `5.0.0`  
Service: `services/ai_director/`

## Pipeline position

```
Psychology → Audience Intelligence → AI Studio Director (blueprint)
  → Script → Visuals → Cinematography → Retention → Voice
  → Studio Render → Optimization Lab → Production QA
```

Executive stage: `direction` (between `research` and `script`)

Workflows:

- `intelligence` / `full_content` — after `audience_intelligence`, before `script_generation`
- `media_production` — first engine in the list

## Production Blueprint

Every project receives:

| Field | Purpose |
|---|---|
| Topic, audience, age, knowledge level | Who the piece is for |
| Platform, video length | Format constraints |
| Educational / entertainment goals | Dual intent |
| Emotion & curiosity curves | Retention architecture |
| Retention targets | 3s / 10s / mid / completion |
| Visual, animation, color, camera | Look & feel |
| Narration & music style | Sound identity |
| Editing style | Cut length, density, captions |
| Thumbnail & SEO strategy | Discovery |
| Publishing time | Timing |
| Expected competition / difficulty | Market reality |
| Expected CTR / watch time / completion | Forecasts |
| Competitor analysis + differentiation | Originality with edge |
| Production plan | Engine handoff order |

No production engine should invent its own creative assumptions when a blueprint is present.

## Style Library

Reusable production styles (`services/ai_director/styles.py`):

- Modern Documentary
- Minimal Whiteboard
- Science Documentary
- Kurzgesagt Inspired
- Vox Inspired
- Apple Keynote
- History Channel
- National Geographic
- Technology Review
- Space Documentary
- Medical Animation
- Corporate Explainer

Each style defines motion, typography, transitions, music, narration, colors, camera, and graphics — mapped onto studio render grades and optimization visual styles.

## Visual / narration / music / editing direction

Chosen **before scripting**:

- Visual modality: real imagery, illustrations, 3D, motion graphics, stock, government imagery, hybrid
- Narration personas: confident, conversational, teacher, professor, storyteller, documentary host, engineer, scientist
- Music: ambient, inspirational, epic, technology, space, documentary, minimal, electronic, cinematic orchestra
- Editing: average cut length, transition density, movement intensity, caption frequency, animation/graphic density

## Platform strategy

Presets for YouTube Shorts, TikTok, Instagram Reels, Facebook Reels, X, Pinterest, LinkedIn, and YouTube long-form (aspect, max length, hook window, SEO focus).

## Competitor analysis

Before create: top creators, avg views/length/pacing, thumbnail/hook/editing/narration styles, publishing frequency — plus differentiation recommendations and originality guardrails.

## Downstream handoff

`apply_blueprint_to_candidate` writes additive fields:

- `production_blueprint`, `director_package`
- `visual_style`, `narration_style`, `music_mood`, `preferred_camera_moves`
- `color_palette`, `color_grade_profile`, `creative_style_id`
- `retention_targets`, `emotion_curve`, `curiosity_curve`
- `director_expectations` (CTR, watch time, completion)

Legacy `DirectorPackage` fields remain; V5 adds `production_blueprint` (additive contract).

## Success criteria

1. Every project feels intentionally directed
2. Different topics resolve to different styles (not mechanically identical)
3. Directed candidates score 100 on blueprint consistency; undirected score 0
4. All engines in the production plan receive precise instructions

## Validation

```bash
python -m pytest tests/test_studio_director_v5.py tests/test_ai_director.py tests/test_ai_director_engine.py -q
python scripts/verify_studio_director_e2e.py
```

Artifacts: `data/productions/_validation/studio_director/`

See also: `AI_DIRECTOR.md` (Agent 18 package contract), `DATA_CONTRACTS.md` § director_package.
