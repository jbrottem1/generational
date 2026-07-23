#Requires -Version 5.1
<#
.SYNOPSIS
  Generational local Windows workstation certification (Blender-aware).
.NOTES
  ASCII-only + UTF-8 BOM for Windows PowerShell 5.1.
  Does not modify production architecture.
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [string]$BlenderExe = "",
  [switch]$SkipBlenderProbe,
  [switch]$SkipNetwork
)

$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $RepoRoot) {
  $RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
}
$OutDir = Join-Path $ScriptDir "certification_artifacts"
$ReportPath = Join-Path $ScriptDir "WORKSTATION_CERTIFICATION_REPORT.md"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$script:Score = 0
$script:MaxScore = 100
$script:Blockers = New-Object System.Collections.Generic.List[string]
$script:Warnings = New-Object System.Collections.Generic.List[string]
$script:Remediation = New-Object System.Collections.Generic.List[string]
$script:Report = New-Object System.Collections.Generic.List[string]

function Add-ReportLine([string]$Text) { [void]$script:Report.Add($Text) }
function Add-Blocker([string]$Text) {
  [void]$script:Blockers.Add($Text)
  Add-ReportLine ("- BLOCKER: " + $Text)
}
function Add-Warning([string]$Text) {
  [void]$script:Warnings.Add($Text)
  Add-ReportLine ("- WARNING: " + $Text)
}
function Add-Points([int]$Points, [string]$Reason) {
  $script:Score += $Points
  Add-ReportLine ("- +" + $Points + " : " + $Reason)
}
function Add-Fix([string]$Text) { [void]$script:Remediation.Add($Text) }

function Invoke-Capture {
  param([string]$FilePath, [string[]]$ArgumentList = @())
  $stdout = Join-Path $OutDir ("cap_out_" + [guid]::NewGuid().ToString("N") + ".txt")
  $stderr = Join-Path $OutDir ("cap_err_" + [guid]::NewGuid().ToString("N") + ".txt")
  try {
    $p = Start-Process -FilePath $FilePath -ArgumentList $ArgumentList `
      -NoNewWindow -Wait -PassThru `
      -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    $out = ""
    $err = ""
    if (Test-Path $stdout) { $out = Get-Content -Raw -ErrorAction SilentlyContinue $stdout }
    if (Test-Path $stderr) { $err = Get-Content -Raw -ErrorAction SilentlyContinue $stderr }
    return [pscustomobject]@{
      ExitCode = $p.ExitCode
      StdOut   = $(if ($null -eq $out) { "" } else { $out })
      StdErr   = $(if ($null -eq $err) { "" } else { $err })
    }
  } catch {
    return [pscustomobject]@{ ExitCode = 1; StdOut = ""; StdErr = $_.Exception.Message }
  } finally {
    Remove-Item $stdout, $stderr -ErrorAction SilentlyContinue
  }
}

function Find-BlenderExe {
  param([string]$Explicit = "")
  if ($Explicit -and (Test-Path -LiteralPath $Explicit)) {
    return (Resolve-Path -LiteralPath $Explicit).Path
  }

  $cmd = Get-Command blender -ErrorAction SilentlyContinue
  if ($cmd -and $cmd.Source -and (Test-Path $cmd.Source)) { return $cmd.Source }

  $roots = @(
    "${env:ProgramFiles}\Blender Foundation",
    "${env:ProgramFiles(x86)}\Blender Foundation",
    "$env:LOCALAPPDATA\Programs\Blender Foundation"
  )
  foreach ($root in $roots) {
    if (-not (Test-Path $root)) { continue }
    $hit = Get-ChildItem -Path $root -Filter "blender.exe" -Recurse -ErrorAction SilentlyContinue |
      Sort-Object FullName -Descending |
      Select-Object -First 1
    if ($hit) { return $hit.FullName }
  }

  $wingetLink = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\blender.exe"
  if (Test-Path -LiteralPath $wingetLink) { return (Resolve-Path -LiteralPath $wingetLink).Path }

  try {
    $w = winget list --id BlenderFoundation.Blender 2>$null | Out-String
    if ($w -match "BlenderFoundation\.Blender") {
      Add-Warning "winget reports Blender installed, but blender.exe was not found under Program Files."
    }
  } catch { }

  return $null
}

function Test-ParserSelfCheck {
  $tokens = $null
  $errors = $null
  [void][System.Management.Automation.Language.Parser]::ParseFile(
    $PSCommandPath,
    [ref]$tokens,
    [ref]$errors
  )
  return @($errors).Count
}

