# Release Candidate 1 Report

**Generated:** 2026-07-10T16:06:14.489437+00:00
**Declaration:** Release Candidate 1 Ready
**Success rate:** 100.0% (5/5)
**Production readiness:** 92%

## Aggregate metrics

| Metric | Value |
|---|---|
| Batch runtime | 106.35s |
| Average runtime | 21.27s |
| Average estimated cost | $0.0177 |
| Total estimated cost | $0.0885 |
| Average QC score | 100.0 |
| Total retries | 0 |
| Recovery events | 0 |

## Per-run results

| # | Topic | OK | Runtime (s) | Cost ($) | Retries | QC | MP4 bytes | Failed |
|---|---|---|---|---|---|---|---|---|
| 1 | Secrets of Bioluminescence | True | 29.74 | 0.019 | 0 | 100 | 473940 | — |
| 2 | Black Holes Explained | True | 17.94 | 0.0173 | 0 | 100 | 378556 | — |
| 3 | Why Octopuses Are So Intelligent | True | 17.3 | 0.0171 | 0 | 100 | 373185 | — |
| 4 | The History of Rome in 60 Seconds | True | 22.76 | 0.018 | 0 | 100 | 421886 | — |
| 5 | How Trees Communicate Underground | True | 18.6 | 0.0171 | 0 | 100 | 372720 | — |

## Common failures

- None

## Remaining integrations

- ElevenLabs (music/SFX)
- Runway/Fal (video clips)
- YouTube OAuth (live publish)

## Remaining blockers

- ElevenLabs (music/SFX)
- Runway/Fal (video clips)
- YouTube OAuth (live publish)
- Thumbnails missing on 5/5 runs (image gen optional for RC1 core path)
- OpenAI Images returns `dall-e-3 does not exist` on this account — stage completes with placeholders; render falls back to color-bed + narration (non-blocking for RC1 core path)

## Warnings (non-blocking)

- Image generation failed on all 5 runs (invalid image model for key); pipeline continued and still exported playable MP4s
- Music / SFX / video clips / publish skipped due to missing credentials (expected)

## Recommendation

Freeze feature work. Proceed to RC1 packaging / staging publish dry-run with OAuth.
Do not expand architecture. Optional post-RC1 ops: fix image model id for this OpenAI account, then add music/OAuth credentials.
