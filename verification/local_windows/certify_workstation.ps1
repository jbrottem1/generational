#Requires -Version 5.1
<#
.SYNOPSIS
  Generational local Windows workstation certification audit.

.DESCRIPTION
  Verification-only. Does not modify Generational architecture or production assets.
  Produces WORKSTATION_CERTIFICATION_REPORT.md with PASS or FAIL.

  Run on your LOCAL Windows PC — not inside the Cursor cloud VM.

.PARAMETER RepoRoot
  Path to the Generational repository. Auto-detected when possible.

.PARAMETER BlenderExe
  Optional explicit path to blender.exe.

.PARAMETER SkipNetwork
  Skip GitHub network push/pull probes.
#>
[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [string]$BlenderExe = "",
    [switch]$SkipNetwork
)

$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$OutReport = Join-Path $ScriptDir "WORKSTATION_CERTIFICATION_REPORT.md"
$ArtifactDir = Join-Path $ScriptDir "certification_artifacts"
New-Item -ItemType Directory -Force -Path $ArtifactDir | Out-Null

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
function New-Check {
    param(
        [string]$Domain,
        [string]$Name,
        [ValidateSet("PASS", "FAIL", "WARN", "INFO")][string]$Status,
        [string]$Detail = "",
        [bool]$Blocker = $false
    )
    [pscustomobject]@{
        Domain  = $Domain
        Name    = $Name
        Status  = $Status
        Detail  = $Detail
        Blocker = $Blocker
    }
}

function Invoke-Capture {
    param(
        [string]$FilePath,
        [string[]]$ArgumentList = @(),
        [int]$TimeoutSec = 60
    )
    $stdout = Join-Path $ArtifactDir ("out_" + [guid]::NewGuid().ToString("N") + ".txt")
    $stderr = Join-Path $ArtifactDir ("err_" + [guid]::NewGuid().ToString("N") + ".txt")
    try {
        $p = Start-Process -FilePath $FilePath -ArgumentList $ArgumentList `
            -NoNewWindow -PassThru -Wait `
            -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        $out = ""
        $err = ""
        if (Test-Path $stdout) { $out = Get-Content -Raw -ErrorAction SilentlyContinue $stdout }
        if (Test-Path $stderr) { $err = Get-Content -Raw -ErrorAction SilentlyContinue $stderr }
        return [pscustomobject]@{
            ExitCode = $p.ExitCode
            StdOut   = $out
            StdErr   = $err
            Combined = (($out + "`n" + $err).Trim())
        }
    }
    catch {
        return [pscustomobject]@{
            ExitCode = -1
            StdOut   = ""
            StdErr   = $_.Exception.Message
            Combined = $_.Exception.Message
        }
    }
    finally {
        Remove-Item $stdout, $stderr -ErrorAction SilentlyContinue
    }
}

