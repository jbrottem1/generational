# Experimentation Guide

## Controlled experiment checklist

1. Choose **one** primary variable (`hook_structure`, `narration_voice`, `thumbnail`, …).
2. Hold constant: facts, runtime, platform, narrator (unless testing voice), music, captions, CTA, export.
3. Write a falsifiable hypothesis and success metric (e.g. completion_rate_pct).
4. Generate 3 variants with `scripts/creative_performance_lab.py run`.
5. Complete human review before publishing anything.
6. Publish manually if desired; attach each platform video ID.
7. Wait for the minimum observation window; refresh analytics; evaluate.
8. Promote a learning only when status is PROVISIONAL/CONFIRMED.

## Status meanings

| Status | Meaning |
| --- | --- |
| INSUFFICIENT_DATA | Too few views / no analytics |
| EARLY_SIGNAL | Directional only |
| PROVISIONAL_WINNER | Enough for a cautious call |
| CONFIRMED_WINNER | Stronger sample |
| INCONCLUSIVE | Conflicting / weak |

## Variables you can test

See `CONTROLLED_VARIABLES` in `services/creative_performance_lab/models.py`.

Mark `exploratory=True` only when intentionally changing multiple axes.