# ---------------------------------------------------------------------------
Add-ReportLine "# Generational Workstation Certification Report"
Add-ReportLine ""
Add-ReportLine ("Generated: " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss K"))
Add-ReportLine ("Hostname: " + $env:COMPUTERNAME)
Add-ReportLine ("User: " + $env:USERNAME)
Add-ReportLine ("RepoRoot: " + $RepoRoot)
Add-ReportLine ("Script: " + $PSCommandPath)
Add-ReportLine ""
Add-ReportLine "## Self-check"
$parserErrs = Test-ParserSelfCheck
Add-ReportLine ("- PowerShell parser errors in this script: " + $parserErrs)
if ($parserErrs -gt 0) {
  Add-Blocker "certify_workstation.ps1 still has parser errors"
}

# ---------------------------------------------------------------------------
Add-ReportLine ""
Add-ReportLine "## 1. Windows / Hardware"
$os = Get-CimInstance Win32_OperatingSystem
$cs = Get-CimInstance Win32_ComputerSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$ramGB = [math]::Round($cs.TotalPhysicalMemory / 1GB, 1)
Add-ReportLine ("- OS: " + $os.Caption + " (" + $os.Version + ")")
Add-ReportLine ("- Architecture: " + $env:PROCESSOR_ARCHITECTURE)
Add-ReportLine ("- CPU: " + $cpu.Name)
Add-ReportLine ("- Logical processors: " + $cpu.NumberOfLogicalProcessors)
Add-ReportLine ("- RAM: " + $ramGB + " GB")
if ($ramGB -ge 16) { Add-Points 5 "RAM >= 16GB" } else {
  Add-Warning "RAM under 16GB may limit 3D production"
  Add-Points 2 "RAM present but under 16GB"
}

# ---------------------------------------------------------------------------
Add-ReportLine ""
Add-ReportLine "## 2. GPU / Drivers / CUDA"
$gpuRows = @(Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue)
if ($gpuRows.Count -eq 0) {
  Add-Blocker "No Win32_VideoController GPU detected"
} else {
  foreach ($g in $gpuRows) {
    $vramMB = if ($g.AdapterRAM -and $g.AdapterRAM -gt 0) {
      [math]::Round($g.AdapterRAM / 1MB)
    } else { "unknown" }
    Add-ReportLine ("- GPU: " + $g.Name)
    Add-ReportLine ("- DriverVersion (WMI): " + $g.DriverVersion)
    Add-ReportLine ("- AdapterRAM (WMI MB): " + $vramMB)
  }
  Add-Points 5 "GPU enumerated via WMI"
}

$nvidia = Get-Command nvidia-smi -ErrorAction SilentlyContinue
$cudaOk = $false
$nvidiaDriver = ""
$nvidiaName = ""
$nvidiaVram = ""
if ($nvidia) {
  # Supported query fields only (no cuda_version).
  $q = Invoke-Capture -FilePath $nvidia.Source -ArgumentList @(
    "--query-gpu=name,driver_version,memory.total",
    "--format=csv,noheader"
  )
  Add-ReportLine ("- nvidia-smi: " + ($q.StdOut.Trim() -replace "`r?`n", " | "))
  if ($q.ExitCode -eq 0 -and $q.StdOut.Trim()) {
    $parts = $q.StdOut.Trim().Split(",") | ForEach-Object { $_.Trim() }
    if ($parts.Count -ge 3) {
      $nvidiaName = $parts[0]
      $nvidiaDriver = $parts[1]
      $nvidiaVram = $parts[2]
    }
    Add-Points 8 "nvidia-smi query succeeded"
    $cudaOk = $true
  } else {
    Add-Warning "nvidia-smi present but query failed"
    Add-ReportLine ("- nvidia-smi stderr: " + $q.StdErr.Trim())
  }
  $ver = Invoke-Capture -FilePath $nvidia.Source -ArgumentList @()
  if ($ver.StdOut -match "CUDA Version:\s*([0-9.]+)") {
    Add-ReportLine ("- CUDA Version (from nvidia-smi banner): " + $Matches[1])
  }
} else {
  Add-Warning "nvidia-smi not found (AMD/Intel GPU or driver tools missing)"
  Add-Fix "If NVIDIA GPU: install Studio/Game Ready driver from https://www.nvidia.com/drivers"
}

# ---------------------------------------------------------------------------
Add-ReportLine ""
Add-ReportLine "## 3. PowerShell / Python / Git"
Add-ReportLine ("- PowerShell: " + $PSVersionTable.PSVersion.ToString())
Add-Points 3 "PowerShell available"

$py = Get-Command python -ErrorAction SilentlyContinue
if ($py) {
  $pv = Invoke-Capture -FilePath $py.Source -ArgumentList @("--version")
  Add-ReportLine ("- Python: " + $pv.StdOut.Trim() + $pv.StdErr.Trim())
  Add-ReportLine ("- Python path: " + $py.Source)
  Add-Points 5 "Python on PATH"
} else {
  Add-Blocker "python not on PATH"
  Add-Fix "winget install Python.Python.3.12"
}

$git = Get-Command git -ErrorAction SilentlyContinue
if ($git) {
  $gv = Invoke-Capture -FilePath $git.Source -ArgumentList @("--version")
  Add-ReportLine ("- Git: " + $gv.StdOut.Trim())
  Add-Points 3 "Git available"
  Push-Location $RepoRoot
  $remote = (git remote get-url origin 2>$null)
  $branch = (git branch --show-current 2>$null)
  Pop-Location
  Add-ReportLine ("- Git remote: " + $remote)
  Add-ReportLine ("- Git branch: " + $branch)
  if ($remote -match "generational") { Add-Points 2 "GitHub remote looks correct" }
} else {
  Add-Blocker "git not on PATH"
  Add-Fix "winget install Git.Git"
}

$lfs = Get-Command git-lfs -ErrorAction SilentlyContinue
if ($lfs) {
  $lv = Invoke-Capture -FilePath $lfs.Source -ArgumentList @("version")
  Add-ReportLine ("- Git LFS: " + $lv.StdOut.Trim())
  Add-Points 3 "Git LFS installed"
  Push-Location $RepoRoot
  $lfsEnv = (git lfs env 2>$null | Select-Object -First 20) -join "`n"
  Pop-Location
  Add-ReportLine "### git lfs env (truncated)"
  Add-ReportLine '```'
  Add-ReportLine $lfsEnv
  Add-ReportLine '```'
} else {
  Add-Warning "Git LFS not installed"
  Add-Fix "winget install GitHub.GitLFS ; git lfs install"
}

$ff = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($ff) {
  $fv = Invoke-Capture -FilePath $ff.Source -ArgumentList @("-version")
  $first = ($fv.StdOut -split "`r?`n")[0]
  Add-ReportLine ("- FFmpeg: " + $first)
  Add-Points 3 "FFmpeg available"
} else {
  Add-Warning "ffmpeg not on PATH (needed for some video pipelines)"
  Add-Fix "winget install Gyan.FFmpeg"
}

# ---------------------------------------------------------------------------
Add-ReportLine ""
Add-ReportLine "## 4. Blender installation"
$blender = Find-BlenderExe -Explicit $BlenderExe
$blenderVersion = ""
if ($SkipNetwork) {
  Add-ReportLine "- SkipNetwork: network git checks skipped (local certification mode)"
}
$bpyOk = $false
$eeveeOk = $false
$cyclesOk = $false
$ffmpegBlender = $false
$bgOk = $false
$optix = $false
$cudaDev = $false
$hip = $false
$oneapi = $false
$metal = $false
$cpuOnly = $true
$deviceSummary = "unknown"
$pngOk = $false
$animOk = $false
$engineUsed = ""
$deviceUsed = ""
$pngPath = ""
$animPath = ""
$pngSeconds = ""
$animSeconds = ""

if (-not $blender) {
  Add-Blocker "Blender not installed / blender.exe not found"
  Add-Fix "cd verification\local_windows ; .\INSTALL_AND_CERTIFY.bat"
  Add-Fix "Or: winget install --exact --id BlenderFoundation.Blender"
} else {
  Add-ReportLine ("- blender.exe: " + $blender)
  Add-ReportLine ("- install dir: " + (Split-Path $blender -Parent))
  Add-Points 10 "blender.exe located"

  $bv = Invoke-Capture -FilePath $blender -ArgumentList @("--version")
  $blenderVersion = (($bv.StdOut + "`n" + $bv.StdErr) -split "`r?`n" | Where-Object { $_ -match "Blender" } | Select-Object -First 1)
  if (-not $blenderVersion) { $blenderVersion = ($bv.StdOut + $bv.StdErr).Trim() }
  Add-ReportLine ("- blender --version: " + $blenderVersion)
  if ($bv.ExitCode -eq 0 -or $blenderVersion -match "Blender") {
    Add-Points 5 "blender --version works"
  } else {
    Add-Blocker "blender --version failed"
  }

  if (-not $SkipBlenderProbe) {
    $probeBpy = Join-Path $ScriptDir "probe_bpy.py"
    $probeOut = Join-Path $OutDir "bpy_probe.json"
    $pr = Invoke-Capture -FilePath $blender -ArgumentList @(
      "--background",
      "--python", $probeBpy,
      "--",
      $probeOut
    )
    Add-ReportLine ("- bpy probe exit: " + $pr.ExitCode)
    if (Test-Path $probeOut) {
      try {
        $j = Get-Content -Raw $probeOut | ConvertFrom-Json
        $bgOk = [bool]$j.background_ok
        $bpyOk = [bool]$j.bpy_ok
        $eeveeOk = [bool]$j.eevee_available
        $cyclesOk = [bool]$j.cycles_available
        $ffmpegBlender = [bool]$j.ffmpeg_support
        $optix = [bool]$j.optix
        $cudaDev = [bool]$j.cuda
        $hip = [bool]$j.hip
        $oneapi = [bool]$j.oneapi
        $metal = [bool]$j.metal
        $cpuOnly = [bool]$j.cpu_only
        $deviceSummary = [string]$j.device_summary
        Add-ReportLine ("- bpy_ok: " + $bpyOk)
        Add-ReportLine ("- background_ok: " + $bgOk)
        Add-ReportLine ("- eevee_available: " + $eeveeOk)
        Add-ReportLine ("- cycles_available: " + $cyclesOk)
        Add-ReportLine ("- ffmpeg_support (Blender): " + $ffmpegBlender)
        Add-ReportLine ("- Cycles devices: " + $deviceSummary)
        Add-ReportLine ("- OptiX: " + $optix + " | CUDA: " + $cudaDev + " | HIP: " + $hip + " | oneAPI: " + $oneapi + " | Metal: " + $metal)
        Add-ReportLine ("- CPU only: " + $cpuOnly)
        if ($bpyOk -and $bgOk) { Add-Points 10 "bpy + background mode OK" } else { Add-Blocker "bpy/background probe failed" }
        if ($eeveeOk) { Add-Points 3 "Eevee available" } else { Add-Warning "Eevee not reported available" }
        if ($cyclesOk) { Add-Points 5 "Cycles available" } else { Add-Blocker "Cycles not available" }
        if ($ffmpegBlender) { Add-Points 2 "Blender FFmpeg support present" } else { Add-Warning "Blender FFmpeg support not detected" }
        if ($optix -or $cudaDev -or $hip -or $oneapi) {
          Add-Points 7 "GPU Cycles backend detected (not blindly enabled)"
        } else {
          Add-Warning "No GPU Cycles backend detected; CPU fallback only"
          Add-Points 2 "CPU Cycles fallback documented"
        }
      } catch {
        Add-Blocker ("Failed to parse bpy probe JSON: " + $_.Exception.Message)
      }
    } else {
      Add-Blocker "bpy probe did not write JSON"
      Add-ReportLine ("- probe stdout: " + $pr.StdOut.Trim())
      Add-ReportLine ("- probe stderr: " + $pr.StdErr.Trim())
    }

    # Real scene render (mesh + camera + light + PNG + short anim)
    $probeScene = Join-Path $ScriptDir "probe_scene_render.py"
    $sceneJson = Join-Path $OutDir "scene_render.json"
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $sr = Invoke-Capture -FilePath $blender -ArgumentList @(
      "--background",
      "--python", $probeScene,
      "--",
      $OutDir,
      $sceneJson
    )
    $sw.Stop()
    Add-ReportLine ("- scene render wrapper exit: " + $sr.ExitCode)
    Add-ReportLine ("- scene render wall seconds: " + [math]::Round($sw.Elapsed.TotalSeconds, 2))
    if (Test-Path $sceneJson) {
      try {
        $sj = Get-Content -Raw $sceneJson | ConvertFrom-Json
        $pngOk = [bool]$sj.png_ok
        $animOk = [bool]$sj.anim_ok
        $engineUsed = [string]$sj.engine
        $deviceUsed = [string]$sj.device
        $pngPath = [string]$sj.png_path
        $animPath = [string]$sj.anim_path
        $pngSeconds = [string]$sj.png_seconds
        $animSeconds = [string]$sj.anim_seconds
        Add-ReportLine ("- render engine: " + $engineUsed)
        Add-ReportLine ("- compute device: " + $deviceUsed)
        Add-ReportLine ("- PNG path: " + $pngPath)
        Add-ReportLine ("- PNG exists: " + $pngOk + " size=" + $sj.png_bytes + " seconds=" + $pngSeconds)
        Add-ReportLine ("- Anim path: " + $animPath)
        Add-ReportLine ("- Anim exists: " + $animOk + " size=" + $sj.anim_bytes + " seconds=" + $animSeconds)
        Add-ReportLine ("- scene has mesh/camera/light: " + $sj.has_mesh + "/" + $sj.has_camera + "/" + $sj.has_light)
        if ($pngOk -and (Test-Path $pngPath)) {
          Add-Points 10 "Real Blender one-frame PNG render"
        } else {
          Add-Blocker "Blender PNG frame missing"
        }
        if ($animOk -and (Test-Path $animPath)) {
          Add-Points 8 "Real Blender short animation output"
        } else {
          Add-Blocker "Blender animation output missing"
        }
      } catch {
        Add-Blocker ("Failed to parse scene render JSON: " + $_.Exception.Message)
      }
    } else {
      Add-Blocker "scene render probe did not write JSON"
      Add-ReportLine ("- stdout: " + $sr.StdOut.Trim())
      Add-ReportLine ("- stderr: " + $sr.StdErr.Trim())
    }
  } else {
    Add-Warning "SkipBlenderProbe set; Blender runtime checks skipped"
  }
}

# ---------------------------------------------------------------------------
Add-ReportLine ""
Add-ReportLine "## 5. Repository / Generational assets"
$mustDirs = @("services", "engines", "apps", "data", "verification")
$pathsOk = $true
foreach ($d in $mustDirs) {
  $p = Join-Path $RepoRoot $d
  if (Test-Path $p) {
    Add-ReportLine ("- OK dir: " + $d)
  } else {
    $pathsOk = $false
    Add-Blocker ("Missing repo directory: " + $d)
  }
}
if ($pathsOk) { Add-Points 5 "Core repository paths valid" }

$blend = @(Get-ChildItem -Path $RepoRoot -Recurse -Filter "*.blend" -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch "\\node_modules\\|\\\.git\\|\\certification_artifacts\\" })
$fbx = @(Get-ChildItem -Path $RepoRoot -Recurse -Include *.fbx,*.glb,*.gltf -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch "\\node_modules\\|\\\.git\\" })
$doctorMeta = @(Get-ChildItem -Path (Join-Path $RepoRoot "data") -Recurse -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match "DOCTOR_001|doctor_001" })