function Find-CommandPath {
    param([string]$Name)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

function Resolve-RepoRoot {
    param([string]$Hint)
    $candidates = @()
    if ($Hint) { $candidates += $Hint }
    $candidates += (Split-Path -Parent (Split-Path -Parent $ScriptDir))  # .../Generational from verification/local_windows
    $candidates += (Get-Location).Path
    $candidates += "C:\AI\Projects\Generational"
    $candidates += Join-Path $env:USERPROFILE "AI\Projects\Generational"
    $candidates += Join-Path $env:USERPROFILE "Documents\Generational"
    foreach ($c in $candidates) {
        if (-not $c) { continue }
        $app = Join-Path $c "app.py"
        $req = Join-Path $c "requirements.txt"
        if ((Test-Path $app) -and (Test-Path $req)) { return (Resolve-Path $c).Path }
    }
    return $null
}

function Find-BlenderExe {
    param([string]$Explicit)
    if ($Explicit -and (Test-Path $Explicit)) { return (Resolve-Path $Explicit).Path }
    $fromPath = Find-CommandPath "blender"
    if ($fromPath) { return $fromPath }

    $roots = @(
        ${env:ProgramFiles},
        ${env:ProgramFiles(x86)},
        "$env:LOCALAPPDATA\Programs"
    ) | Where-Object { $_ }

    foreach ($root in $roots) {
        $bf = Join-Path $root "Blender Foundation"
        if (-not (Test-Path $bf)) { continue }
        $hits = Get-ChildItem -Path $bf -Filter "blender.exe" -Recurse -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending
        if ($hits) { return $hits[0].FullName }
    }
    return $null
}

$Checks = New-Object System.Collections.Generic.List[object]
$Meta = [ordered]@{
    StartedUtc     = (Get-Date).ToUniversalTime().ToString("o")
    ComputerName   = $env:COMPUTERNAME
    UserName       = $env:USERNAME
    ScriptPath     = $PSCommandPath
    RepoRoot       = $null
    BlenderExe     = $null
    Overall        = "FAIL"
    Score          = 0
}

# -----------------------------------------------------------------------------
# 1. Windows
# -----------------------------------------------------------------------------
try {
    $os = Get-CimInstance Win32_OperatingSystem
    $caption = $os.Caption
    $version = $os.Version
    $build = $os.BuildNumber
    $arch = $os.OSArchitecture
    $Checks.Add((New-Check "Windows" "OS detected" "PASS" "$caption ($arch) version $version build $build"))
    if ($caption -match "Windows 10|Windows 11|Windows Server") {
        $Checks.Add((New-Check "Windows" "Supported Windows family" "PASS" $caption))
    }
    else {
        $Checks.Add((New-Check "Windows" "Supported Windows family" "WARN" "Unexpected OS: $caption"))
    }
}
catch {
    $Checks.Add((New-Check "Windows" "OS detected" "FAIL" $_.Exception.Message -Blocker $true))
}

# -----------------------------------------------------------------------------
# 2. CPU / RAM
# -----------------------------------------------------------------------------
try {
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
    $Checks.Add((New-Check "Hardware" "CPU" "PASS" ("{0} | Cores={1} Logical={2} MaxClockMHz={3}" -f $cpu.Name, $cpu.NumberOfCores, $cpu.NumberOfLogicalProcessors, $cpu.MaxClockSpeed)))
}
catch {
    $Checks.Add((New-Check "Hardware" "CPU" "FAIL" $_.Exception.Message))
}

try {
    $os = Get-CimInstance Win32_OperatingSystem
    $totalGB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
    $freeGB = [math]::Round($os.FreePhysicalMemory / 1MB, 1)
    $status = if ($totalGB -ge 16) { "PASS" } elseif ($totalGB -ge 8) { "WARN" } else { "FAIL" }
    $blocker = $totalGB -lt 8
    $Checks.Add((New-Check "Hardware" "RAM" $status ("Total={0} GB Free={1} GB" -f $totalGB, $freeGB) -Blocker $blocker))
}
catch {
    $Checks.Add((New-Check "Hardware" "RAM" "FAIL" $_.Exception.Message))
}

try {
    $sys = Get-CimInstance Win32_ComputerSystem
    $Checks.Add((New-Check "Hardware" "Machine" "INFO" ("Manufacturer={0} Model={1}" -f $sys.Manufacturer, $sys.Model)))
}
catch { }

# -----------------------------------------------------------------------------
# 3. GPU / NVIDIA / CUDA / OptiX / Vulkan / OpenGL
# -----------------------------------------------------------------------------
$gpuList = @()
try {
    $gpuList = @(Get-CimInstance Win32_VideoController)
    foreach ($g in $gpuList) {
        $vramGB = if ($g.AdapterRAM -and $g.AdapterRAM -gt 0) { [math]::Round($g.AdapterRAM / 1GB, 2) } else { "unknown" }
        $Checks.Add((New-Check "GPU" "Video adapter" "PASS" ("{0} | Driver={1} | AdapterRAM~{2} GB" -f $g.Name, $g.DriverVersion, $vramGB)))
    }
    if (-not $gpuList) {
        $Checks.Add((New-Check "GPU" "Video adapter" "FAIL" "No Win32_VideoController found" -Blocker $true))
    }
}
catch {
    $Checks.Add((New-Check "GPU" "Video adapter" "FAIL" $_.Exception.Message -Blocker $true))
}

$nvidiaSmi = Find-CommandPath "nvidia-smi"
if (-not $nvidiaSmi) {
    $candidate = "C:\Windows\System32\nvidia-smi.exe"
    if (Test-Path $candidate) { $nvidiaSmi = $candidate }
}
if ($nvidiaSmi) {
    $n = Invoke-Capture -FilePath $nvidiaSmi -ArgumentList @("--query-gpu=name,driver_version,memory.total,cuda_version", "--format=csv,noheader")
    if ($n.ExitCode -eq 0 -and $n.Combined) {
        $Checks.Add((New-Check "GPU" "NVIDIA driver / nvidia-smi" "PASS" $n.Combined.Trim()))
    }
    else {
        $Checks.Add((New-Check "GPU" "NVIDIA driver / nvidia-smi" "FAIL" $n.Combined -Blocker $true))
    }
    $n2 = Invoke-Capture -FilePath $nvidiaSmi -ArgumentList @("-L")
    $Checks.Add((New-Check "GPU" "NVIDIA GPU list" $(if ($n2.ExitCode -eq 0) { "PASS" } else { "WARN" }) $n2.Combined.Trim()))
}
else {
    $hasNvidiaName = $gpuList | Where-Object { $_.Name -match "NVIDIA" }
    if ($hasNvidiaName) {
        $Checks.Add((New-Check "GPU" "NVIDIA driver / nvidia-smi" "FAIL" "NVIDIA GPU present but nvidia-smi not found" -Blocker $true))
    }
    else {
        $Checks.Add((New-Check "GPU" "NVIDIA driver / nvidia-smi" "WARN" "nvidia-smi not found (AMD/Intel GPU may still work with HIP/oneAPI)"))
    }
}

# CUDA toolkit probe (optional — Blender often ships its own CUDA/OptiX)
$nvcc = Find-CommandPath "nvcc"
if ($nvcc) {
    $c = Invoke-Capture -FilePath $nvcc -ArgumentList @("--version")
    $Checks.Add((New-Check "Accelerators" "CUDA toolkit (nvcc)" "PASS" ($c.Combined -replace "\s+", " ").Trim()))
}
else {
    $cudaPath = $env:CUDA_PATH
    if ($cudaPath -and (Test-Path $cudaPath)) {
        $Checks.Add((New-Check "Accelerators" "CUDA toolkit" "PASS" "CUDA_PATH=$cudaPath (nvcc not on PATH)"))
    }
    else {
        $Checks.Add((New-Check "Accelerators" "CUDA toolkit (nvcc)" "WARN" "nvcc/CUDA_PATH not found — Blender may still use bundled CUDA kernels if GPU drivers are OK"))
    }
}

# OptiX — typically validated via Blender Cycles devices; check common SDK env
if ($env:OPTIX_ROOT -or $env:OptiX_INSTALL_DIR) {
    $Checks.Add((New-Check "Accelerators" "OptiX SDK env" "PASS" ("OPTIX_ROOT={0} OptiX_INSTALL_DIR={1}" -f $env:OPTIX_ROOT, $env:OptiX_INSTALL_DIR)))
}
else {
    $Checks.Add((New-Check "Accelerators" "OptiX SDK env" "INFO" "No OptiX SDK env vars — OK if Blender reports OPTIX devices"))
}

# Vulkan
$vulkan = Find-CommandPath "vulkaninfo"
if (-not $vulkan) {
    foreach ($p in @(
        "C:\Windows\System32\vulkaninfo.exe",
        "C:\Windows\SysWOW64\vulkaninfo.exe"
    )) { if (Test-Path $p) { $vulkan = $p; break } }
}
if ($vulkan) {
    $v = Invoke-Capture -FilePath $vulkan -ArgumentList @("--summary") -TimeoutSec 45
    $summary = ($v.Combined -split "`n" | Select-Object -First 25) -join " | "
    $ok = ($v.ExitCode -eq 0) -and ($v.Combined -match "GPU|device|Vulkan")
    $Checks.Add((New-Check "Accelerators" "Vulkan" $(if ($ok) { "PASS" } else { "WARN" }) $summary))
}
else {
    $Checks.Add((New-Check "Accelerators" "Vulkan" "WARN" "vulkaninfo not found"))
}

# OpenGL via PowerShell + optional opengl32 (best-effort: use wgl through blender later; here check dll)
$glDll = "C:\Windows\System32\opengl32.dll"
if (Test-Path $glDll) {
    $fi = Get-Item $glDll
    $Checks.Add((New-Check "Accelerators" "OpenGL DLL present" "PASS" ("opengl32.dll LastWrite={0}" -f $fi.LastWriteTime)))
}
else {
    $Checks.Add((New-Check "Accelerators" "OpenGL DLL present" "FAIL" "opengl32.dll missing" -Blocker $true))
}

# -----------------------------------------------------------------------------
# 4. Blender
# -----------------------------------------------------------------------------
$blender = Find-BlenderExe -Explicit $BlenderExe
$Meta.BlenderExe = $blender
$blenderOk = $false
$cyclesGpu = $false

if (-not $blender) {
    $Checks.Add((New-Check "Blender" "Installed" "FAIL" "blender.exe not found on PATH or under Program Files\Blender Foundation" -Blocker $true))
}
else {
    $Checks.Add((New-Check "Blender" "Installed" "PASS" $blender))
    $ver = Invoke-Capture -FilePath $blender -ArgumentList @("--version")
    if ($ver.ExitCode -eq 0 -or $ver.Combined -match "Blender") {
        $line = ($ver.Combined -split "`n" | Select-Object -First 3) -join " "
        $Checks.Add((New-Check "Blender" "Version" "PASS" $line.Trim()))
        $blenderOk = $true
    }
    else {
        $Checks.Add((New-Check "Blender" "Version" "FAIL" $ver.Combined -Blocker $true))
    }

    # Background + bpy
    $bpyPy = Join-Path $ArtifactDir "probe_bpy.py"
    @"
import bpy, sys, json
info = {
    "version": bpy.app.version_string,
    "version_cycle": getattr(bpy.app, "version_cycle", ""),
    "binary_path": bpy.app.binary_path,
    "build_platform": getattr(bpy.app, "build_platform", ""),
}
# Engines
engines = []
try:
    for e in bpy.types.RenderEngine.__subclasses__():
        pass
except Exception:
    pass
engine_ids = []
try:
    # Prefer render.engines enum if available
    rna = bpy.context.scene.render.bl_rna.properties.get("engine")
    if rna and hasattr(rna, "enum_items"):
        engine_ids = [i.identifier for i in rna.enum_items]
except Exception as ex:
    engine_ids = ["error:" + str(ex)]
info["render_engines"] = engine_ids
info["has_cycles"] = any("CYCLES" == e or e.endswith("CYCLES") for e in engine_ids) or "CYCLES" in engine_ids
info["has_eevee"] = any("EEVEE" in e for e in engine_ids)

# Cycles devices
devices = []
try:
    cycles_prefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        cycles_prefs.get_devices()
    except Exception:
        pass
    for d in getattr(cycles_prefs, "devices", []):
        devices.append({
            "name": d.name,
            "type": d.type,
            "use": bool(getattr(d, "use", False)),
        })
    info["cycles_devices"] = devices
    info["cycles_compute_device"] = getattr(cycles_prefs, "compute_device_type", "")
except Exception as ex:
    info["cycles_devices_error"] = str(ex)

print("GENERATIONAL_BLENDER_PROBE=" + json.dumps(info))
"@ | Set-Content -Encoding UTF8 $bpyPy

    $probe = Invoke-Capture -FilePath $blender -ArgumentList @("-b", "--python", $bpyPy) -TimeoutSec 120
    $probeJsonLine = ($probe.Combined -split "`n" | Where-Object { $_ -match "^GENERATIONAL_BLENDER_PROBE=" } | Select-Object -Last 1)
    if ($probeJsonLine) {
        $jsonText = $probeJsonLine -replace "^GENERATIONAL_BLENDER_PROBE=", ""
        try {
            $info = $jsonText | ConvertFrom-Json
            $Checks.Add((New-Check "Blender" "Background launch (-b)" "PASS" ("bpy version {0}" -f $info.version)))
            $Checks.Add((New-Check "Blender" "bpy availability" "PASS" ("binary={0}" -f $info.binary_path)))
            if ($info.has_cycles) {
                $Checks.Add((New-Check "Blender" "Cycles available" "PASS" ("engines: {0}" -f ($info.render_engines -join ", "))))
            }
            else {
                $Checks.Add((New-Check "Blender" "Cycles available" "FAIL" ("engines: {0}" -f ($info.render_engines -join ", ")) -Blocker $true))
            }
            if ($info.has_eevee) {
                $Checks.Add((New-Check "Blender" "Eevee available" "PASS" ("engines: {0}" -f ($info.render_engines -join ", "))))
            }
            else {
                $Checks.Add((New-Check "Blender" "Eevee available" "WARN" ("engines: {0}" -f ($info.render_engines -join ", "))))
            }

            $devs = @($info.cycles_devices)
            if ($devs.Count -gt 0) {
                $devSummary = ($devs | ForEach-Object { "{0}[{1}] use={2}" -f $_.name, $_.type, $_.use }) -join "; "
                $gpuTypes = @($devs | Where-Object { $_.type -match "CUDA|OPTIX|HIP|ONEAPI|METAL" })
                if ($gpuTypes.Count -gt 0) {
                    $cyclesGpu = $true
                    $Checks.Add((New-Check "Blender" "Cycles GPU devices" "PASS" ("compute={0} | {1}" -f $info.cycles_compute_device, $devSummary)))
                    $optix = @($devs | Where-Object { $_.type -eq "OPTIX" })
                    if ($optix.Count -gt 0) {
                        $Checks.Add((New-Check "Accelerators" "OptiX (via Blender Cycles)" "PASS" (($optix | ForEach-Object { $_.name }) -join ", ")))
                    }
                    else {
                        $Checks.Add((New-Check "Accelerators" "OptiX (via Blender Cycles)" "WARN" "No OPTIX device listed — CUDA/HIP may still be usable"))
                    }
                    $cudaDev = @($devs | Where-Object { $_.type -eq "CUDA" })
                    if ($cudaDev.Count -gt 0) {
                        $Checks.Add((New-Check "Accelerators" "CUDA (via Blender Cycles)" "PASS" (($cudaDev | ForEach-Object { $_.name }) -join ", ")))
                    }
                }
                else {
                    $Checks.Add((New-Check "Blender" "Cycles GPU devices" "FAIL" ("Only CPU devices: {0}" -f $devSummary) -Blocker $true))
                }
            }
            else {
                $err = $info.cycles_devices_error
                $Checks.Add((New-Check "Blender" "Cycles GPU devices" "FAIL" ("No devices. {0}" -f $err) -Blocker $true))
            }
            $info | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $ArtifactDir "blender_probe.json")
        }
        catch {
            $Checks.Add((New-Check "Blender" "Background / bpy probe parse" "FAIL" $_.Exception.Message -Blocker $true))
        }
    }
    else {
        $Checks.Add((New-Check "Blender" "Background launch / bpy" "FAIL" $probe.Combined -Blocker $true))
    }

    # One-frame background render (empty scene — verifies render pipeline)
    if ($blenderOk) {
        $frameOut = Join-Path $ArtifactDir "blender_verification_frame.png"
        $renderPy = Join-Path $ArtifactDir "probe_render.py"
        @"
import bpy, os
out = r"$($frameOut -replace '\\','\\')"
bpy.ops.wm.read_factory_settings(use_empty=False)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
try:
    scene.cycles.device = "GPU"
except Exception:
    pass
scene.cycles.samples = 16
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("GENERATIONAL_RENDER_OK=" + out)
print("GENERATIONAL_RENDER_EXISTS=" + str(os.path.exists(out)))
"@ | Set-Content -Encoding UTF8 $renderPy
        $rr = Invoke-Capture -FilePath $blender -ArgumentList @("-b", "--python", $renderPy) -TimeoutSec 300
        if ((Test-Path $frameOut) -and ($rr.Combined -match "GENERATIONAL_RENDER_EXISTS=True")) {
            $Checks.Add((New-Check "Blender" "Background one-frame render" "PASS" $frameOut))
        }
        else {
            $Checks.Add((New-Check "Blender" "Background one-frame render" "FAIL" $rr.Combined -Blocker $true))
        }
    }
}

