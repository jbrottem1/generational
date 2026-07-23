#Requires -Version 5.1
<#
.SYNOPSIS
  Install Blender (if needed) and run Generational workstation certification on Windows.

.DESCRIPTION
  LOCAL WINDOWS ONLY. Do not run in Cursor cloud VMs.
  - Detects existing Blender installs
  - Installs official BlenderFoundation.Blender via winget when missing
  - Adds Blender directory to the user PATH when needed
  - Runs real Blender scene render probes
  - Runs certify_workstation.ps1

.PARAMETER SkipInstall
  Do not attempt winget install; only detect/configure and certify.

.PARAMETER SkipNetwork
  Passed through to certification (skips git fetch/push dry-run).

.PARAMETER RepoRoot
  Optional Generational repo root.
#>
[CmdletBinding()]
param(
    [switch]$SkipInstall,
    [switch]$SkipNetwork,
    [string]$RepoRoot = "",
    [string]$BlenderExe = ""
)

$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ArtifactDir = Join-Path $ScriptDir "certification_artifacts"
New-Item -ItemType Directory -Force -Path $ArtifactDir | Out-Null
$LogPath = Join-Path $ArtifactDir "install_and_certify.log"

function Write-Log([string]$Message) {
    $line = "[{0}] {1}" -f (Get-Date -Format "o"), $Message
    Write-Host $line
    Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8
}

function Find-BlenderExe {
    param([string]$Explicit)
    if ($Explicit -and (Test-Path -LiteralPath $Explicit)) {
        return (Resolve-Path -LiteralPath $Explicit).Path
    }
    $cmd = Get-Command "blender" -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $roots = @()
    if ($env:ProgramFiles) { $roots += $env:ProgramFiles }
    if (${env:ProgramFiles(x86)}) { $roots += ${env:ProgramFiles(x86)} }
    if ($env:LOCALAPPDATA) { $roots += (Join-Path $env:LOCALAPPDATA "Programs") }

    foreach ($root in $roots) {
        $bf = Join-Path $root "Blender Foundation"
        if (-not (Test-Path -LiteralPath $bf)) { continue }
        $hits = Get-ChildItem -Path $bf -Filter "blender.exe" -Recurse -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending
        if ($hits) { return $hits[0].FullName }
    }

    # winget link location sometimes used
    $wingetLinks = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\blender.exe"
    if (Test-Path -LiteralPath $wingetLinks) { return (Resolve-Path $wingetLinks).Path }

    return $null
}

function Add-UserPath([string]$Directory) {
    if (-not $Directory -or -not (Test-Path -LiteralPath $Directory)) { return $false }
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if (-not $userPath) { $userPath = "" }
    $parts = @($userPath -split ';' | Where-Object { $_ -and $_.Trim() })
    $exists = $false
    foreach ($p in $parts) {
        if ($p.Trim().ToLowerInvariant() -eq $Directory.Trim().ToLowerInvariant()) { $exists = $true; break }
    }
    if (-not $exists) {
        $newPath = ($parts + $Directory) -join ';'
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        Write-Log ("Added to user PATH: {0}" -f $Directory)
    }
    else {
        Write-Log ("Already on user PATH: {0}" -f $Directory)
    }
    # Update current process PATH
    if (($env:Path -split ';') -notcontains $Directory) {
        $env:Path = $env:Path.TrimEnd(';') + ';' + $Directory
    }
    return $true
}

Write-Log "=== Generational LOCAL Windows Blender install + certification ==="
Write-Log ("ScriptDir={0}" -f $ScriptDir)
Write-Log ("Computer={0} User={1}" -f $env:COMPUTERNAME, $env:USERNAME)

# -----------------------------------------------------------------------------
# STEP 1 - Detect Blender
# -----------------------------------------------------------------------------
$blender = Find-BlenderExe -Explicit $BlenderExe
if ($blender) {
    Write-Log ("Blender already installed: {0}" -f $blender)
}
else {
    Write-Log "Blender not found on PATH or under Program Files\Blender Foundation"
}

