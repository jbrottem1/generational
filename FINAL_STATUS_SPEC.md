# FINAL STATUS SPEC

Canonical final statuses for every local Generational production.

The physical local MP4 under `~/Desktop/AI Start-Up/Videos/` is the source of truth for export completion.

---

## Statuses

### SUCCESS

Use when:

- Final MP4 exists at an absolute local library path
- Video and audio streams are valid (ffprobe)
- Duration and resolution are valid
- Required QC passes (or was regenerable without inventing false failures)
- No hard blockers remain

Mapped publishing status: `ready_for_review`  
Mapped local render status: `verified`

### SUCCESS_WITH_WARNINGS

Use when:

- Final MP4 exists and is playable
- Export technical verification passes
- One or more non-critical QC reports are missing, regenerated from the file, or below stretch targets
- The user can still open and review the video

Mapped publishing status: `ready_for_review`  
Mapped local render status: `verified`

Warnings must be listed in the completion block. Never hide a successful export behind a failure banner.

### FAILED

Use only when:

- No usable MP4 exists
- The MP4 is corrupt / truncated / zero-byte
- Video stream is missing
- Required audio is missing
- Duration is invalid
- Render/export is incomplete
- Export path is inaccessible
- Final destination was not created
- A true hard-fail quality condition exists (broken animation QC, foundation lipsync/animation floors when metrics exist, placeholders, etc.)

Mapped publishing status: `qc_failed`  
Mapped local render status: `failed`

---

## Hard-fail conditions

These force `FAILED` (unless demoted by the warning table below):

| Condition | Meaning |
|-----------|---------|
| `missing_export_path` | No export path recorded and no file to inspect |
| `export_missing` / `destination_not_created` | Final destination file absent |
| `export_zero_bytes` / `export_truncated` | Empty or near-empty file |
| `missing_video` | No video stream |
| `missing_audio` | No audio stream when audio is required |
| `invalid_duration` | Duration ≤ 0.5s |
| `invalid_resolution` | Missing width/height |
| `implausible_bitrate` | Average bitrate &lt; 40 kbps (truncated/incomplete evidence) |
| `duration_mismatch` | Probe duration far from expected render duration |
| `incomplete_ffmpeg_output` | Incomplete container evidence |
| `stale_cloud_path` | Path points at cloud agent filesystem |
| `export_path_inaccessible` | Cannot read destination |
| `placeholder_assets_remain` | Placeholder assets still present |
| `export_verification_failed` | Technical verification failed and file not recoverable |
| `animation_qc_failed` | Performer QC explicitly `passed: false` |
| `lipsync_below_foundation_floor` | Foundation lipsync floor breached when real QC metrics exist |
| `animation_below_foundation_floor` | Foundation animation floor breached when real QC metrics exist |
| Gesture/mouth hard fails | `wave_gesture_forbidden`, idle/walk out of range, mouth not varying, etc. |
| `missing_animation_qc` | Only when **no** verified MP4 exists |
| `reality_qc_failed` | Reality image QC hard-failed (caller-provided) |

---

## Warning conditions

These must **not** alone mark a verified MP4 as `FAILED`:

| Condition | Meaning |
|-----------|---------|
| `animation_qc_missing` | Animation QC report absent; MP4 still verifies |
| `qc_report_regenerated` / `qc_report_missing_recovered` | QC rebuilt from destination file |
| `whiteboard_sync_metadata_missing` | Soft whiteboard timing metadata absent |
| `equation_*` whiteboard soft checks | Equation timing soft warnings |
| `export_too_small` / `export_size_below_legacy_threshold` | Legacy raw-size gate demoted; use technical validity instead |
| `*_below_threshold` | Soft dimension score below target (non-foundation floors) |
| `technical_validity_below_threshold` | Soft technical score miss when file still verifies |
| `overall_below_target` | Overall below stretch target (e.g. 78) |
| `manifest_path_null_recovered` | Manifest path repaired from verified file |
| `companion_files_incomplete` | Optional companions incomplete |
| `small_file_size_context_ok` | Small but bitrate-sane short-form file |

---

## Assignment algorithm

1. Inspect the **destination** MP4 (never the temp render alone for final status).
2. Run technical validity (`assess_export_technical_validity`).
3. Collect QC hard fails and warnings.
4. Demote warning-only reasons even if a caller listed them under hard fails.
5. Assign:
   - `FAILED` if export not verified, file missing, or true hard fails remain
   - `SUCCESS_WITH_WARNINGS` if verified and warnings remain
   - `SUCCESS` if verified and no warnings

---

## Path consistency

One absolute path must agree across:

- render job
- export module
- production manifest (`export_path`)
- QC / foundation gate
- media library index
- production report
- dashboard
- terminal completion block

No subsystem may independently guess a different path for final status.

---

## Completion block

Every run prints:

```
STATUS: SUCCESS | SUCCESS_WITH_WARNINGS | FAILED

FINAL FILE:
 <absolute path>

FILE SIZE:
 …

DURATION:
 …

VIDEO:
 …

AUDIO:
 …

QC:
 Passed | Passed with warnings | Failed

FINDER:
 Available locally | Not available
```

When warnings exist, list each under `WARNINGS:` without hiding the successful export.
