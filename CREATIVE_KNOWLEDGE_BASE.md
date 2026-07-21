# Creative Knowledge Base

Audience Intelligence maintains a **growing, evidence-backed** creative memory used to brief future productions.

## Stores

| Store | Path | Owner |
|-------|------|-------|
| Audience Intelligence memory | `data/audience_intelligence/CREATIVE_MEMORY.json` | Audience Intelligence |
| Production lessons mirror | `data/audience_intelligence/PRODUCTION_LESSONS.json` | Audience Intelligence |
| Creative Performance Lab | `data/creative_performance_lab/creative_performance_knowledge.json` | CPL (experiments) |
| Publishing creative library | `data/analytics/creative_knowledge_library.json` | Publishing Intelligence |

Audience Intelligence **composes** CPL / Publishing signals when useful. It does **not** fork or overwrite those libraries.

## Lesson schema

```json
{
  "lesson_id": "ail_...",
  "statement": "Three-beat openings consistently improve curiosity.",
  "category": "hook_patterns",
  "confidence": 0.62,
  "evidence": [{"type": "post_production_review", "...": "..."}],
  "platform": "youtube_shorts",
  "niche": "biology",
  "topic": "...",
  "production_id": "...",
  "source": "post_production_review|bootstrap_seed",
  "tags": [],
  "active": true
}
```

Confidence rises when the same lesson is corroborated by later reviews.

## Categories

`hook_patterns` · `curiosity_gaps` · `emotional_triggers` · `visual_pacing` · `camera_movement_styles` · `narration_styles` · `thumbnail_characteristics` · `caption_styles` · `scene_density` · `transition_styles` · `subject_best_practices` · `platform_recommendations`

## Rules

- Every recommendation must carry **evidence** and **confidence**.
- Do not invent live platform metrics — use analytics interfaces when connected.
- Briefs and lessons **guide** Scene / World / Cinematic / Voice / Publishing; they do not replace them.
- CPL still owns experiment promotion gates; AI owns production-review lessons.

## CLI

```bash
python scripts/audience_intelligence.py search "professor voice science"
python scripts/audience_intelligence.py lessons
python scripts/creative_performance_lab.py learnings --platform youtube_shorts
```

See also: `PRODUCTION_LESSONS.md`, `AUDIENCE_INTELLIGENCE.md`.