# -----------------------------------------------------------------------------
# STEP 2 - Install if missing
# -----------------------------------------------------------------------------
$installedThisRun = $false
if (-not $blender -and -not $SkipInstall) {
    $winget = Get-Command "winget" -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Log "Installing official package BlenderFoundation.Blender via winget..."
        $args = @(
            "install", "--exact", "--id", "BlenderFoundation.Blender",
            "--accept-package-agreements", "--accept-source-agreements"
        )
        $p = Start-Process -FilePath $winget.Source -ArgumentList $args -NoNewWindow -PassThru -Wait
        Write-Log ("winget exit code: {0}" -f $p.ExitCode)
        Start-Sleep -Seconds 2
        $blender = Find-BlenderExe -Explicit ""
        if ($blender) {
            $installedThisRun = $true
            Write-Log ("Blender installed: {0}" -f $blender)
        }
        else {
            Write-Log "WARNING: winget finished but blender.exe was not discovered yet."
        }
    }
    else {
        Write-Log "winget is unavailable."
        Write-Log "Manual install required from the official site:"
        Write-Log "  1) Open https://www.blender.org/download/"
        Write-Log "  2) Download the Windows x64 installer from Blender Foundation"
        Write-Log "  3) Install to the default path under C:\Program Files\Blender Foundation\"
        Write-Log "  4) Re-run INSTALL_AND_CERTIFY.bat"
    }
}

if ($blender) {
    $blenderDir = Split-Path -Parent $blender
    [void](Add-UserPath -Directory $blenderDir)

    Write-Log "Verifying blender --version via full path..."
    $ver = & $blender --version 2>&1 | Out-String
    Write-Log $ver.Trim()

    Write-Log "Verifying bpy in background mode..."
    $bpyOut = & $blender --background --python-expr "import bpy; print('BPY_OK=' + bpy.app.version_string)" 2>&1 | Out-String
    Write-Log $bpyOut.Trim()
}
else {
    Write-Log "ERROR: blender.exe still not present. Certification will FAIL on Blender checks."
}

# -----------------------------------------------------------------------------
# STEP 6 - Real Blender scene test (also re-run inside cert script)
# -----------------------------------------------------------------------------
if ($blender) {
    $png = Join-Path $ArtifactDir "blender_verification_frame.png"
    $mp4 = Join-Path $ArtifactDir "blender_verification_animation.mp4"
    $animDir = Join-Path $ArtifactDir "blender_anim_frames"
    $probe = Join-Path $ScriptDir "probe_scene_render.py"
    if (Test-Path -LiteralPath $probe) {
        Write-Log "Running real Blender scene render probe..."
        $env:GENERATIONAL_RENDER_OUT = $png
        $env:GENERATIONAL_ANIM_OUT = $mp4
        $env:GENERATIONAL_ANIM_DIR = $animDir
        $probeOut = & $blender -b --python $probe 2>&1 | Out-String
        Write-Log $probeOut.Trim()
        Write-Log ("PNG exists: {0}" -f (Test-Path -LiteralPath $png))
        Write-Log ("MP4 exists: {0}" -f (Test-Path -LiteralPath $mp4))
        if (Test-Path -LiteralPath $animDir) {
            $frames = @(Get-ChildItem -LiteralPath $animDir -Filter "*.png" -ErrorAction SilentlyContinue)
            Write-Log ("Anim frames: {0}" -f $frames.Count)
        }
    }
    else {
        Write-Log ("Missing probe: {0}" -f $probe)
    }
}

# -----------------------------------------------------------------------------
# STEP 9 - Certification
# -----------------------------------------------------------------------------
$cert = Join-Path $ScriptDir "certify_workstation.ps1"
$certArgs = @()
if ($RepoRoot) { $certArgs += @("-RepoRoot", $RepoRoot) }
if ($blender) { $certArgs += @("-BlenderExe", $blender) }
if ($SkipNetwork) { $certArgs += "-SkipNetwork" }

Write-Log ("Launching certification: {0}" -f $cert)
$certProc = Start-Process -FilePath "powershell.exe" -ArgumentList (
    @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $cert) + $certArgs
) -NoNewWindow -PassThru -Wait
Write-Log ("Certification exit code: {0}" -f $certProc.ExitCode)

$report = Join-Path $ScriptDir "WORKSTATION_CERTIFICATION_REPORT.md"
if (Test-Path -LiteralPath $report) {
    Write-Log ("Report generated: {0}" -f $report)
}
else {
    Write-Log "ERROR: WORKSTATION_CERTIFICATION_REPORT.md was not generated"
}

Write-Log ("InstalledThisRun={0}" -f $installedThisRun)
Write-Log ("BlenderExe={0}" -f $blender)
Write-Log "Done."
exit $certProc.ExitCode
