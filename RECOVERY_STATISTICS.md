# RECOVERY STATISTICS

Generated: `2026-07-14T12:45:03.547754+00:00`

- Productions: 10
- Recovery flags observed: 0
- Ended with MP4 (recovery or first-pass): 10
- Avg retries/production: 0.0

## Mechanism

1. Provider image/video failure → cinematic fallback still (asset resolver)
2. Assembly `No resolved visual assets` → renderer regenerates stills + one assemble retry
3. Ops engines: per-engine retries from stage `max_retries`
4. Animation engine remains soft-skipped (`not ready`) without aborting production