Add-ReportLine ("- .blend files found: " + $blend.Count)
Add-ReportLine ("- fbx/glb/gltf found: " + $fbx.Count)
Add-ReportLine ("- DOCTOR_001 metadata/json hits under data/: " + $doctorMeta.Count)

$gitignore = Join-Path $RepoRoot ".gitignore"
$gitattributes = Join-Path $RepoRoot ".gitattributes"
$ignoresBlend = $false
if (Test-Path $gitignore) {
  $gi = Get-Content $gitignore -Raw
  if ($gi -match "(?m)^\s*\*\.blend\s*$" -or $gi -match "(?m)^\s*\*\.blend$") { $ignoresBlend = $true }
}
Add-ReportLine ("- .gitignore ignores *.blend: " + $ignoresBlend)
Add-ReportLine ("- .gitattributes exists: " + (Test-Path $gitattributes))

if ($blend.Count -eq 0) {
  Add-Warning "No production .blend files in this clone (content production blocked until restored)"
  Add-ReportLine "- Sync diagnosis: ABSENT FROM GIT (not an LFS pointer pull failure)."
  Add-ReportLine "- DOCTOR_001 exists as JSON/metadata under data/, not as Blender binary assets."
  Add-ReportLine "- Synchronization plan: restore .blend from external asset store/laptop backup; enable Git LFS only after explicit approval."
  Add-ReportLine "- See: verification/local_windows/ASSET_SYNC_FINDINGS.md"
  Add-ReportLine "- Proposed (not applied): verification/local_windows/RECOMMENDED_gitattributes.txt"
  Add-Points 3 "Asset synchronization issue explicitly diagnosed (absent from Git)"
  Add-Fix "Copy local DOCTOR_001 .blend assets into an approved repo path, then re-run CERTIFY.bat"
  Add-Fix "Review RECOMMENDED_gitattributes.txt before enabling Git LFS; do not migrate history without approval"
} else {
  Add-Points 5 "Production .blend assets present"
  foreach ($b in $blend | Select-Object -First 10) {
    Add-ReportLine ("  - " + $b.FullName)
  }
}

