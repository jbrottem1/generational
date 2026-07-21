<#
.SYNOPSIS
  Generational Windows AI workstation bootstrap (Phases 1–4).

.DESCRIPTION
  Creates the C:\AI directory layout, reports installed development tools
  (without installing anything), inspects Git identity, and optionally clones
  the Generational repository into C:\AI\Projects\Generational.

  Safe by design:
  - Never deletes or overwrites existing files
  - Never installs software automatically
  - Never runs git config --global without explicit -SetGitIdentity
  - Never clones over a non-empty destination

.PARAMETER RepoUrl
  Git remote to clone. Default: https://github.com/jbrottem1/generational.git

.PARAMETER SkipClone
  Only create directories and report tools / Git config.

.PARAMETER Clone
  After checks, clone the repo if the destination is empty/missing.

.PARAMETER SetGitIdentity
  If supplied with -GitUserName and -GitUserEmail, write global Git identity.
  Requires explicit approval from the operator.

.PARAMETER GitUserName
  Value for git config --global user.name (only with -SetGitIdentity).

.PARAMETER GitUserEmail
  Value for git config --global user.email (only with -SetGitIdentity).

.EXAMPLE
  # Phase 1–3 only (recommended first run)
  powershell -ExecutionPolicy Bypass -File .\Initialize-AIWorkstation.ps1 -SkipClone

.EXAMPLE
  # After GitHub auth is ready
  powershell -ExecutionPolicy Bypass -File .\Initialize-AIWorkstation.ps1 -Clone
#>

[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [string]$RepoUrl = 'https://github.com/jbrottem1/generational.git',
  [switch]$SkipClone,
  [switch]$Clone,
  [switch]$SetGitIdentity,
  [string]$GitUserName,
  [string]$GitUserEmail
)

$ErrorActionPreference = 'Stop'

function Write-Milestone {
  param([string]$Title)
  Write-Host ''
  Write-Host ('=' * 72) -ForegroundColor Cyan
  Write-Host " $Title" -ForegroundColor Cyan
  Write-Host ('=' * 72) -ForegroundColor Cyan
}

function Write-Step {
  param([string]$Message)
  Write-Host ''
  Write-Host "→ $Message" -ForegroundColor Yellow
}