# -----------------------------------------------------------------------------
# 5. Python
# -----------------------------------------------------------------------------
$py = Find-CommandPath "python"
if (-not $py) { $py = Find-CommandPath "py" }
if ($py) {
    $pv = Invoke-Capture -FilePath $py -ArgumentList @("--version")
    $Checks.Add((New-Check "Python" "Interpreter on PATH" "PASS" ("{0} => {1}" -f $py, $pv.Combined.Trim())))
}
else {
    $Checks.Add((New-Check "Python" "Interpreter on PATH" "WARN" "python/py not on PATH (venv may still exist)"))
}

# -----------------------------------------------------------------------------
# 6. Git
# -----------------------------------------------------------------------------
$git = Find-CommandPath "git"
if (-not $git) {
    $Checks.Add((New-Check "Git" "Installed" "FAIL" "git not on PATH" -Blocker $true))
}
else {
    $gv = Invoke-Capture -FilePath $git -ArgumentList @("--version")
    $Checks.Add((New-Check "Git" "Installed" "PASS" $gv.Combined.Trim()))

    $lfs = Find-CommandPath "git-lfs"
    if (-not $lfs) {
        $lfsProbe = Invoke-Capture -FilePath $git -ArgumentList @("lfs", "version")
        if ($lfsProbe.ExitCode -eq 0) {
            $Checks.Add((New-Check "Git" "Git LFS" "PASS" $lfsProbe.Combined.Trim()))
        }
        else {
            $Checks.Add((New-Check "Git" "Git LFS" "WARN" "git lfs not available — configure before large .blend sync"))
        }
    }
    else {
        $lv = Invoke-Capture -FilePath $lfs -ArgumentList @("version")
        $Checks.Add((New-Check "Git" "Git LFS" "PASS" $lv.Combined.Trim()))
    }
}

