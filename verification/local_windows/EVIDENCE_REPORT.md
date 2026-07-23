# Evidence Report — Workstation Certification Package Audit

**Date (UTC):** 2026-07-23  
**Auditor host:** Cursor agent (history/branch inspection only)  
**User branch under investigation:** `migration/windows-workstation`  
**Scope:** Audit + repair of `verification/local_windows` only. No production architecture changes.

---

## Questions answered

### 1. Was `verification/local_windows` ever committed?

**YES.**

It was committed and pushed to GitHub on branch:

`cursor/motivational-media-studio-92dd`

---

### 2. If yes — which commit, which branch, why missing here?

| Item | Value |
|---|---|
| **Initial commit** | `5d66f52a67ca8a65f8f0d08f07ba9dd134d5ebf9` — *Add local Windows workstation certification package* |
| **Follow-up** | `eeb6f06d` — *Add CERTIFY.ps1 launcher for local Windows certification* |
| **Latest package tip** | `53020887` — *Harden local Blender probe for Cycles/OptiX device detection* |
| **Branch containing package** | `origin/cursor/motivational-media-studio-92dd` (only) |
| **Present on `main`?** | **NO** |
| **Present on `migration/windows-workstation` (before repair)?** | **NO** |

**Why `Get-ChildItem -Recurse -Filter certify_workstation.ps1` returned nothing on your PC:**

1. Your local checkout is on **`migration/windows-workstation`**.
2. `git pull` correctly reported **Already up to date** for *that* branch tip (`9100e342`).
3. The certification package lives on a **different feature branch** (`cursor/motivational-media-studio-92dd`) that was **never merged** into `migration/windows-workstation` or `main`.
4. Merge-base of the two branches is still `7db0b3ad` (`main` tip at divergence). Commit `5d66f52a` is **not an ancestor** of `migration/windows-workstation`.

So GitHub auth and pull were fine; the files were simply **not on the branch you pulled**.

---

### 3. If no — why did a previous Cursor session reference them?

N/A for “never committed” — they **were** committed.  
The previous session referenced them because it created and pushed them on `cursor/motivational-media-studio-92dd` / PR context, not onto `migration/windows-workstation`.

---

### 4. Repository search results

| Path / name | Working tree on `cursor/motivational-media-studio-92dd` | `origin/migration/windows-workstation` (pre-repair) | `origin/main` | Git history |
|---|---|---|---|---|
| `verification/local_windows/certify_workstation.ps1` | Present | Absent | Absent | Introduced in `5d66f52a` |
| `verification/local_windows/CERTIFY.bat` | Present | Absent | Absent | Introduced in `5d66f52a` |
| `verification/local_windows/CERTIFY.ps1` | Present | Absent | Absent | Introduced in `eeb6f06d` |
| `verification/local_windows/README.md` | Present | Absent | Absent | Introduced in `5d66f52a` |
| `WORKSTATION_CERTIFICATION_REPORT.md` | Not in repo (generated locally by the script) | Absent | Absent | Never committed (runtime output) |

**Branches containing `5d66f52a`:**

- `cursor/motivational-media-studio-92dd`
- `remotes/origin/cursor/motivational-media-studio-92dd`

---

### 5. Evidence commands (reproducible)

```bash
git fetch origin --prune
git log --all --oneline -- verification/local_windows
git branch -a --contains 5d66f52a
git ls-tree -r --name-only origin/cursor/motivational-media-studio-92dd | grep local_windows
git ls-tree -r --name-only origin/migration/windows-workstation | grep local_windows
git merge-base --is-ancestor 5d66f52a origin/migration/windows-workstation; echo $?
# expect: 1 (not ancestor)
```

Blob hash of `certify_workstation.ps1` at package tip:

`3e4767ba0329f84bb0281bbb4a78ea4c4a33420d`

---

## Repair performed (this session)

Ported **only** `verification/local_windows/*` from  
`origin/cursor/motivational-media-studio-92dd` → `migration/windows-workstation`  
and committed/pushed so a Windows machine on `migration/windows-workstation` can:

```bat
git pull
dir verification\local_windows\certify_workstation.ps1
cd verification\local_windows
CERTIFY.bat
```

No production engines, providers, or architecture were modified.

---

## Verdict

| Finding | Result |
|---|---|
| Package existed in Git? | **YES** |
| On user’s branch before repair? | **NO** |
| Root cause | Branch mismatch / never merged |
| User pull healthy? | **YES** (“Already up to date” was correct) |
| Repair | Package brought onto `migration/windows-workstation` |
