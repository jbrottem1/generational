# Generational asset synchronization findings (local certification support)

## Question
Where are DOCTOR_001 / character / environment Blender assets?

## Findings on branch `migration/windows-workstation`

| Asset type | Present in Git? | Notes |
|---|---|---|
| `*.blend` | **NO** | Zero `.blend` files on this branch (and none found on `main`) |
| `*.fbx` / `*.glb` / `*.gltf` | **NO** | Absent from Git tree |
| DOCTOR_001 metadata | **YES** | JSON/docs under `data/human_realism/characters/DOCTOR_001`, `data/character_rig_studio/actors/DOCTOR_001`, `data/studio_assets/DOCTOR_001`, etc. |
| Character/environment code + docs | **YES** | Markdown/JSON studio packages |
| Git LFS pointers for blends | **NO** | No `.gitattributes` LFS rules; `git lfs ls-files` empty |

## Interpretation

Missing production `.blend` files are **not** caused by failed LFS checkout.
They are **absent from the Git repository**.

Likely locations / next sync options:
1. External asset store / laptop-only folder not yet committed
2. Another unpublished drive/share
3. Assets still to be authored from the JSON character packages into Blender

## Recommendation

1. Locate the source of truth for DOCTOR_001 `.blend` on your workstation or studio share
2. Approve Git LFS (see `RECOMMENDED_gitattributes.txt`) before adding large binaries
3. Place blends under a clear repo path, for example:
   - `data/studio_assets/DOCTOR_001/BLENDER/`
   - `assets/characters/DOCTOR_001/`
4. Re-run `INSTALL_AND_CERTIFY.bat`

Do not fabricate `.blend` files in certification.