$gh = Find-CommandPath "gh"
if ($gh -and -not $SkipNetwork) {
    $auth = Invoke-Capture -FilePath $gh -ArgumentList @("auth", "status")
    if ($auth.Combined -match "Logged in") {
        $Checks.Add((New-Check "Git" "GitHub authentication (gh)" "PASS" (($auth.Combined -split "`n" | Select-Object -First 8) -join " | ")))
    }
    else {
        $Checks.Add((New-Check "Git" "GitHub authentication (gh)" "WARN" $auth.Combined))
    }
}
elseif (-not $SkipNetwork) {
    $Checks.Add((New-Check "Git" "GitHub authentication (gh)" "WARN" "gh CLI not found — will rely on git remote credentials"))
}

# -----------------------------------------------------------------------------
# 7. Generational repository
# -----------------------------------------------------------------------------
$repo = Resolve-RepoRoot -Hint $RepoRoot
$Meta.RepoRoot = $repo

if (-not $repo) {
    $Checks.Add((New-Check "Generational" "Repository location" "FAIL" "Could not find Generational (looked for app.py + requirements.txt). Pass -RepoRoot." -Blocker $true))
}
else {
    $Checks.Add((New-Check "Generational" "Repository location" "PASS" $repo))

    $required = @(
        "app.py", "requirements.txt", "core", "engines", "services", "providers", "ui", "tests", "productions", "data"
    )
    foreach ($rel in $required) {
        $p = Join-Path $repo $rel
        if (Test-Path $p) {
            $Checks.Add((New-Check "Generational" "Path $rel" "PASS" $p))
        }
        else {
            $Checks.Add((New-Check "Generational" "Path $rel" "FAIL" "Missing $p" -Blocker $true))
        }
    }

    # Production / output dirs
    foreach ($rel in @("productions", "productions\scripts", "data\logs", "data\assets", "data\publishing_queue")) {
        $p = Join-Path $repo $rel
        if (Test-Path $p) {
            $Checks.Add((New-Check "Generational" "Output/prod dir $rel" "PASS" $p))
        }
        else {
            $Checks.Add((New-Check "Generational" "Output/prod dir $rel" "WARN" "Missing $p"))
        }
    }

    # Asset discovery
    $blend = @(Get-ChildItem -Path $repo -Filter "*.blend" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 20)
    if ($blend.Count -gt 0) {
        $Checks.Add((New-Check "Generational" "Blender assets (.blend)" "PASS" ("Found {0} (showing up to 20): {1}" -f $blend.Count, (($blend | ForEach-Object FullName) -join "; "))))
    }
    else {
        $Checks.Add((New-Check "Generational" "Blender assets (.blend)" "FAIL" "No .blend files under repo" -Blocker $true))
    }

    $charHits = @(Get-ChildItem -Path $repo -Recurse -ErrorAction SilentlyContinue -Directory |
        Where-Object { $_.Name -match "(?i)character|char_|doctor_001|rig" } |
        Select-Object -First 15)
    if ($charHits.Count -gt 0) {
        $Checks.Add((New-Check "Generational" "Character asset folders" "PASS" (($charHits | ForEach-Object FullName) -join "; ")))
    }
    else {
        $Checks.Add((New-Check "Generational" "Character asset folders" "FAIL" "No character/Doctor_001/rig folders found" -Blocker $true))
    }

    $envHits = @(Get-ChildItem -Path $repo -Recurse -ErrorAction SilentlyContinue -Directory |
        Where-Object { $_.Name -match "(?i)environment|env_|set_|world_|scene_env" } |
        Select-Object -First 15)
    if ($envHits.Count -gt 0) {
        $Checks.Add((New-Check "Generational" "Environment asset folders" "PASS" (($envHits | ForEach-Object FullName) -join "; ")))
    }
    else {
        $Checks.Add((New-Check "Generational" "Environment asset folders" "WARN" "No environment asset folders matched — confirm your asset layout"))
    }

    # Doctor specifically
    $doctor = @(Get-ChildItem -Path $repo -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match "(?i)doctor_001|doctor001|DOCTOR_001" } |
        Select-Object -First 10)
    if ($doctor.Count -gt 0) {
        $Checks.Add((New-Check "Generational" "DOCTOR_001 asset" "PASS" (($doctor | ForEach-Object FullName) -join "; ")))
    }
    else {
        $Checks.Add((New-Check "Generational" "DOCTOR_001 asset" "FAIL" "DOCTOR_001 not found in repository tree" -Blocker $true))
    }

    # Python venv inside repo
    $venvPython = Join-Path $repo "venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $vv = Invoke-Capture -FilePath $venvPython -ArgumentList @("--version")
        $Checks.Add((New-Check "Python" "Generational venv" "PASS" ("{0} => {1}" -f $venvPython, $vv.Combined.Trim())))
        $pip = Invoke-Capture -FilePath $venvPython -ArgumentList @("-m", "pip", "check")
        if ($pip.ExitCode -eq 0) {
            $Checks.Add((New-Check "Python" "Pip package integrity" "PASS" ($pip.Combined.Trim())))
        }
        else {
            $Checks.Add((New-Check "Python" "Pip package integrity" "WARN" $pip.Combined))
        }
        $mods = Invoke-Capture -FilePath $venvPython -ArgumentList @("-c", "import streamlit,openai,dotenv,plotly; print('core-imports-ok')")
        if ($mods.Combined -match "core-imports-ok") {
            $Checks.Add((New-Check "Python" "Core package imports" "PASS" "streamlit, openai, dotenv, plotly"))
        }
        else {
            $Checks.Add((New-Check "Python" "Core package imports" "FAIL" $mods.Combined -Blocker $true))
        }
    }
    else {
        $Checks.Add((New-Check "Python" "Generational venv" "FAIL" "Missing $venvPython — create with: python -m venv venv && venv\Scripts\pip install -r requirements.txt" -Blocker $true))
    }

    # .env
    $envFile = Join-Path $repo ".env"
    if (Test-Path $envFile) {
        $Checks.Add((New-Check "Generational" ".env present" "PASS" $envFile))
    }
    else {
        $Checks.Add((New-Check "Generational" ".env present" "WARN" "Missing .env (copy from .env.example) — live OpenAI stays in Demo Mode"))
    }

    # Git repo probes inside Generational
    if ($git) {
        Push-Location $repo
        try {
            $remote = Invoke-Capture -FilePath $git -ArgumentList @("remote", "-v")
            if ($remote.Combined -match "github.com[:/].*generational") {
                $Checks.Add((New-Check "Git" "Remote origin (generational)" "PASS" (($remote.Combined -split "`n" | Select-Object -First 2) -join " | ")))
            }
            elseif ($remote.Combined -match "origin") {
                $Checks.Add((New-Check "Git" "Remote origin" "WARN" $remote.Combined))
            }
            else {
                $Checks.Add((New-Check "Git" "Remote origin" "FAIL" "No origin remote" -Blocker $true))
            }

            $branch = Invoke-Capture -FilePath $git -ArgumentList @("rev-parse", "--abbrev-ref", "HEAD")
            $status = Invoke-Capture -FilePath $git -ArgumentList @("status", "-sb")
            $Checks.Add((New-Check "Git" "Current branch" "PASS" $branch.Combined.Trim()))
            $Checks.Add((New-Check "Git" "Working tree status" "INFO" $status.Combined.Trim()))

            if (-not $SkipNetwork) {
                $fetch = Invoke-Capture -FilePath $git -ArgumentList @("fetch", "origin")
                if ($fetch.ExitCode -eq 0) {
                    $Checks.Add((New-Check "Git" "Pull/fetch from origin" "PASS" "git fetch origin succeeded"))
                }
                else {
                    $Checks.Add((New-Check "Git" "Pull/fetch from origin" "FAIL" $fetch.Combined -Blocker $true))
                }
                $pushDry = Invoke-Capture -FilePath $git -ArgumentList @("push", "--dry-run", "origin", "HEAD")
                if ($pushDry.ExitCode -eq 0) {
                    $Checks.Add((New-Check "Git" "Push (dry-run)" "PASS" $pushDry.Combined.Trim()))
                }
                else {
                    $Checks.Add((New-Check "Git" "Push (dry-run)" "FAIL" $pushDry.Combined -Blocker $true))
                }
            }
            else {
                $Checks.Add((New-Check "Git" "Network probes" "INFO" "Skipped (-SkipNetwork)"))
            }

            $attr = Join-Path $repo ".gitattributes"
            if (Test-Path $attr) {
                $attrText = Get-Content -Raw $attr
                if ($attrText -match "filter=lfs") {
                    $Checks.Add((New-Check "Git" "LFS tracking configured" "PASS" ".gitattributes contains filter=lfs"))
                }
                else {
                    $Checks.Add((New-Check "Git" "LFS tracking configured" "WARN" ".gitattributes exists but no filter=lfs rules"))
                }
            }
            else {
                $Checks.Add((New-Check "Git" "LFS tracking configured" "WARN" "No .gitattributes — add LFS rules for *.blend / textures / media"))
            }
        }
        finally {
            Pop-Location
        }
    }
}