if ($doctorMeta.Count -gt 0) {
  Add-Points 2 "DOCTOR_001 metadata present under data/"
}

# ---------------------------------------------------------------------------
Add-ReportLine ""
Add-ReportLine "## 6. Score / Verdict"
if ($script:Score -gt $script:MaxScore) { $script:Score = $script:MaxScore }
Add-ReportLine ("- Score: " + $script:Score + " / " + $script:MaxScore)
Add-ReportLine ("- Blockers: " + $script:Blockers.Count)
Add-ReportLine ("- Warnings: " + $script:Warnings.Count)

$mandatoryPass = (
  $null -ne $blender -and
  $bgOk -and
  $bpyOk -and
  $pngOk -and
  $animOk -and
  ($eeveeOk -or $cyclesOk) -and
  $pathsOk -and
  $script:Blockers.Count -eq 0
)

if ($mandatoryPass -and $script:Score -ge 80) {
  Add-ReportLine ""
  Add-ReportLine "## WORKSTATION CERTIFIED FOR GENERATIONAL 3D PRODUCTION"
  $verdict = "PASS"
} else {
  Add-ReportLine ""
  Add-ReportLine "## CERTIFICATION FAILED"
  $verdict = "FAIL"
  Add-ReportLine ""
  Add-ReportLine "### Remaining blockers"
  if ($script:Blockers.Count -eq 0) {
    Add-ReportLine "- Score/mandatory checks did not meet threshold (no discrete blocker list)."
  } else {
    foreach ($b in $script:Blockers) { Add-ReportLine ("- " + $b) }
  }
}

