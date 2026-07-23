# Visual Production Package — Contract Reference

The **Visual Production Package** is the complete, directed visual plan the
Visual Intelligence Engine (the Cinematic AI Director) attaches to every
scripted candidate as `candidate["visual_package"]`. Every downstream
consumer — Voice & Audio, the future Render Engine, the UI — reads this one
JSON-safe dict. This document is the contract: keys are additive; removing
or renaming a key is a breaking change.

Produced by: `services/visual/package.py::build_visual_package(idea, niche=, subject=, aspect_ratio=, style_key=, attention=)`

## Inputs the Director consumes

| Source | What it provides |
|---|---|
| Trend Discovery / Research | `niche`, `subject` context |
| Psychology Engine | concept-level psychology signals on the candidate |
| Script Engine | the canonical `structured_script` handoff (scene breakdown, timestamps, emotional beats); falls back to script variants / raw script |
| Attention Graph | `attention_graph.scores` (hook / rewatch) feeding per-scene retention prediction — the Attention Graph runs **before** Visual Intelligence in the pipeline |

An operator or brand system may force a style via `context["visual_style"]`
(any key from `services/visual/styles.py`); otherwise the niche default
applies, falling back to `cinematic`.

## Top-level keys

| Key | Type | Contents |
|---|---|---|
| `visual_score` | int 0-100 | Weighted overall score (`PACKAGE_SCORE_WEIGHTS`) |
| `score_components` | dict | scene_visuals, hook_strength, predicted_retention, thumbnail_power, pacing_fitness, camera_variety |
| `summary` | str | Plain-English one-paragraph verdict |
| `aspect_ratio` | str | e.g. `"9:16"` (from the platform spec) |
| `visual_style` | str | Resolved style preset key |
| `style_preset` | dict | The full resolved preset (palette, lighting bias, art style, grade, overlay/caption style, mood) |
| `color_palette` | str | The style's palette (applied to every scene) |
| `storyboard` | list | Compact human-readable panels (one per scene) |
| `scenes` | list | Full directed scene dicts — see below |
| `shot_list` | list | Professional shot list (shot type, lens, DOF, motion, composition per scene) |
| `asset_requests` | list | Provider-agnostic asset request per scene, routed through source adapters |
| `image_prompts` | list | Per scene: model-agnostic spec + dialect prompts for Midjourney, Flux, Stable Diffusion, DALL-E, OpenAI Images |
| `video_prompts` | list | Per scene: spec + dialect prompts for Runway, Veo, Pika, Luma, Kling, Sora |
| `thumbnails` | list | Five scored concepts, best first — see below |
| `hook_sequence` | dict | Five-frame first-3-second plan + scroll-stop rationale |
| `caption_plan` | list | Timed caption segments (text, overlay, placement, style) |
| `pacing_report` | dict | Cut rhythm diagnostics vs. the retention ideal |
| `camera_plan` | dict | Per-scene camera setups + variety score |
| `transitions` | list | Scene-to-scene transition map |
| `motion_report` | dict | Motion energy: average, level, peak, per-scene curve |
| `retention_curve` | dict | Predicted retention per scene, average, final, weakest scene |
| `render_package` | dict | Machine-consumable handoff for the Render Engine — see below |

## Scene contract (`scenes[]`)

Every scene carries all fields in
`services/visual/models.py::REQUIRED_SCENE_COMPONENTS`:

| Field group | Fields |
|---|---|
| Identity | `scene_number`, `purpose` (hook / pattern_interrupt / curiosity_loop / story_beat / payoff / cta), `emotion`, `length_sec`, `narration` |
| Attention | `attention_level` (high/medium/low), `predicted_retention` (0-100), `visual_scores` (12 triggers), `visual_score`, `thumbnail_candidate` (bool) |
| Camera | `shot_type` (14-shot vocabulary), `camera_angle`, `camera_motion`, `lens_recommendation`, `depth_of_field`, `zoom` |
| Art direction | `visual_style`, `visual_description`, `shot_composition`, `subject_placement`, `lighting`, `environment`, `color_palette`, `background` |
| Motion & cuts | `motion_intensity` (0-100), `motion_recommendation`, `transition_in`, `transition_out` |
| Sourcing | `asset_type` (adapter key), `ai_image_prompt`, `ai_video_prompt`, `stock_footage_query`, `broll` |
| Overlays & timing | `overlay`, `text_overlay`, `caption_placement`, `caption_timing` {start_sec, end_sec}, `sound_effect`, `sfx_timing` {at_sec, cue}, `music_style` |

The 12 visual psychology triggers scored per scene: curiosity,
pattern_interrupt, contrast, novelty, human_faces, eye_contact, motion,
scale, speed, emotional_color, negative_space, visual_hierarchy.

## Thumbnail contract (`thumbnails[]`)

Each of the five concepts carries: `label`, `description`, `title_overlay`,
`emotion`, `color_strategy`, `focal_subject`, `eye_direction`,
`composition`, `scores` (curiosity, readability, contrast, facial_focus,
object_focus, color, emotion — each 0-100), `contrast_score`, `overall`,
and `click_probability_pct` (calibrated 1.5–14%). Back-compat mirrors
(`focal_point`, `text_overlay`, `color_scheme`, `expected_ctr_pct`) stay in
sync with the canonical fields.

## Render Package contract (`render_package`)

Versioned via `render_package_version` (currently `"1.0"`). The Render
Engine executes it clip by clip without re-deriving any creative decision:

- `title`, `style`, `aspect_ratio`, `total_duration_sec`, `clip_count`, `music_style`
- `clips[]` — contiguous timeline; each clip: `clip_number`, `start_sec` /
  `end_sec` / `duration_sec`, `asset_request` (source adapter payload),
  `shot_type`, `camera_motion`, `zoom`, `transition_in` / `transition_out`,
  `overlay` {text, treatment}, `caption` {text, placement, timing},
  `sfx` {at_sec, cue}, `predicted_retention`
- `thumbnail_brief` — the winning thumbnail concept
- `retention_curve` — per-clip predicted retention

## Extension points (never touch the engine)

| To add… | Do this |
|---|---|
| A visual style | `services/visual/styles.py::register_style(key, preset)` |
| An asset source/provider | `services/visual/sources.py::register_source(adapter)` (subclass `AssetSourceAdapter`) |
| An AI image/video model | One formatter in `services/visual/prompts.py` |
| A shot type | One entry in `services/visual/shots.py::SHOT_TYPES` (+ purpose sequence) |

## Guarantees

- **Deterministic** — same input, same package; fully testable without API keys (Demo Mode carries the whole Director).
- **JSON-safe** — every value survives the workflow context and Streamlit session state.
- **Additive evolution** — downstream consumers (`services/audio/package.py`, `ui/components.py`) rely on existing keys; new capabilities add keys.

Tests: `tests/test_visual_intelligence.py` (unit + pipeline integration).