function Test-CommandAvailable {
  param([string]$Name)
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-CommandVersionSafe {
  param(
    [string]$Name,
    [string[]]$Args = @('--version')
  )
  if (-not (Test-CommandAvailable $Name)) {
    return $null
  }
  try {
    $output = & $Name @Args 2>&1 | Out-String
    return ($output -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 1).Trim()
  } catch {
    return 'installed (version probe failed)'
  }
}

function Test-AppInstalled {
  param(
    [string]$DisplayNamePattern,
    [string[]]$ExePaths = @()
  )
  foreach ($path in $ExePaths) {
    if ($path -and (Test-Path -LiteralPath $path)) {
      return $true
    }
  }
  $roots = @(
    'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*'
  )
  foreach ($root in $roots) {
    $hit = Get-ItemProperty $root -ErrorAction SilentlyContinue |
      Where-Object { $_.DisplayName -and ($_.DisplayName -match $DisplayNamePattern) } |
      Select-Object -First 1
    if ($hit) { return $true }
  }
  return $false
}

# ---------------------------------------------------------------------------
# PHASE 1 — Directory structure
# ---------------------------------------------------------------------------
Write-Milestone 'PHASE 1 — Create directory structure'

Write-Step 'Verify whether C:\AI exists (no changes yet).'
$aiRoot = 'C:\AI'
if (Test-Path -LiteralPath $aiRoot) {
  Write-Host "  Already exists: $aiRoot"
} else {
  Write-Host "  Missing: $aiRoot — will create."
}

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

Write-Step 'Create any missing folders under C:\AI (existing folders left untouched).'
foreach ($path in $folders) {
  if (Test-Path -LiteralPath $path) {
    Write-Host "  Already exists: $path"
  } else {
    if ($PSCmdlet.ShouldProcess($path, 'Create directory')) {
      New-Item -ItemType Directory -Path $path | Out-Null
      Write-Host "  Created:        $path" -ForegroundColor Green
    }
  }
}

Write-Step 'Confirm final directory structure.'
if (Test-CommandAvailable 'tree') {
  tree /A 'C:\AI'
} else {
  Get-ChildItem -LiteralPath 'C:\AI' -Recurse -Directory |
    ForEach-Object { $_.FullName.Replace('C:\AI', 'C:\AI') } |
    Sort-Object
}

Write-Host ''
Write-Host 'PHASE 1 COMPLETE — Verify the tree above before continuing.' -ForegroundColor Green

# ---------------------------------------------------------------------------
# PHASE 2 — Development tools (report only; never install)
# ---------------------------------------------------------------------------
Write-Milestone 'PHASE 2 — Verify development tools (report only)'

Write-Step 'Probe PATH and common install locations. Nothing will be installed.'

$toolReport = @()

function Add-ToolRow {
  param(
    [string]$Name,
    [bool]$Present,
    [string]$Detail,
    [string]$Why,
    [string]$OfficialUrl
  )
  $script:toolReport += [pscustomobject]@{
    Tool     = $Name
    Status   = $(if ($Present) { 'FOUND' } else { 'MISSING' })
    Detail   = $Detail
    Why      = $Why
    Download = $OfficialUrl
  }
}

# Git
$gitVer = Get-CommandVersionSafe 'git'
Add-ToolRow -Name 'Git' -Present ([bool]$gitVer) -Detail $(if ($gitVer) { $gitVer } else { 'not on PATH' }) `
  -Why 'Source control for Generational; required for clone/pull/push Mac ↔ Windows workflow.' `
  -OfficialUrl 'https://git-scm.com/download/win'

# GitHub Desktop
$ghDesktop = Test-AppInstalled -DisplayNamePattern 'GitHub Desktop' -ExePaths @(
  "$env:LOCALAPPDATA\GitHubDesktop\GitHubDesktop.exe",
  "$env:LOCALAPPDATA\Programs\GitHub Desktop\GitHubDesktop.exe"
)
Add-ToolRow -Name 'GitHub Desktop' -Present $ghDesktop `
  -Detail $(if ($ghDesktop) { 'Installed' } else { 'Not detected' }) `
  -Why 'GUI auth + clone workflow for GitHub; convenient for initial Windows sign-in.' `
  -OfficialUrl 'https://desktop.github.com/'

# Python
$pyVer = Get-CommandVersionSafe 'python'
if (-not $pyVer) { $pyVer = Get-CommandVersionSafe 'py' -Args @('-3', '--version') }
Add-ToolRow -Name 'Python' -Present ([bool]$pyVer) -Detail $(if ($pyVer) { $pyVer } else { 'not on PATH' }) `
  -Why 'Generational is a Python/Streamlit app; runtime for venv, pytest, and streamlit run.' `
  -OfficialUrl 'https://www.python.org/downloads/windows/'

# uv
$uvVer = Get-CommandVersionSafe 'uv'
Add-ToolRow -Name 'uv' -Present ([bool]$uvVer) -Detail $(if ($uvVer) { $uvVer } else { 'not on PATH' }) `
  -Why 'Fast Python package/venv manager; optional but recommended for reproducible installs.' `
  -OfficialUrl 'https://docs.astral.sh/uv/getting-started/installation/'

# Node.js / npm (not required by Generational core today; useful for tooling)
$nodeVer = Get-CommandVersionSafe 'node'
$npmVer = Get-CommandVersionSafe 'npm'
Add-ToolRow -Name 'Node.js' -Present ([bool]$nodeVer) -Detail $(if ($nodeVer) { $nodeVer } else { 'not on PATH' }) `
  -Why 'Not required by Generational core today; useful for front-end tooling and Cursor/ecosystem scripts.' `
  -OfficialUrl 'https://nodejs.org/en/download'
Add-ToolRow -Name 'npm' -Present ([bool]$npmVer) -Detail $(if ($npmVer) { $npmVer } else { 'not on PATH' }) `
  -Why 'Ships with Node.js; package manager for JS tooling if/when needed.' `
  -OfficialUrl 'https://nodejs.org/en/download'

# Docker Desktop
$dockerVer = Get-CommandVersionSafe 'docker'
$dockerDesktop = Test-AppInstalled -DisplayNamePattern 'Docker Desktop' -ExePaths @(
  "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
)
$dockerPresent = [bool]$dockerVer -or $dockerDesktop
Add-ToolRow -Name 'Docker Desktop' -Present $dockerPresent `
  -Detail $(if ($dockerVer) { $dockerVer } elseif ($dockerDesktop) { 'Installed (daemon may be stopped)' } else { 'Not detected' }) `
  -Why 'Optional for containerized providers/services and consistent runtime isolation.' `
  -OfficialUrl 'https://www.docker.com/products/docker-desktop/'

# Visual Studio Build Tools
$vsBuild = Test-AppInstalled -DisplayNamePattern 'Visual Studio Build Tools|Build Tools for Visual Studio' -ExePaths @(
  "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
)
$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$vsDetail = 'Not detected'
if (Test-Path -LiteralPath $vswhere) {
  try {
    $vsPath = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath 2>$null
    if ($vsPath) {
      $vsBuild = $true
      $vsDetail = "MSVC tools at $vsPath"
    } else {
      $vsDetail = 'vswhere present; MSVC C++ tools not confirmed'
    }
  } catch {
    $vsDetail = 'vswhere present; probe failed'
  }
}
Add-ToolRow -Name 'Visual Studio Build Tools' -Present $vsBuild -Detail $vsDetail `
  -Why 'Compiles native Python wheels (and some ML deps) on Windows when binaries are unavailable.' `
  -OfficialUrl 'https://visualstudio.microsoft.com/visual-cpp-build-tools/'

# FFmpeg
$ffmpegVer = Get-CommandVersionSafe 'ffmpeg' -Args @('-version')
Add-ToolRow -Name 'FFmpeg' -Present ([bool]$ffmpegVer) -Detail $(if ($ffmpegVer) { $ffmpegVer } else { 'not on PATH' }) `
  -Why 'Media encode/decode for video/audio pipelines Generational is building toward.' `
  -OfficialUrl 'https://www.gyan.dev/ffmpeg/builds/'

# PowerShell 7
$pwshVer = Get-CommandVersionSafe 'pwsh'
Add-ToolRow -Name 'PowerShell 7' -Present ([bool]$pwshVer) -Detail $(if ($pwshVer) { $pwshVer } else { 'not on PATH (Windows PowerShell 5.1 may still be available)' }) `
  -Why 'Modern cross-platform shell; preferred for long-term automation scripts under C:\AI\Scripts.' `
  -OfficialUrl 'https://learn.microsoft.com/powershell/scripting/install/installing-powershell-on-windows'

$toolReport | Format-Table -AutoSize Tool, Status, Detail
Write-Host ''

$missing = @($toolReport | Where-Object { $_.Status -eq 'MISSING' })
if ($missing.Count -eq 0) {
  Write-Host 'All probed tools were found.' -ForegroundColor Green
} else {
  Write-Host 'MISSING TOOLS — not installed by this script. Review and approve each install:' -ForegroundColor Magenta
  foreach ($m in $missing) {
    Write-Host ''
    Write-Host "  Tool:     $($m.Tool)" -ForegroundColor Magenta
    Write-Host "  Why:      $($m.Why)"
    Write-Host "  Download: $($m.Download)"
  }
  Write-Host ''
  Write-Host 'Reply with which tools you approve installing (or install manually from the links).' -ForegroundColor Yellow
}

Write-Host ''
Write-Host 'PHASE 2 COMPLETE — No software was installed.' -ForegroundColor Green

# ---------------------------------------------------------------------------
# PHASE 3 — Git setup (inspect; configure only if explicitly requested)
# ---------------------------------------------------------------------------
Write-Milestone 'PHASE 3 — Git setup'

if (-not (Test-CommandAvailable 'git')) {
  Write-Host 'Git is not available on PATH. Install Git before continuing Phases 3–4.' -ForegroundColor Red
} else {
  Write-Step 'Check git --version and global identity (read-only unless -SetGitIdentity).'
  git --version

  $existingName = git config --global user.name 2>$null
  $existingEmail = git config --global user.email 2>$null

  Write-Host "  user.name  = $(if ($existingName) { $existingName } else { '(not set)' })"
  Write-Host "  user.email = $(if ($existingEmail) { $existingEmail } else { '(not set)' })"

  if ($SetGitIdentity) {
    if (-not $GitUserName -or -not $GitUserEmail) {
      throw '-SetGitIdentity requires both -GitUserName and -GitUserEmail'
    }
    Write-Step "Write global Git identity to '$GitUserName' / '$GitUserEmail' (explicit approval via switch)."
    if ($PSCmdlet.ShouldProcess('git config --global', 'Set user.name / user.email')) {
      git config --global user.name $GitUserName
      git config --global user.email $GitUserEmail
      Write-Host '  Updated global Git identity.' -ForegroundColor Green
    }
  } elseif (-not $existingName -or -not $existingEmail) {
    Write-Host ''
    Write-Host 'Git identity is incomplete. Do NOT guess — provide name and email, then re-run with:' -ForegroundColor Yellow
    Write-Host '  .\Initialize-AIWorkstation.ps1 -SkipClone -SetGitIdentity -GitUserName "Your Name" -GitUserEmail "you@example.com"'
  }
}

Write-Host ''
Write-Host 'PHASE 3 COMPLETE.' -ForegroundColor Green

# ---------------------------------------------------------------------------
# PHASE 4 — GitHub connection / clone
# ---------------------------------------------------------------------------
Write-Milestone 'PHASE 4 — GitHub connection / clone'

$projectRoot = 'C:\AI\Projects\Generational'
$gitDir = Join-Path $projectRoot '.git'

Write-Step 'Inspect clone destination (never wipe existing content).'
if (Test-Path -LiteralPath $gitDir) {
  Write-Host "  Git repository already present at $projectRoot"
  Push-Location $projectRoot
  try {
    git remote -v
    git status -sb
  } finally {
    Pop-Location
  }
  Write-Host '  Skipping clone.' -ForegroundColor Green
} elseif ($SkipClone -and -not $Clone) {
  Write-Host '  -SkipClone set (or default). Not cloning yet.'
  Write-Host '  Next: sign in to GitHub Desktop (File → Options → Accounts), then re-run with -Clone.'
  Write-Host "  Destination: $projectRoot"
  Write-Host "  Remote:      $RepoUrl"
} elseif ($Clone) {
  $items = @()
  if (Test-Path -LiteralPath $projectRoot) {
    $items = @(Get-ChildItem -LiteralPath $projectRoot -Force | Where-Object { $_.Name -ne '.DS_Store' })
  }
  if ($items.Count -gt 0) {
    Write-Host "  Destination is not empty: $projectRoot" -ForegroundColor Red
    Write-Host '  Refusing to clone over existing files. Move/rename the folder, then retry.' -ForegroundColor Red
  } else {
    if (-not (Test-CommandAvailable 'git')) {
      throw 'Git is required to clone. Install Git, then re-run with -Clone.'
    }
    Write-Step "Clone $RepoUrl into $projectRoot using Git (not a manual copy)."
    if (-not (Test-Path -LiteralPath $projectRoot)) {
      New-Item -ItemType Directory -Path $projectRoot | Out-Null
    }
    if ($PSCmdlet.ShouldProcess($projectRoot, "git clone $RepoUrl .")) {
      # Clone into the existing empty folder — never delete destination content.
      Push-Location $projectRoot
      try {
        git clone $RepoUrl .
      } finally {
        Pop-Location
      }
      Write-Host "  Clone complete: $projectRoot" -ForegroundColor Green
    }
  }
} else {
  Write-Host '  Neither -Clone nor -SkipClone specified — defaulting to report-only (no clone).'
  Write-Host '  Re-run with -Clone after GitHub authentication is ready.'
}

Write-Host ''
Write-Host 'PHASE 4 COMPLETE.' -ForegroundColor Green
Write-Host ''
Write-Host 'Next milestones (manual / Cursor on this PC):' -ForegroundColor Cyan
Write-Host '  Phase 5–6: open C:\AI\Projects\Generational in Cursor, create venv, install deps, run tests'
Write-Host '  Phase 7:   review Windows optimization recommendations in SETUP.md (do not auto-apply)'
Write-Host '  Phase 8:   verify Mac ↔ Windows git pull/push workflow'
Write-Host '  Phase 9:   SETUP.md lives in the repo root after pull'
Write-Host ''
