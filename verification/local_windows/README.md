# Generational - Local Windows Workstation Certification

**Run this on your Windows PC only.**  
Do **not** run it inside a Cursor cloud VM.

## Recommended one command (install Blender if needed + certify)

```bat
git pull origin migration/windows-workstation
cd verification\local_windows
INSTALL_AND_CERTIFY.bat
```

This will:
1. Detect existing Blender installs
2. Install official `BlenderFoundation.Blender` via winget if missing
3. Add Blender to the user PATH when needed
4. Run real Blender scene render probes (mesh + camera + light + PNG + short anim)
5. Write `WORKSTATION_CERTIFICATION_REPORT.md`

## Certification only (Blender already installed)

```bat
CERTIFY.bat
```

Or:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\certify_workstation.ps1
```

## What it checks

| Domain | Checks |
|---|---|
| Windows | OS, CPU, RAM |
| GPU | WMI + `nvidia-smi` (supported fields only) |
| Blender | exe path, version, background, `bpy`, Eevee, Cycles, FFmpeg, devices |
| Render | Real one-frame PNG + short Blender animation under `certification_artifacts\` |
| Python / Git / LFS / FFmpeg | Presence and basic health |
| Generational assets | `.blend` inventory + DOCTOR_001 metadata; sync diagnosis if missing |

## Probe scripts

- `probe_bpy.py` - background/`bpy`/engine/device JSON probe
- `probe_scene_render.py` - real scene render probe (not FFmpeg-only graphics)
- `probe_render.py` - legacy helper retained for compatibility

## Output

- `WORKSTATION_CERTIFICATION_REPORT.md`
- `certification_artifacts\` (PNG, MP4 or PNG sequence, probe JSON, logs)

Exit codes:
- `0` = certified
- `2` = certification failed (blockers listed in report)

## Asset sync note

Production `.blend` files are currently **absent from Git** (not an LFS checkout failure).  
See `ASSET_SYNC_FINDINGS.md` and `RECOMMENDED_gitattributes.txt` (proposal only; not applied).
