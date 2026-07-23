# Creative Excellence System

Software is frozen. Viewer attention is the product.

This layer does **not** redesign engines. It judges finished productions the way elite educational Shorts teams do.

**V2 Creative Quality Initiative:** see [`V2_CREATIVE_QUALITY.md`](V2_CREATIVE_QUALITY.md) for documentary craft scores (visual / motion / storytelling / clarity / hook / retention / audio / polish) and existing-system levers.

## What it measures

| Timeline | Craft |
|----------|--------|
| First 3 seconds | Viewer emotion |
| First 6 seconds | Curiosity |
| First 15 seconds | Payoff |
| Middle pacing | Visual movement |
| Ending | Narration energy |

## Viewer outcomes (not code)

- Would someone stop scrolling?
- Would someone finish watching?
- Would someone share it?
- Would someone subscribe?

## Creative Excellence Score (≠ engineering)

- Engineering Quality *(contrast only)*
- Creative Quality
- Viewer Retention
- Educational Value
- Entertainment
- Shareability
- Emotional Impact
- Curiosity

**Creative Excellence overall ignores engineering** on purpose. A perfect export that nobody watches fails this score.

## Rule: exactly ONE recommendation

Every review returns a single highest-impact creative change ranked by **expected retention gain**.  
Never ship a laundry list.

## Commands

```bash
# Review the gold-standard flagship
python scripts/run_creative_excellence_review.py --gold-standard

# Review any PRODUCTION_REPORT.json
python scripts/run_creative_excellence_review.py --report data/productions/_ops/<id>/PRODUCTION_REPORT.json
```

## API

```python
from services.creative_excellence import review_production_creative_excellence

result = review_production_creative_excellence(
    candidate,
    production_report=report,
    production_id="…",
)
print(result["scorecard"]["creative_excellence_score"])
print(result["single_recommendation"])
```

Wired automatically at the end of `run_studio_ops` (soft fail if unavailable).

## Artifacts

- Per review: `data/productions/_validation/creative_excellence/<id>/`
- History: `data/analytics/creative_excellence_history.json`
- Ops copy: `data/productions/_ops/<id>/CREATIVE_EXCELLENCE.md`

## Mission success

Every new production should raise Creative Excellence vs the previous entry in history. If it does not, apply only the single recommendation before scaling volume.