# -----------------------------------------------------------------------------
# Scoring / verdict
# -----------------------------------------------------------------------------
$passN = @($Checks | Where-Object Status -eq "PASS").Count
$failN = @($Checks | Where-Object Status -eq "FAIL").Count
$warnN = @($Checks | Where-Object Status -eq "WARN").Count
$blockers = @($Checks | Where-Object { $_.Blocker -and $_.Status -eq "FAIL" })
$totalScored = [math]::Max(1, $passN + $failN + $warnN)
$score = [int][math]::Round(100.0 * ($passN + 0.4 * $warnN) / ($passN + $failN + $warnN))
# Hard fail if blockers
if ($blockers.Count -gt 0) {
    $score = [math]::Min($score, 59)
    $Meta.Overall = "FAIL"
}
else {
    $Meta.Overall = "PASS"
    $score = [math]::Max($score, 80)
}
$Meta.Score = $score
$Meta.FinishedUtc = (Get-Date).ToUniversalTime().ToString("o")

# -----------------------------------------------------------------------------
# Write report
# -----------------------------------------------------------------------------
$sb = New-Object System.Text.StringBuilder
function Add-Line([string]$t) { [void]$sb.AppendLine($t) }

Add-Line "# WORKSTATION CERTIFICATION REPORT"
Add-Line ""
Add-Line "| Field | Value |"
Add-Line "|---|---|"
Add-Line ("| **Verdict** | **{0}** |" -f $Meta.Overall)
Add-Line ("| **Environment Score** | **{0} / 100** |" -f $Meta.Score)
Add-Line ("| Computer | {0} |" -f $Meta.ComputerName)
Add-Line ("| User | {0} |" -f $Meta.UserName)
Add-Line ("| Started (UTC) | {0} |" -f $Meta.StartedUtc)
Add-Line ("| Finished (UTC) | {0} |" -f $Meta.FinishedUtc)
Add-Line ("| RepoRoot | {0} |" -f $(if ($Meta.RepoRoot) { $Meta.RepoRoot } else { "(not found)" }))
Add-Line ("| BlenderExe | {0} |" -f $(if ($Meta.BlenderExe) { $Meta.BlenderExe } else { "(not found)" }))
Add-Line "| Audit host | Local Windows (not Cursor cloud) |"
Add-Line ""

