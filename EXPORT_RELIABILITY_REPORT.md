# EXPORT RELIABILITY REPORT

Mission: Permanent local export reliability — prevent false failures and missing videos.

Date: 2026-07-12  
Production under analysis: Origin of Turtles (`turtle_202`)

---

## Root cause of the false failure

### Primary bug (manifest / publishing status)

`export_verified_production` built a verification checklist with:

- `manifest_updated = False`
- `library_index_updated = False`

…then called `update_manifest_from_export()` **before** flipping those flags.  
`verification.ok` was therefore `false`, and the manifest permanently stored:

- `publishing_status: "qc_failed"`
- `local_render_status: "failed"` (later inconsistent with index)

even though every media check had already passed:

| Check | Origin of Turtles |
|-------|-------------------|
| file_exists | true |
| size_gt_zero | true (~1.54 MB) |
| video_stream | true (h264 1080×1920) |
| audio_stream | true (aac) |
| duration | true (24.5s) |
| companion_files | true |

The corrected `verification.ok = true` computed after bookkeeping was **never re-saved**.

**Actual MP4 (source of truth):**  
`/Users/jaredbrottem/Desktop/AI Start-Up/Videos/Biology/Biology_001_202_Origin_of_Turtles.mp4`  
(~1.54 MB, 24.5s, H.264 + AAC, bitrate ~502 kbps)

### Secondary false negatives

1. **`export_too_small`** — Quality gate used a flat 50 KB threshold and defaulted `export_bytes` to `0` when omitted. Foundation gate often ran **before** export (no path/bytes), or with a path but no size → hard fail despite a playable MP4.

2. **`animation_qc_missing`** — Treated as a hard fail when the `qc` block was absent, even if the final video verified. `run_local_render_job.py` also omitted `qc` when calling the foundation gate.

3. **`technical_validity_below_threshold` / soft scores** — Soft dimension misses could block overall `passed` even when the MP4 was technically fine.

4. **`export_path: null` risk** — Premature failure paths and stale cloud paths (`/home/ubuntu/...`) could leave reporting systems disagreeing with Finder.

5. **Ordering** — Final QC ran against pre-export production packages instead of the destination file.

---

## Fixes implemented

### Atomic export workflow (`services/generational_os/export.py`)

1. Verify temporary source  
2. Copy to canonical destination (with retry)  
3. Wait until destination exists and size is stable  
4. Verify destination with ffprobe + technical validity  
5. Write companions  
6. Update library index  
7. Persist manifest **with bookkeeping flags already true**  
8. Assign final status  
9. Print completion block with absolute path  

### Final status taxonomy (`services/generational_os/final_status.py`)

- `SUCCESS`
- `SUCCESS_WITH_WARNINGS`
- `FAILED`

See `FINAL_STATUS_SPEC.md`.

### Technical validity (`services/media_production/verified_export.py`)

- Context-aware size/bitrate (no universal 50 KB hard fail)
- Hard fail only on truncated/corrupt/missing-stream/implausible-bitrate/duration mismatch/stale cloud path
- `wait_for_file` for copy completion

### Quality scoring (`services/quality/content_score.py`)

- Resolve bytes from path/probe when omitted
- Demote raw `export_too_small` when file verifies
- Missing animation QC → soft warning when MP4 verifies

### Foundation gate (`services/animation/foundation_gate.py`)

- Attempt QC regeneration from destination MP4
- Missing QC metadata → warning when export verifies; hard fail only without a usable MP4
- Emits `final_status`

### Runners

- `scripts/foundation_v2_turtles.py` — export first, then gate against destination
- `scripts/run_local_render_job.py` — pass `qc` + `export_bytes` + post-export gate + completion block
- `scripts/benchmark_export_reliability_turtles.py` — local re-verify without full re-render

### Manifest (`services/generational_os/manifest.py`)

- `final_status` field
- Absolute `export_path`
- Explicit publishing / local-render status from final assignment

---

## Files changed

