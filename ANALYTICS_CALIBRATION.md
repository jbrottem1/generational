# Analytics Calibration

Compares **internal predictions** to **real platform metrics**.

## Sources

- YouTube: existing `providers/analytics/youtube.py` (requires credentials).
- TikTok / Instagram: stub interfaces only (`services/creative_performance_lab/analytics_providers.py`).

Never invent or scrape analytics.

## Calibration flow

```bash
python scripts/creative_performance_lab.py attach EXP_ID --variant A --video-id ...
python scripts/creative_performance_lab.py analytics EXP_ID
python scripts/creative_performance_lab.py evaluate EXP_ID
```

Metrics compared when present:

- Predicted hook strength vs early retention (when available)
- Predicted completion vs actual completion / % viewed
- Predicted CTR vs actual CTR
- Predicted shareability vs share rate
- Predicted / human winner vs actual winner

Errors recorded as absolute + percent error. Ranking accuracy is tracked separately.

Publishing Intelligence calibration (`services/publishing_intelligence/calibration.py`) remains the channel-level prior system; CPL evaluates per-experiment lift.
