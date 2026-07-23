# Generational — Local Windows Workstation Certification

**Run this on your Windows PC only.**  
Do **not** run it inside the Cursor cloud VM.

## One command

From File Explorer: double-click `CERTIFY.bat`

Or from CMD / PowerShell (in this folder):

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
| Windows | OS version, build, architecture |
| CPU / RAM | Model, cores, total memory |
| GPU | NVIDIA model, VRAM, driver |
| Accelerators | CUDA, OptiX, Vulkan, OpenGL |
| Blender | Install path, version, `-b` render, `bpy`, Cycles, Eevee, GPU devices |
| Python | Version, Generational venv, pip packages |
| Git | Version, remote, auth, LFS, push/pull dry checks |
| Generational | Repo layout, production folders, Blender/character/environment assets, output dirs |

## Output

Creates in this folder:

- `WORKSTATION_CERTIFICATION_REPORT.md` — full report with **PASS** or **FAIL**
- `certification_artifacts\` — probe logs, sample Blender render if Blender is present

Exit codes:

- `0` = **PASS** (certified)
- `1` = **FAIL** (fixes listed in the report)

## Optional arguments

```powershell
.\certify_workstation.ps1 -RepoRoot "C:\AI\Projects\Generational"
.\certify_workstation.ps1 -BlenderExe "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
.\certify_workstation.ps1 -SkipNetwork
```

## After a FAIL

Install the fixes listed at the bottom of the report, then re-run `CERTIFY.bat` until it prints:

```text
✅ WORKSTATION CERTIFIED FOR GENERATIONAL PRODUCTION
```