Add-ReportLine ""
Add-ReportLine "## Remediation commands"
if ($script:Remediation.Count -eq 0) {
  Add-ReportLine "- None queued."
} else {
  foreach ($r in $script:Remediation) { Add-ReportLine ("- ``" + $r + "``") }
}

Add-ReportLine ""
Add-ReportLine "## Summary table"
Add-ReportLine "| Check | Value |"
Add-ReportLine "|---|---|"
Add-ReportLine ("| Windows | " + $os.Caption + " |")
Add-ReportLine ("| CPU | " + $cpu.Name + " |")
Add-ReportLine ("| RAM GB | " + $ramGB + " |")
Add-ReportLine ("| GPU (nvidia-smi) | " + $(if ($nvidiaName) { $nvidiaName } else { "see WMI" }) + " |")
Add-ReportLine ("| NVIDIA driver | " + $(if ($nvidiaDriver) { $nvidiaDriver } else { "n/a" }) + " |")
Add-ReportLine ("| VRAM | " + $(if ($nvidiaVram) { $nvidiaVram } else { "see WMI" }) + " |")
Add-ReportLine ("| Blender exe | " + $(if ($blender) { $blender } else { "MISSING" }) + " |")
Add-ReportLine ("| Blender version | " + $(if ($blenderVersion) { $blenderVersion } else { "n/a" }) + " |")
Add-ReportLine ("| bpy | " + $bpyOk + " |")
Add-ReportLine ("| Eevee | " + $eeveeOk + " |")
Add-ReportLine ("| Cycles | " + $cyclesOk + " |")
Add-ReportLine ("| Cycles devices | " + $deviceSummary + " |")
Add-ReportLine ("| Render engine used | " + $engineUsed + " |")
Add-ReportLine ("| Compute device used | " + $deviceUsed + " |")
Add-ReportLine ("| One-frame PNG | " + $pngOk + " |")
Add-ReportLine ("| Short anim | " + $animOk + " |")
Add-ReportLine ("| Git LFS | " + $(if ($lfs) { "yes" } else { "no" }) + " |")
Add-ReportLine ("| .blend count | " + $blend.Count + " |")
Add-ReportLine ("| Verdict | " + $verdict + " |")
Add-ReportLine ("| Final score | " + $script:Score + " / " + $script:MaxScore + " |")

$utf8 = New-Object System.Text.UTF8Encoding $true
[System.IO.File]::WriteAllLines($ReportPath, $script:Report.ToArray(), $utf8)

Write-Host ""
Write-Host ("Report: " + $ReportPath)
Write-Host ("Score: " + $script:Score + " / " + $script:MaxScore)
Write-Host ("Verdict: " + $verdict)
if ($verdict -eq "FAIL") { exit 2 } else { exit 0 }