| File | Change |
|------|--------|
| `services/generational_os/export.py` | Atomic export + final status + completion |
| `services/generational_os/final_status.py` | **New** status assignment + completion formatter |
| `services/generational_os/manifest.py` | `final_status`; persist absolute path + explicit statuses |
| `services/media_production/verified_export.py` | Technical validity, bitrate/fps probe, wait_for_file |
| `services/quality/content_score.py` | Contextual size; soft warnings; verified-export pass logic |
| `services/quality/__init__.py` | Export `soft_warning_reasons` |
| `services/animation/foundation_gate.py` | QC recovery; warning demotion; final_status |
| `scripts/foundation_v2_turtles.py` | Post-export gate + completion |
| `scripts/run_local_render_job.py` | Post-export gate + qc/bytes + completion |
| `scripts/benchmark_export_reliability_turtles.py` | **New** turtles reliability benchmark |
| `tests/test_export_reliability.py` | **New** regression suite |
| `tests/test_foundation_gate.py` | Real temp MP4 fixtures |
| `FINAL_STATUS_SPEC.md` | **New** status contract |
| `EXPORT_RELIABILITY_REPORT.md` | **New** this report |

---

## Status logic changes

| Before | After |
|--------|--------|
| Manifest saved with `ok=false` because bookkeeping flags were still false | Manifest saved only after library + bookkeeping are true |
| `export_too_small` hard-fail at 50 KB / missing bytes | Technical validity; legacy size demoted to warning |
| `animation_qc_missing` hard-fail | Regenerate or warn when MP4 verifies |
| Gate often pre-export | Gate runs against destination path + bytes |
| Binary ok / failed | `SUCCESS` / `SUCCESS_WITH_WARNINGS` / `FAILED` |

---

## Tests added

`tests/test_export_reliability.py` covers:

- Valid small short-form MP4
- Missing animation-QC metadata but valid video
- Temp exists / final missing → FAILED
- Final exists / manifest path null → SUCCESS_WITH_WARNINGS recovery
- Zero-byte MP4
- Missing audio / missing video
- Duration mismatch
- Stale cloud path
- Local Desktop SUCCESS
- Duplicate filename versioning
- Warning-only QC → SUCCESS_WITH_WARNINGS
- True hard failure (`animation_qc_failed`)
- Export persists `manifest_updated` / `library_index_updated` / `ready_for_review`

Related suites updated/green: `tests/test_foundation_gate.py`, `tests/test_quality_education.py`  
**26 passed** in the reliability-focused run.

---

## Benchmark result (Origin of Turtles)

Command:

```bash
GENERATIONAL_EXECUTION_MODE=local python3 scripts/benchmark_export_reliability_turtles.py
```

Result:

```
STATUS: SUCCESS_WITH_WARNINGS
FINAL FILE:
 /Users/jaredbrottem/Desktop/AI Start-Up/Videos/Biology/Biology_001_202_Origin_of_Turtles.mp4
FILE SIZE: 1.5 MB
DURATION: 24.5 seconds
VIDEO: H264, 1080x1920
AUDIO: AAC
WARNINGS:
 - whiteboard_sync_metadata_missing
 - overall_below_target:77.3<78.0
```

- `ok: true`
- `hard_fails: []`
- Valid local MP4 recognized as successfully exported
- Soft warnings listed without false FAILED

Artifact: `data/productions/_validation/export_reliability/TURTLE_202_BENCHMARK.json`

---

## Remaining risks

1. **Case / spelling of library root** — code uses `AI Start-Up`; Finder may show `AI Start-UP`. macOS case-insensitive volumes resolve both; case-sensitive volumes would need a single locked spelling.
2. **Recovered technical-only QC** — regenerates a stub from ffprobe; gesture/lipsync floors are not invented as hard fails, but full performer QC still requires a real render-time report for strict Foundation shipping.
3. **Reality QC** — still a caller-provided hard fail when it fails; not demoted by export verification (intentional content gate).
4. **Dedup path** — duplicate hash reuse returns early; ensure callers still print completion (handled when `print_completion=True`).
5. **Historical manifests** — older `qc_failed` records remain until re-exported/benchmarked; turtles was repaired by the benchmark.

---

## Success condition checklist

| Criterion | Status |
|-----------|--------|
| Valid local MP4 recognized as exported | Pass (benchmark) |
| False-negative export failures eliminated | Pass (root cause + tests) |
| Real failures remain blocked | Pass (zero-byte, missing A/V, etc.) |
| Missing metadata → repair/warning | Pass |
| Absolute local path always recorded | Pass |
| Library / manifest / QC / terminal agree | Pass on benchmark |
| Clear SUCCESS / SUCCESS_WITH_WARNINGS / FAILED | Pass |
