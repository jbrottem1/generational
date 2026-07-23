# Production Lessons

Human-readable log of Audience Intelligence creative memory.

Machine source of truth: `data/audience_intelligence/CREATIVE_MEMORY.json`  
JSON mirror: `data/audience_intelligence/PRODUCTION_LESSONS.json`

Regenerate / inspect:

```bash
python scripts/audience_intelligence.py seed
python scripts/audience_intelligence.py lessons
python scripts/audience_intelligence.py search "biology hooks"
```

## How lessons are created

1. **Bootstrap seeds** — starter patterns (moderate confidence) until corroborated.
2. **Post-production review** — after each completed ops run (or CLI `review`), exactly **one** highest-impact improvement is recorded from Creative Excellence + production reports.
3. **Future analytics** — when YouTube / TikTok / Instagram interfaces are connected, real retention / CTR / AVD evidence can raise confidence.

## Example lesson forms

- Fast zooms improve biology hooks.
- Ocean environments outperform static blue backgrounds.
- Three-beat openings consistently improve curiosity.
- Professor voice performs best for educational science.

Each stored row includes supporting evidence and a confidence score.

## Brief → produce → learn loop

```
Creative Brief  →  existing production systems  →  Creative Excellence
                                              →  AI post-review (one lesson)
                                              →  smarter next Brief
```

No new production engines. No renderer changes. No pipeline redesign.

See: `AUDIENCE_INTELLIGENCE.md`, `CREATIVE_KNOWLEDGE_BASE.md`.
