# Generational — Windows AI Workstation Setup

This document prepares and records the **primary Windows development workstation** for the Generational AI Content Operating System.

Repository: [https://github.com/jbrottem1/generational](https://github.com/jbrottem1/generational)

Canonical project path on Windows:

```text
C:\AI\Projects\Generational
```

Bootstrap script (run in PowerShell on the Windows PC):

```text
scripts\windows\Initialize-AIWorkstation.ps1
```

---

## Environment note (cloud vs local)

If you are reading this from a Cursor Cloud Agent session, that agent runs on **Linux** and cannot create `C:\AI` or inspect Windows-installed apps. Use the PowerShell script on the Windows machine for Phases 1–4 and 6–8. Phase 5 (project validation) below reflects the repository as inspected in this workspace.

---

## Phase 1 — Directory structure

### Layout

```text
C:\AI
├── Assets          # Shared media / brand assets outside any single repo
├── Exports         # Rendered or published outputs
├── Models          # Local model weights / caches (keep out of git)
├── Projects
│   └── Generational   # This repository (git clone)
├── Repositories    # Other git checkouts
├── Tools           # Portable CLIs, SDK drop-ins
├── Videos          # Source / reference video
├── Temp            # Scratch space (safe to clear)
├── Logs            # Machine-level logs (app logs still live under data/logs/)
├── Backups         # Manual or scripted backups
└── Scripts         # Host automation (copies of bootstrap scripts, etc.)
```

### Create (PowerShell)

Explain first: these commands only create missing directories; they do not delete or overwrite files.

```powershell
# From a clone (or download) of this repo:
cd <path-to-generational>
powershell -ExecutionPolicy Bypass -File .\scripts\windows\Initialize-AIWorkstation.ps1 -SkipClone
```

Or create the tree directly:

```powershell
$folders = @(
  'C:\AI',
  'C:\AI\Assets',
  'C:\AI\Exports',
  'C:\AI\Models',
  'C:\AI\Projects',
  'C:\AI\Projects\Generational',
  'C:\AI\Repositories',
  'C:\AI\Tools',
  'C:\AI\Videos',
  'C:\AI\Temp',
  'C:\AI\Logs',
  'C:\AI\Backups',
  'C:\AI\Scripts'
)
foreach ($path in $folders) {
  if (-not (Test-Path $path)) { New-Item -ItemType Directory -Path $path | Out-Null }
}
tree /A C:\AI
```

**Milestone check:** `tree /A C:\AI` shows the layout above.

---

## Phase 2 — Development tools

The bootstrap script **detects** tools and **never installs** them. Approve each missing install yourself.

| Tool | Required for Generational? | Why | Official download |
|---|---|---|---|
| **Git** | **Required** | Clone / pull / push between Mac and Windows | https://git-scm.com/download/win |
| **GitHub Desktop** | Recommended | Easy GitHub authentication on Windows | https://desktop.github.com/ |
| **Python 3.11+** (3.12 OK) | **Required** | App runtime (Streamlit, engines, pytest) | https://www.python.org/downloads/windows/ |
| **uv** | Optional | Fast, reliable Python env/package installs | https://docs.astral.sh/uv/getting-started/installation/ |
| **Node.js** + **npm** | Optional today | Not used by core Generational; handy for future JS tooling | https://nodejs.org/en/download |
| **Docker Desktop** | Optional | Containerized services / isolation later | https://www.docker.com/products/docker-desktop/ |
| **Visual Studio Build Tools** | Situational | Compiling native Python wheels on Windows | https://visualstudio.microsoft.com/visual-cpp-build-tools/ |
| **FFmpeg** | Recommended soon | Video/audio encode paths in the media pipeline | https://www.gyan.dev/ffmpeg/builds/ (or `winget install Gyan.FFmpeg` after approval) |
| **PowerShell 7** | Recommended | Modern shell for `C:\AI\Scripts` automation | https://learn.microsoft.com/powershell/scripting/install/installing-powershell-on-windows |

**Admin privileges:** installing to `Program Files`, enabling Hyper-V/WSL for Docker, or changing system PATH usually requires an elevated installer. Creating `C:\AI\...` as a normal user typically does **not**.

**Milestone check:** re-run the bootstrap script and confirm required tools show `FOUND`.

---

## Phase 3 — Git configuration

On the Windows PC:

```powershell
git --version
git config --global user.name
git config --global user.email
```

If name/email are empty, **do not guess**. Provide values, then either set them yourself:

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

or re-run the bootstrap script with explicit approval:

```powershell
.\scripts\windows\Initialize-AIWorkstation.ps1 -SkipClone `
  -SetGitIdentity -GitUserName "Your Name" -GitUserEmail "you@example.com"
```

Suggested identity for this workstation owner (confirm before use):

- Name: `Jared Brottem`
- Email: `jcbrottem@gmail.com`

Also recommended (optional, ask before applying):

```powershell
git config --global init.defaultBranch main
git config --global core.autocrlf true          # Windows
git config --global pull.rebase false           # merge-style pulls unless you prefer rebase
```

**Milestone check:** `git config --global --list` shows `user.name` and `user.email`.

---

## Phase 4 — GitHub connection and clone

1. Install/open **GitHub Desktop** → **File → Options → Accounts** → sign in to GitHub.
2. Confirm CLI auth works (HTTPS credential manager or SSH):

   ```powershell
   gh auth status   # if GitHub CLI is installed
   git ls-remote https://github.com/jbrottem1/generational.git
   ```

3. Clone with Git into the prepared folder (**never copy the project folder manually**):

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\windows\Initialize-AIWorkstation.ps1 -Clone
   ```

   Equivalent manual commands:

   ```powershell
   # Destination must be empty (except the folder itself)
   cd C:\AI\Projects\Generational
   git clone https://github.com/jbrottem1/generational.git .
   ```

**Milestone check:**

```powershell
cd C:\AI\Projects\Generational
git status -sb
git remote -v
```

---

## Phase 5 — Project validation (repository inspection)

### Languages

- **Python** (primary) — Streamlit UI, engines, services, providers, tests
- No Node/TypeScript application package in-repo today

### Package managers

- **pip** via `requirements.txt` / `requirements-dev.txt`
- Optional: **uv** (`uv venv` + `uv pip install -r requirements-dev.txt`)
- No `package.json`, no Poetry/Pipenv lockfile in-repo

### Python / Node versions

- Developed/tested in cloud on **Python 3.12**
- Target: **Python 3.11+** on Windows (3.12 preferred)
- Node/npm: **not required** for core app

### Requirements

Runtime (`requirements.txt`):

- `streamlit>=1.32`
- `openai>=1.3.0`
- `python-dotenv>=1.0.0`
- `plotly>=5.20`

Dev (`requirements-dev.txt`):

- runtime deps + `pytest>=7.4`

### Environment variables

From `.env.example`:

```env
OPENAI_API_KEY=
```

Copy to `.env` (gitignored). Without a key, the app runs in **Demo Mode**.

### Configuration files

| File | Role |
|---|---|
| `.env` / `.env.example` | API keys |
| `.streamlit/config.toml` | Dark theme / client toolbar |
| `.gitignore` | venv, `.env`, generated `data/` artifacts |
| `core/constants.py` | App config, niches, model names, version |
| `MASTER_ARCHITECTURE.md` | System architecture |
| `AGENT_WORKFLOW.md` | Multi-agent ownership rules |

### Build / run / test

```powershell
cd C:\AI\Projects\Generational
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
copy .env.example .env   # then edit OPENAI_API_KEY if desired
streamlit run app.py
python -m pytest
```

### Project structure (high level)

```text
generational/
├── app.py                 # Streamlit entry
├── core/                  # models, storage, workflows, AI providers
├── engines/               # pipeline plugins (intelligence + production)
├── providers/             # external source/LLM/media connectors
├── services/              # research, ideation, production, assets, …
├── ui/                    # Streamlit tabs/components
├── tests/                 # pytest suite
├── data/                  # local runtime data (mostly gitignored)
├── scripts/windows/       # workstation bootstrap
├── requirements.txt
├── requirements-dev.txt
└── SETUP.md               # this file
```

**Milestone check:** `python -m pytest` passes on the Windows venv.

---

## Phase 6 — Open the development environment

1. Open **Cursor** → **File → Open Folder** → `C:\AI\Projects\Generational`
2. Select the workspace interpreter: `C:\AI\Projects\Generational\venv\Scripts\python.exe`
3. Verify Git integration shows the correct branch (usually `main`)
4. Confirm no broken expectations:
   - Paths use repo-relative `data/` (not hard-coded Mac paths)
   - `.env` exists if you want live OpenAI calls
   - `streamlit run app.py` serves locally

**Common Windows issues**

| Symptom | Likely cause | Fix |
|---|---|---|
| `python` opens Store stub | App execution aliases | Disable “App Installer” python aliases in Windows Settings, or use `py -3` |
| `Activate.ps1` blocked | Execution policy | See Phase 7; or `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` after approval |
| Native wheel build fails | Missing MSVC | Install Visual Studio Build Tools (C++ workload) after approval |
| Long path errors | Legacy MAX_PATH | Enable long paths (Phase 7) |

---

## Phase 7 — Windows optimization (recommendations only)

Do **not** apply these blindly. Review each change, then approve.

### Developer Mode

**Settings → Privacy & security → For developers → Developer Mode**  
Why: symlink support, better dev-device features for Node/tooling.

### Power plan

Use **High performance** or **Ultimate Performance** while training/rendering.  
Why: avoids CPU parking/throttling during long jobs.

### Long file paths

```powershell
# Requires Administrator — elevates MAX_PATH for Win32 apps / Git
New-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem' `
  -Name 'LongPathsEnabled' -Value 1 -PropertyType DWORD -Force
```

Also:

```powershell
git config --global core.longpaths true
```

### Windows Terminal

Install from Microsoft Store; set PowerShell 7 as default profile.  
Why: better Unicode, tabs, and script hosting.

### File Explorer

Enable: file name extensions, hidden items.  
Consider excluding `C:\AI\Models`, `C:\AI\Temp`, and project `venv\` from real-time AV scanning if scans thrash disk (trade-off: security vs speed — decide consciously).

### Execution policy

```powershell
Get-ExecutionPolicy -List
# Recommended after approval:
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Why: allows local scripts (`Activate.ps1`, bootstrap) without unlocking the entire machine.

### Virtual memory / page file

For heavy local models: ensure free SSD headroom (models + page file). System-managed page file on the OS SSD is fine to start; for 64GB+ RAM workstations, system-managed remains a solid default unless you profile a specific shortage.

### GPU / CUDA (future)

When local inference lands, install the NVIDIA driver + CUDA toolkit matching your PyTorch/build pins — document the exact versions in this file when adopted.

---

## Phase 8 — Mac ↔ Windows workflow

```text
MacBook  →  commit  →  push  →  Windows PC  →  pull  →  develop  →  commit  →  push  →  MacBook
```

### On Mac (before leaving a session)

```bash
git status
git pull origin main
# ... work ...
git add <paths>
git commit -m "Clear message"
git push origin <branch>
```

### On Windows (start of session)

```powershell
cd C:\AI\Projects\Generational
git status -sb
git pull origin main   # or: git fetch origin; git checkout <branch>; git pull
```

### Verify the loop

1. On Mac: create a tiny branch, commit a harmless doc tweak, push.
2. On Windows: `git fetch` + `git checkout` that branch + `git pull`.
3. Confirm the file appears, make a second tiny commit, push.
4. On Mac: pull and confirm.

Never sync the project by copying folders or using iCloud/Dropbox on the git working tree — use **Git only**.

Keep machine-local artifacts out of git (already covered by `.gitignore`): `venv/`, `.env`, `data/projects/*.json`, caches, logs.

**Milestone check:** a commit created on one machine is visible on the other after push/pull with no divergent “mystery” files.

---

## Phase 9 — Documentation (this file)

Maintain `SETUP.md` in the repo root so both Mac and Windows share the same workstation contract.

After first successful Windows bootstrap, update the checklist below with real versions from that machine.

### Installed software (fill in on the Windows PC)

| Tool | Version / notes | Date |
|---|---|---|
| Git | | |
| GitHub Desktop | | |
| Python | | |
| uv | | |
| Node.js | | |
| npm | | |
| Docker Desktop | | |
| VS Build Tools | | |
| FFmpeg | | |
| PowerShell 7 | | |
| Cursor | | |

### Directory layout

See Phase 1 — canonical root `C:\AI`.

### Git configuration

- `user.name`: _(confirm)_
- `user.email`: _(confirm)_
- Default remote: `origin` → `https://github.com/jbrottem1/generational.git`

### Development workflow

Mac commit/push ↔ Windows pull/develop/commit/push (Phase 8). Multi-agent rules: `AGENT_WORKFLOW.md`.

### Recommended next steps

1. Run `Initialize-AIWorkstation.ps1 -SkipClone` on Windows; paste the tool report back for approval of installs.
2. Configure Git identity; sign in to GitHub Desktop.
3. Run with `-Clone`; open the folder in Cursor.
4. Create `venv`, install `requirements-dev.txt`, run `pytest`, then `streamlit run app.py`.
5. Apply approved Phase 7 OS tweaks.
6. Prove the Mac ↔ Windows git loop with a throwaway branch.
7. Add `OPENAI_API_KEY` to `.env` when ready for live generation.

---

## Quick command card (Windows)

```powershell
# Bootstrap directories + tool report
powershell -ExecutionPolicy Bypass -File .\scripts\windows\Initialize-AIWorkstation.ps1 -SkipClone

# Clone after GitHub auth
powershell -ExecutionPolicy Bypass -File .\scripts\windows\Initialize-AIWorkstation.ps1 -Clone

# Daily dev
cd C:\AI\Projects\Generational
git pull
.\venv\Scripts\Activate.ps1
streamlit run app.py
python -m pytest
```