if ($Meta.Overall -eq "PASS") {
    Add-Line "## ✅ WORKSTATION CERTIFIED FOR GENERATIONAL PRODUCTION"
}
else {
    Add-Line "## ❌ CERTIFICATION FAILED"
}
Add-Line ""
Add-Line "## Summary counts"
Add-Line ""
Add-Line ("- PASS: **{0}**" -f $passN)
Add-Line ("- FAIL: **{0}**" -f $failN)
Add-Line ("- WARN: **{0}**" -f $warnN)
Add-Line ("- Blockers: **{0}**" -f $blockers.Count)
Add-Line ""

$domains = $Checks | Select-Object -ExpandProperty Domain -Unique
Add-Line "## Domain status"
Add-Line ""
Add-Line "| Domain | Worst status |"
Add-Line "|---|---|"
foreach ($d in $domains) {
    $items = @($Checks | Where-Object Domain -eq $d)
    $worst = "PASS"
    if ($items | Where-Object Status -eq "FAIL") { $worst = "FAIL" }
    elseif ($items | Where-Object Status -eq "WARN") { $worst = "WARN" }
    Add-Line ("| {0} | {1} |" -f $d, $worst)
}
Add-Line ""

Add-Line "## Full checklist"
Add-Line ""
Add-Line "| Domain | Check | Status | Detail |"
Add-Line "|---|---|---|---|"
foreach ($c in $Checks) {
    $detail = ($c.Detail -replace "\|", "/" -replace "`r|`n", " ").Trim()
    if ($detail.Length -gt 220) { $detail = $detail.Substring(0, 217) + "..." }
    Add-Line ("| {0} | {1} | {2} | {3} |" -f $c.Domain, $c.Name, $c.Status, $detail)
}
Add-Line ""

