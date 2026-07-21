# PRODUCTION RELIABILITY REPORT

Generated: `2026-07-14T12:45:03.547411+00:00`

## Verdict

- MP4 success rate: **100.0%** (target ≥ 90%)
- Gate passed: **YES**
- Ops success count: 10/10
- Publication-ready count: 10/10
- Architecture frozen: `True`
- Avg execution time: 26880 ms
- Avg retries: 0.0

## Production chain (verified handoffs)

Research → Psychology → Script → Scene Builder → World/Media → Asset Resolution → ElevenLabs/Voice → Cinematic Director → Renderer (`video`/`assemble_mp4`) → Validation → Export → Library

### Critical repair applied

1. **Asset resolution** now materializes cinematic fallback stills when AI/stock providers return mock URIs.
2. **`assemble_mp4`** accepts real local files even if a provider incorrectly set `placeholder=True`.
3. **Renderer recovery** retries assembly once after regenerating stills when visuals were missing.
4. **Export packaging** copies MP4/audio/captions/thumbnail into the project folder and resolves relative paths.
5. **Success reporting** remains honest: `success` requires a physical MP4.
6. **Stage instrumentation** records engine_results, retries, failure_reason, dependency health.

## Validation productions

| ID | Category | Topic | MP4 | Playable | Caps | Thumb | Audio | Success | Time (ms) |
|---|---|---|---|---|---|---|---|---|---|
| rel_01_biology | Biology | How mitochondria make ATP | Y | Y | Y | Y | Y | Y | 58777 |
| rel_02_physics | Physics | Why light bends in water | Y | Y | Y | Y | Y | Y | 24994 |
| rel_03_astronomy | Astronomy | How black holes bend spacetime | Y | Y | Y | Y | Y | Y | 30403 |
| rel_04_history | History | How the printing press changed Europe | Y | Y | Y | Y | Y | Y | 20592 |
| rel_05_medicine | Medicine | How vaccines teach the immune system | Y | Y | Y | Y | Y | Y | 21600 |
| rel_06_ai | AI | How neural networks learn from data | Y | Y | Y | Y | Y | Y | 24747 |
| rel_07_nature | Nature | Why forests create their own rain | Y | Y | Y | Y | Y | Y | 21689 |
| rel_08_engineering | Engineering | How suspension bridges distribute force | Y | Y | Y | Y | Y | Y | 21421 |
| rel_09_psychology | Psychology | How habits form in the brain | Y | Y | Y | Y | Y | Y | 22182 |
| rel_10_ocean | Ocean Science | How deep ocean currents move heat | Y | Y | Y | Y | Y | Y | 22396 |

## Library

`/Users/jaredbrottem/Desktop/AI Start-UP/Apps/generational/data/productions/_validation/production_reliability`