if ($blockers.Count -gt 0) {
    Add-Line "## Required fixes before production"
    Add-Line ""
    $i = 1
    foreach ($b in $blockers) {
        Add-Line ("{0}. **[{1}] {2}** — {3}" -f $i, $b.Domain, $b.Name, $b.Detail)
        $i++
    }
    Add-Line ""
    Add-Line "### Suggested remediation map"
    Add-Line ""
    Add-Line "1. Install **Blender 4.2 LTS+** and ensure `blender.exe` is on PATH or under ``Program Files\Blender Foundation``."
    Add-Line "2. Install current **NVIDIA Studio/Game Ready drivers**; confirm ``nvidia-smi`` works."
    Add-Line "3. In Blender → Edit → Preferences → System → Cycles Render Devices: enable **OptiX** (preferred) or **CUDA**."
    Add-Line "4. Place / sync **DOCTOR_001** and character/environment ``.blend`` assets into the Generational tree (or pass the correct ``-RepoRoot``)."
    Add-Line "5. Create venv: ``python -m venv venv`` then ``venv\Scripts\pip install -r requirements.txt``."
    Add-Line "6. Copy ``.env.example`` → ``.env`` and set keys as needed."
    Add-Line "7. Install **Git LFS** and track ``*.blend``, textures, and large media."
    Add-Line "8. Re-run ``CERTIFY.bat`` until verdict is PASS."
    Add-Line ""
}

Add-Line "## Artifacts"
Add-Line ""
Add-Line ("- Report: ``{0}``" -f $OutReport)
Add-Line ("- Artifact dir: ``{0}``" -f $ArtifactDir)
Add-Line ""
Add-Line "---"
Add-Line ""
if ($Meta.Overall -eq "PASS") {
    Add-Line "**FINAL: PASS**"
    Add-Line ""
    Add-Line "✅ WORKSTATION CERTIFIED FOR GENERATIONAL PRODUCTION"
}
else {
    Add-Line "**FINAL: FAIL**"
    Add-Line ""
    Add-Line "❌ CERTIFICATION FAILED — resolve blockers above and re-run CERTIFY.bat"
}

$sb.ToString() | Set-Content -Encoding UTF8 $OutReport

# Console summary
Write-Host ""
Write-Host "============================================================"
if ($Meta.Overall -eq "PASS") {
    Write-Host " FINAL: PASS  (score $($Meta.Score)/100)" -ForegroundColor Green
    Write-Host " WORKSTATION CERTIFIED FOR GENERATIONAL PRODUCTION" -ForegroundColor Green
}
else {
    Write-Host " FINAL: FAIL  (score $($Meta.Score)/100)" -ForegroundColor Red
    Write-Host " CERTIFICATION FAILED" -ForegroundColor Red
    Write-Host " Blockers:" -ForegroundColor Yellow
    foreach ($b in $blockers) {
        Write-Host ("  - [{0}] {1}: {2}" -f $b.Domain, $b.Name, $b.Detail) -ForegroundColor Yellow
    }
}
Write-Host "============================================================"
Write-Host ("Report: {0}" -f $OutReport)
Write-Host ""

if ($Meta.Overall -eq "PASS") { exit 0 } else { exit 1 }
