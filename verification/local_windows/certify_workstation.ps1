#Requires -Version 5.1
<#
.SYNOPSIS
  Generational local Windows workstation certification audit.

.DESCRIPTION
  Verification-only. Does not modify Generational architecture or production assets.
  Produces WORKSTATION_CERTIFICATION_REPORT.md with PASS or FAIL.

  Run on your LOCAL Windows PC - not inside the Cursor cloud VM.

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
        [Parameter(Mandatory = $true)][string]$Domain,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][ValidateSet("PASS", "FAIL", "WARN", "INFO")][string]$Status,
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

function Add-Check {
    param(
        [Parameter(Mandatory = $true)]$List,
        [Parameter(Mandatory = $true)][string]$Domain,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][ValidateSet("PASS", "FAIL", "WARN", "INFO")][string]$Status,
        [string]$Detail = "",
        [bool]$Blocker = $false
    )
    $item = New-Check -Domain $Domain -Name $Name -Status $Status -Detail $Detail -Blocker $Blocker
    [void]$List.Add($item)
}

function Invoke-Capture {
    param(
        [string]$FilePath,
        [string[]]$ArgumentList = @(),
        [int]$TimeoutSec = 120,
        [hashtable]$Environment = $null
    )
    $stdout = Join-Path $ArtifactDir ("out_" + [guid]::NewGuid().ToString("N") + ".txt")
    $stderr = Join-Path $ArtifactDir ("err_" + [guid]::NewGuid().ToString("N") + ".txt")
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $FilePath
        # Quote args safely for ProcessStartInfo
        $quoted = @()
        foreach ($a in $ArgumentList) {
            if ($null -eq $a) { continue }
            $s = [string]$a
            if ($s -match '\s') { $quoted += '"' + ($s -replace '"', '\"') + '"' } else { $quoted += $s }
        }
        $psi.Arguments = [string]::Join(" ", $quoted)
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.CreateNoWindow = $true
        if ($Environment) {
            foreach ($key in $Environment.Keys) {
                $psi.EnvironmentVariables[$key] = [string]$Environment[$key]
            }
        }
        $proc = New-Object System.Diagnostics.Process
        $proc.StartInfo = $psi
        [void]$proc.Start()
        $outTask = $proc.StandardOutput.ReadToEndAsync()
        $errTask = $proc.StandardError.ReadToEndAsync()
        if (-not $proc.WaitForExit($TimeoutSec * 1000)) {
            try { $proc.Kill() } catch { }
            return [pscustomobject]@{
                ExitCode = -1
                StdOut   = ""
                StdErr   = "Timed out after $TimeoutSec seconds"
                Combined = "Timed out after $TimeoutSec seconds"
            }
        }
        $out = $outTask.Result
        $err = $errTask.Result
        if ($null -eq $out) { $out = "" }
        if ($null -eq $err) { $err = "" }
        return [pscustomobject]@{
            ExitCode = $proc.ExitCode
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
    $candidates = New-Object System.Collections.Generic.List[string]
    if ($Hint) { [void]$candidates.Add($Hint) }
    [void]$candidates.Add((Split-Path -Parent (Split-Path -Parent $ScriptDir)))
    [void]$candidates.Add((Get-Location).Path)
    [void]$candidates.Add("C:\AI\Projects\Generational")
    if ($env:USERPROFILE) {
        [void]$candidates.Add((Join-Path $env:USERPROFILE "AI\Projects\Generational"))
        [void]$candidates.Add((Join-Path $env:USERPROFILE "Documents\Generational"))
    }
    foreach ($c in $candidates) {
        if (-not $c) { continue }
        $app = Join-Path $c "app.py"
        $req = Join-Path $c "requirements.txt"
        if ((Test-Path -LiteralPath $app) -and (Test-Path -LiteralPath $req)) {
            return (Resolve-Path -LiteralPath $c).Path
        }
    }
    return $null
}

function Find-BlenderExe {
    param([string]$Explicit)
    if ($Explicit -and (Test-Path -LiteralPath $Explicit)) {
        return (Resolve-Path -LiteralPath $Explicit).Path
    }
    $fromPath = Find-CommandPath "blender"
    if ($fromPath) { return $fromPath }

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
    return $null
}

$Checks = New-Object System.Collections.Generic.List[object]
$Meta = @{
    StartedUtc   = (Get-Date).ToUniversalTime().ToString("o")
    ComputerName = $env:COMPUTERNAME
    UserName     = $env:USERNAME
    ScriptPath   = $MyInvocation.MyCommand.Path
    RepoRoot     = $null
    BlenderExe   = $null
    Overall      = "FAIL"
    Score        = 0
}

# -----------------------------------------------------------------------------
# 1. Windows
# -----------------------------------------------------------------------------
try {
    $os = Get-CimInstance Win32_OperatingSystem
    $caption = [string]$os.Caption
    $version = [string]$os.Version
    $build = [string]$os.BuildNumber
    $arch = [string]$os.OSArchitecture
    Add-Check $Checks "Windows" "OS detected" "PASS" ("{0} ({1}) version {2} build {3}" -f $caption, $arch, $version, $build)
    if ($caption -match 'Windows 10|Windows 11|Windows Server') {
        Add-Check $Checks "Windows" "Supported Windows family" "PASS" $caption
    }
    else {
        Add-Check $Checks "Windows" "Supported Windows family" "WARN" ("Unexpected OS: {0}" -f $caption)
    }
}
catch {
    Add-Check $Checks "Windows" "OS detected" "FAIL" $_.Exception.Message $true
}

# -----------------------------------------------------------------------------
# 2. CPU / RAM
# -----------------------------------------------------------------------------
try {
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
    Add-Check $Checks "Hardware" "CPU" "PASS" ("{0} | Cores={1} Logical={2} MaxClockMHz={3}" -f $cpu.Name, $cpu.NumberOfCores, $cpu.NumberOfLogicalProcessors, $cpu.MaxClockSpeed)
}
catch {
    Add-Check $Checks "Hardware" "CPU" "FAIL" $_.Exception.Message
}

try {
    $os = Get-CimInstance Win32_OperatingSystem
    $totalGB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
    $freeGB = [math]::Round($os.FreePhysicalMemory / 1MB, 1)
    $status = "FAIL"
    $blocker = $true
    if ($totalGB -ge 16) { $status = "PASS"; $blocker = $false }
    elseif ($totalGB -ge 8) { $status = "WARN"; $blocker = $false }
    Add-Check $Checks "Hardware" "RAM" $status ("Total={0} GB Free={1} GB" -f $totalGB, $freeGB) $blocker
}
catch {
    Add-Check $Checks "Hardware" "RAM" "FAIL" $_.Exception.Message
}

try {
    $sys = Get-CimInstance Win32_ComputerSystem
    Add-Check $Checks "Hardware" "Machine" "INFO" ("Manufacturer={0} Model={1}" -f $sys.Manufacturer, $sys.Model)
}
catch { }

# -----------------------------------------------------------------------------
# 3. GPU / NVIDIA / CUDA / OptiX / Vulkan / OpenGL
# -----------------------------------------------------------------------------
$gpuList = @()
try {
    $gpuList = @(Get-CimInstance Win32_VideoController)
    foreach ($g in $gpuList) {
        $vramGB = "unknown"
        if ($g.AdapterRAM -and $g.AdapterRAM -gt 0) {
            $vramGB = [math]::Round($g.AdapterRAM / 1GB, 2)
        }
        Add-Check $Checks "GPU" "Video adapter" "PASS" ("{0} | Driver={1} | AdapterRAM~{2} GB" -f $g.Name, $g.DriverVersion, $vramGB)
    }
    if (-not $gpuList -or $gpuList.Count -eq 0) {
        Add-Check $Checks "GPU" "Video adapter" "FAIL" "No Win32_VideoController found" $true
    }
}
catch {
    Add-Check $Checks "GPU" "Video adapter" "FAIL" $_.Exception.Message $true
}

$nvidiaSmi = Find-CommandPath "nvidia-smi"
if (-not $nvidiaSmi) {
    $sysRoot = $env:SystemRoot; if (-not $sysRoot) { $sysRoot = "C:\Windows" }
    $candidate = Join-Path $sysRoot "System32\nvidia-smi.exe"
    if (Test-Path -LiteralPath $candidate) { $nvidiaSmi = $candidate }
}
if ($nvidiaSmi) {
    $n = Invoke-Capture -FilePath $nvidiaSmi -ArgumentList @("--query-gpu=name,driver_version,memory.total,cuda_version", "--format=csv,noheader")
    if ($n.ExitCode -eq 0 -and $n.Combined) {
        Add-Check $Checks "GPU" "NVIDIA driver / nvidia-smi" "PASS" $n.Combined.Trim()
    }
    else {
        Add-Check $Checks "GPU" "NVIDIA driver / nvidia-smi" "FAIL" $n.Combined $true
    }
    $n2 = Invoke-Capture -FilePath $nvidiaSmi -ArgumentList @("-L")
    $n2Status = "WARN"
    if ($n2.ExitCode -eq 0) { $n2Status = "PASS" }
    Add-Check $Checks "GPU" "NVIDIA GPU list" $n2Status $n2.Combined.Trim()
}
else {
    $hasNvidiaName = @($gpuList | Where-Object { $_.Name -match 'NVIDIA' })
    if ($hasNvidiaName.Count -gt 0) {
        Add-Check $Checks "GPU" "NVIDIA driver / nvidia-smi" "FAIL" "NVIDIA GPU present but nvidia-smi not found" $true
    }
    else {
        Add-Check $Checks "GPU" "NVIDIA driver / nvidia-smi" "WARN" "nvidia-smi not found (AMD/Intel GPU may still work with HIP/oneAPI)"
    }
}

$nvcc = Find-CommandPath "nvcc"
if ($nvcc) {
    $c = Invoke-Capture -FilePath $nvcc -ArgumentList @("--version")
    $cText = ($c.Combined -replace '\s+', ' ').Trim()
    Add-Check $Checks "Accelerators" "CUDA toolkit (nvcc)" "PASS" $cText
}
else {
    $cudaPath = $env:CUDA_PATH
    if ($cudaPath -and (Test-Path -LiteralPath $cudaPath)) {
        Add-Check $Checks "Accelerators" "CUDA toolkit" "PASS" ("CUDA_PATH={0} (nvcc not on PATH)" -f $cudaPath)
    }
    else {
        Add-Check $Checks "Accelerators" "CUDA toolkit (nvcc)" "WARN" "nvcc/CUDA_PATH not found - Blender may still use bundled CUDA kernels if GPU drivers are OK"
    }
}

if ($env:OPTIX_ROOT -or $env:OptiX_INSTALL_DIR) {
    Add-Check $Checks "Accelerators" "OptiX SDK env" "PASS" ("OPTIX_ROOT={0} OptiX_INSTALL_DIR={1}" -f $env:OPTIX_ROOT, $env:OptiX_INSTALL_DIR)
}
else {
    Add-Check $Checks "Accelerators" "OptiX SDK env" "INFO" "No OptiX SDK env vars - OK if Blender reports OPTIX devices"
}

$vulkan = Find-CommandPath "vulkaninfo"
if (-not $vulkan) {
    $sysRoot = $env:SystemRoot; if (-not $sysRoot) { $sysRoot = "C:\Windows" }
    $vCandidates = @(
        (Join-Path $sysRoot "System32\vulkaninfo.exe"),
        (Join-Path $sysRoot "SysWOW64\vulkaninfo.exe")
    )
    foreach ($p in $vCandidates) {
        if ($p -and (Test-Path -LiteralPath $p)) { $vulkan = $p; break }
    }
}
if ($vulkan) {
    $v = Invoke-Capture -FilePath $vulkan -ArgumentList @("--summary") -TimeoutSec 45
    $summary = ($v.Combined -split "`n" | Select-Object -First 25) -join " | "
    $ok = ($v.ExitCode -eq 0) -and ($v.Combined -match 'GPU|device|Vulkan')
    $vStatus = "WARN"
    if ($ok) { $vStatus = "PASS" }
    Add-Check $Checks "Accelerators" "Vulkan" $vStatus $summary
}
else {
    Add-Check $Checks "Accelerators" "Vulkan" "WARN" "vulkaninfo not found"
}

$sysRoot = $env:SystemRoot; if (-not $sysRoot) { $sysRoot = "C:\Windows" }
$glDll = Join-Path $sysRoot "System32\opengl32.dll"
if (Test-Path -LiteralPath $glDll) {
    $fi = Get-Item -LiteralPath $glDll
    Add-Check $Checks "Accelerators" "OpenGL DLL present" "PASS" ("opengl32.dll LastWrite={0}" -f $fi.LastWriteTime)
}
else {
    Add-Check $Checks "Accelerators" "OpenGL DLL present" "FAIL" "opengl32.dll missing" $true
}

# -----------------------------------------------------------------------------
# 4. Blender
# -----------------------------------------------------------------------------
$blender = Find-BlenderExe -Explicit $BlenderExe
$Meta.BlenderExe = $blender
$blenderOk = $false

if (-not $blender) {
    Add-Check $Checks "Blender" "Installed" "FAIL" "blender.exe not found on PATH or under Program Files\Blender Foundation" $true
}
else {
    Add-Check $Checks "Blender" "Installed" "PASS" $blender
    $ver = Invoke-Capture -FilePath $blender -ArgumentList @("--version")
    if (($ver.ExitCode -eq 0) -or ($ver.Combined -match 'Blender')) {
        $line = ($ver.Combined -split "`n" | Select-Object -First 3) -join " "
        Add-Check $Checks "Blender" "Version" "PASS" $line.Trim()
        $blenderOk = $true
    }
    else {
        Add-Check $Checks "Blender" "Version" "FAIL" $ver.Combined $true
    }

    $bpyPy = Join-Path $ScriptDir "probe_bpy.py"
    if (-not (Test-Path -LiteralPath $bpyPy)) {
        Add-Check $Checks "Blender" "Background launch / bpy" "FAIL" ("Missing probe script: {0}" -f $bpyPy) $true
    }
    else {
        $probe = Invoke-Capture -FilePath $blender -ArgumentList @("-b", "--python", $bpyPy) -TimeoutSec 120
        $probeJsonLine = $null
        foreach ($line in ($probe.Combined -split "`n")) {
            if ($line -match '^GENERATIONAL_BLENDER_PROBE=') { $probeJsonLine = $line }
        }
        if ($probeJsonLine) {
            $jsonText = $probeJsonLine -replace '^GENERATIONAL_BLENDER_PROBE=', ''
            try {
                $info = $jsonText | ConvertFrom-Json
                Add-Check $Checks "Blender" "Background launch (-b)" "PASS" ("bpy version {0}" -f $info.version)
                Add-Check $Checks "Blender" "bpy availability" "PASS" ("binary={0}" -f $info.binary_path)

                $engineJoin = ""
                if ($info.render_engines) { $engineJoin = [string]::Join(", ", @($info.render_engines)) }

                if ($info.has_cycles) {
                    Add-Check $Checks "Blender" "Cycles available" "PASS" ("engines: {0}" -f $engineJoin)
                }
                else {
                    Add-Check $Checks "Blender" "Cycles available" "FAIL" ("engines: {0}" -f $engineJoin) $true
                }

                if ($info.has_eevee) {
                    Add-Check $Checks "Blender" "Eevee available" "PASS" ("engines: {0}" -f $engineJoin)
                }
                else {
                    Add-Check $Checks "Blender" "Eevee available" "WARN" ("engines: {0}" -f $engineJoin)
                }

                $devs = @($info.cycles_devices)
                if ($devs.Count -gt 0) {
                    $devParts = @()
                    foreach ($d in $devs) {
                        $devParts += ("{0}[{1}] use={2}" -f $d.name, $d.type, $d.use)
                    }
                    $devSummary = [string]::Join("; ", $devParts)
                    $gpuTypes = @($devs | Where-Object { $_.type -match 'CUDA|OPTIX|HIP|ONEAPI|METAL' })
                    if ($gpuTypes.Count -gt 0) {
                        Add-Check $Checks "Blender" "Cycles GPU devices" "PASS" ("compute={0} | {1}" -f $info.cycles_compute_device, $devSummary)
                        $optix = @($devs | Where-Object { $_.type -eq 'OPTIX' })
                        if ($optix.Count -gt 0) {
                            $names = @($optix | ForEach-Object { $_.name })
                            Add-Check $Checks "Accelerators" "OptiX (via Blender Cycles)" "PASS" ([string]::Join(", ", $names))
                        }
                        else {
                            Add-Check $Checks "Accelerators" "OptiX (via Blender Cycles)" "WARN" "No OPTIX device listed - CUDA/HIP may still be usable"
                        }
                        $cudaDev = @($devs | Where-Object { $_.type -eq 'CUDA' })
                        if ($cudaDev.Count -gt 0) {
                            $names = @($cudaDev | ForEach-Object { $_.name })
                            Add-Check $Checks "Accelerators" "CUDA (via Blender Cycles)" "PASS" ([string]::Join(", ", $names))
                        }
                    }
                    else {
                        Add-Check $Checks "Blender" "Cycles GPU devices" "FAIL" ("Only CPU devices: {0}" -f $devSummary) $true
                    }
                }
                else {
                    $err = [string]$info.cycles_devices_error
                    Add-Check $Checks "Blender" "Cycles GPU devices" "FAIL" ("No devices. {0}" -f $err) $true
                }
                $info | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $ArtifactDir "blender_probe.json")
            }
            catch {
                Add-Check $Checks "Blender" "Background / bpy probe parse" "FAIL" $_.Exception.Message $true
            }
        }
        else {
            Add-Check $Checks "Blender" "Background launch / bpy" "FAIL" $probe.Combined $true
        }
    }

    if ($blenderOk) {
        $frameOut = Join-Path $ArtifactDir "blender_verification_frame.png"
        $renderPy = Join-Path $ScriptDir "probe_render.py"
        if (-not (Test-Path -LiteralPath $renderPy)) {
            Add-Check $Checks "Blender" "Background one-frame render" "FAIL" ("Missing probe script: {0}" -f $renderPy) $true
        }
        else {
            $envMap = @{ GENERATIONAL_RENDER_OUT = $frameOut }
            $rr = Invoke-Capture -FilePath $blender -ArgumentList @("-b", "--python", $renderPy) -TimeoutSec 300 -Environment $envMap
            if ((Test-Path -LiteralPath $frameOut) -and ($rr.Combined -match 'GENERATIONAL_RENDER_EXISTS=True')) {
                Add-Check $Checks "Blender" "Background one-frame render" "PASS" $frameOut
            }
            else {
                Add-Check $Checks "Blender" "Background one-frame render" "FAIL" $rr.Combined $true
            }
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
    Add-Check $Checks "Python" "Interpreter on PATH" "PASS" ("{0} => {1}" -f $py, $pv.Combined.Trim())
}
else {
    Add-Check $Checks "Python" "Interpreter on PATH" "WARN" "python/py not on PATH (venv may still exist)"
}

# -----------------------------------------------------------------------------
# 6. Git
# -----------------------------------------------------------------------------
$git = Find-CommandPath "git"
if (-not $git) {
    Add-Check $Checks "Git" "Installed" "FAIL" "git not on PATH" $true
}
else {
    $gv = Invoke-Capture -FilePath $git -ArgumentList @("--version")
    Add-Check $Checks "Git" "Installed" "PASS" $gv.Combined.Trim()

    $lfsProbe = Invoke-Capture -FilePath $git -ArgumentList @("lfs", "version")
    if ($lfsProbe.ExitCode -eq 0) {
        Add-Check $Checks "Git" "Git LFS" "PASS" $lfsProbe.Combined.Trim()
    }
    else {
        Add-Check $Checks "Git" "Git LFS" "WARN" "git lfs not available - configure before large .blend sync"
    }
}

$gh = Find-CommandPath "gh"
if ($gh -and -not $SkipNetwork) {
    $auth = Invoke-Capture -FilePath $gh -ArgumentList @("auth", "status")
    if ($auth.Combined -match 'Logged in') {
        $authSummary = ($auth.Combined -split "`n" | Select-Object -First 8) -join " | "
        Add-Check $Checks "Git" "GitHub authentication (gh)" "PASS" $authSummary
    }
    else {
        Add-Check $Checks "Git" "GitHub authentication (gh)" "WARN" $auth.Combined
    }
}
elseif (-not $SkipNetwork) {
    Add-Check $Checks "Git" "GitHub authentication (gh)" "WARN" "gh CLI not found - will rely on git remote credentials"
}

# -----------------------------------------------------------------------------
# 7. Generational repository
# -----------------------------------------------------------------------------
$repo = Resolve-RepoRoot -Hint $RepoRoot
$Meta.RepoRoot = $repo

if (-not $repo) {
    Add-Check $Checks "Generational" "Repository location" "FAIL" "Could not find Generational (looked for app.py + requirements.txt). Pass -RepoRoot." $true
}
else {
    Add-Check $Checks "Generational" "Repository location" "PASS" $repo

    $required = @(
        "app.py", "requirements.txt", "core", "engines", "services", "providers",
        "ui", "tests", "productions", "data"
    )
    foreach ($rel in $required) {
        $p = Join-Path $repo $rel
        if (Test-Path -LiteralPath $p) {
            Add-Check $Checks "Generational" ("Path {0}" -f $rel) "PASS" $p
        }
        else {
            Add-Check $Checks "Generational" ("Path {0}" -f $rel) "FAIL" ("Missing {0}" -f $p) $true
        }
    }

    foreach ($rel in @("productions", "productions\scripts", "data\logs", "data\assets", "data\publishing_queue")) {
        $p = Join-Path $repo $rel
        if (Test-Path -LiteralPath $p) {
            Add-Check $Checks "Generational" ("Output/prod dir {0}" -f $rel) "PASS" $p
        }
        else {
            Add-Check $Checks "Generational" ("Output/prod dir {0}" -f $rel) "WARN" ("Missing {0}" -f $p)
        }
    }

    $blend = @(Get-ChildItem -Path $repo -Filter "*.blend" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 20)
    if ($blend.Count -gt 0) {
        $paths = @($blend | ForEach-Object { $_.FullName })
        Add-Check $Checks "Generational" "Blender assets (.blend)" "PASS" ("Found {0}: {1}" -f $blend.Count, ([string]::Join("; ", $paths)))
    }
    else {
        Add-Check $Checks "Generational" "Blender assets (.blend)" "FAIL" "No .blend files under repo" $true
    }

    $charHits = @(Get-ChildItem -Path $repo -Recurse -ErrorAction SilentlyContinue -Directory |
        Where-Object { $_.Name -match '(?i)character|char_|doctor_001|rig' } |
        Select-Object -First 15)
    if ($charHits.Count -gt 0) {
        $paths = @($charHits | ForEach-Object { $_.FullName })
        Add-Check $Checks "Generational" "Character asset folders" "PASS" ([string]::Join("; ", $paths))
    }
    else {
        Add-Check $Checks "Generational" "Character asset folders" "FAIL" "No character/Doctor_001/rig folders found" $true
    }

    $envHits = @(Get-ChildItem -Path $repo -Recurse -ErrorAction SilentlyContinue -Directory |
        Where-Object { $_.Name -match '(?i)environment|env_|set_|world_|scene_env' } |
        Select-Object -First 15)
    if ($envHits.Count -gt 0) {
        $paths = @($envHits | ForEach-Object { $_.FullName })
        Add-Check $Checks "Generational" "Environment asset folders" "PASS" ([string]::Join("; ", $paths))
    }
    else {
        Add-Check $Checks "Generational" "Environment asset folders" "WARN" "No environment asset folders matched - confirm your asset layout"
    }

    $doctor = @(Get-ChildItem -Path $repo -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '(?i)doctor_001|doctor001|DOCTOR_001' } |
        Select-Object -First 10)
    if ($doctor.Count -gt 0) {
        $paths = @($doctor | ForEach-Object { $_.FullName })
        Add-Check $Checks "Generational" "DOCTOR_001 asset" "PASS" ([string]::Join("; ", $paths))
    }
    else {
        Add-Check $Checks "Generational" "DOCTOR_001 asset" "FAIL" "DOCTOR_001 not found in repository tree" $true
    }

    $venvPython = Join-Path $repo "venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $venvPython) {
        $vv = Invoke-Capture -FilePath $venvPython -ArgumentList @("--version")
        Add-Check $Checks "Python" "Generational venv" "PASS" ("{0} => {1}" -f $venvPython, $vv.Combined.Trim())
        $pip = Invoke-Capture -FilePath $venvPython -ArgumentList @("-m", "pip", "check")
        if ($pip.ExitCode -eq 0) {
            Add-Check $Checks "Python" "Pip package integrity" "PASS" $pip.Combined.Trim()
        }
        else {
            Add-Check $Checks "Python" "Pip package integrity" "WARN" $pip.Combined
        }
        $mods = Invoke-Capture -FilePath $venvPython -ArgumentList @("-c", "import streamlit,openai,dotenv,plotly; print('core-imports-ok')")
        if ($mods.Combined -match 'core-imports-ok') {
            Add-Check $Checks "Python" "Core package imports" "PASS" "streamlit, openai, dotenv, plotly"
        }
        else {
            Add-Check $Checks "Python" "Core package imports" "FAIL" $mods.Combined $true
        }
    }
    else {
        Add-Check $Checks "Python" "Generational venv" "FAIL" ("Missing {0} - create with: python -m venv venv && venv\Scripts\pip install -r requirements.txt" -f $venvPython) $true
    }

    $envFile = Join-Path $repo ".env"
    if (Test-Path -LiteralPath $envFile) {
        Add-Check $Checks "Generational" ".env present" "PASS" $envFile
    }
    else {
        Add-Check $Checks "Generational" ".env present" "WARN" "Missing .env (copy from .env.example) - live OpenAI stays in Demo Mode"
    }

    if ($git) {
        Push-Location $repo
        try {
            $remote = Invoke-Capture -FilePath $git -ArgumentList @("remote", "-v")
            if ($remote.Combined -match 'github.com[:/].*generational') {
                $remoteSummary = ($remote.Combined -split "`n" | Select-Object -First 2) -join " | "
                Add-Check $Checks "Git" "Remote origin (generational)" "PASS" $remoteSummary
            }
            elseif ($remote.Combined -match 'origin') {
                Add-Check $Checks "Git" "Remote origin" "WARN" $remote.Combined
            }
            else {
                Add-Check $Checks "Git" "Remote origin" "FAIL" "No origin remote" $true
            }

            $branch = Invoke-Capture -FilePath $git -ArgumentList @("rev-parse", "--abbrev-ref", "HEAD")
            $status = Invoke-Capture -FilePath $git -ArgumentList @("status", "-sb")
            Add-Check $Checks "Git" "Current branch" "PASS" $branch.Combined.Trim()
            Add-Check $Checks "Git" "Working tree status" "INFO" $status.Combined.Trim()

            if (-not $SkipNetwork) {
                $fetch = Invoke-Capture -FilePath $git -ArgumentList @("fetch", "origin")
                if ($fetch.ExitCode -eq 0) {
                    Add-Check $Checks "Git" "Pull/fetch from origin" "PASS" "git fetch origin succeeded"
                }
                else {
                    Add-Check $Checks "Git" "Pull/fetch from origin" "FAIL" $fetch.Combined $true
                }
                $pushDry = Invoke-Capture -FilePath $git -ArgumentList @("push", "--dry-run", "origin", "HEAD")
                if ($pushDry.ExitCode -eq 0) {
                    Add-Check $Checks "Git" "Push (dry-run)" "PASS" $pushDry.Combined.Trim()
                }
                else {
                    Add-Check $Checks "Git" "Push (dry-run)" "FAIL" $pushDry.Combined $true
                }
            }
            else {
                Add-Check $Checks "Git" "Network probes" "INFO" "Skipped (-SkipNetwork)"
            }

            $attr = Join-Path $repo ".gitattributes"
            if (Test-Path -LiteralPath $attr) {
                $attrText = Get-Content -Raw -LiteralPath $attr
                if ($attrText -match 'filter=lfs') {
                    Add-Check $Checks "Git" "LFS tracking configured" "PASS" ".gitattributes contains filter=lfs"
                }
                else {
                    Add-Check $Checks "Git" "LFS tracking configured" "WARN" ".gitattributes exists but no filter=lfs rules"
                }
            }
            else {
                Add-Check $Checks "Git" "LFS tracking configured" "WARN" "No .gitattributes - add LFS rules for *.blend / textures / media"
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
$passN = @($Checks | Where-Object { $_.Status -eq "PASS" }).Count
$failN = @($Checks | Where-Object { $_.Status -eq "FAIL" }).Count
$warnN = @($Checks | Where-Object { $_.Status -eq "WARN" }).Count
$blockers = @($Checks | Where-Object { $_.Blocker -and $_.Status -eq "FAIL" })
$denom = [math]::Max(1, ($passN + $failN + $warnN))
$score = [int][math]::Round(100.0 * (($passN + (0.4 * $warnN)) / $denom))
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
# Write report (ASCII-safe markers for Windows PowerShell 5.1)
# -----------------------------------------------------------------------------
$lines = New-Object System.Collections.Generic.List[string]
function Add-ReportLine { param([string]$Text) [void]$script:lines.Add($Text) }

Add-ReportLine "# WORKSTATION CERTIFICATION REPORT"
Add-ReportLine ""
Add-ReportLine "| Field | Value |"
Add-ReportLine "|---|---|"
Add-ReportLine ("| **Verdict** | **{0}** |" -f $Meta.Overall)
Add-ReportLine ("| **Environment Score** | **{0} / 100** |" -f $Meta.Score)
Add-ReportLine ("| Computer | {0} |" -f $Meta.ComputerName)
Add-ReportLine ("| User | {0} |" -f $Meta.UserName)
Add-ReportLine ("| Started (UTC) | {0} |" -f $Meta.StartedUtc)
Add-ReportLine ("| Finished (UTC) | {0} |" -f $Meta.FinishedUtc)
if ($Meta.RepoRoot) { L ("| RepoRoot | {0} |" -f $Meta.RepoRoot) } else { L "| RepoRoot | (not found) |" }
if ($Meta.BlenderExe) { L ("| BlenderExe | {0} |" -f $Meta.BlenderExe) } else { L "| BlenderExe | (not found) |" }
Add-ReportLine "| Audit host | Local Windows (not Cursor cloud) |"
Add-ReportLine ""

if ($Meta.Overall -eq "PASS") {
    Add-ReportLine "## [PASS] WORKSTATION CERTIFIED FOR GENERATIONAL PRODUCTION"
}
else {
    Add-ReportLine "## [FAIL] CERTIFICATION FAILED"
}
Add-ReportLine ""
Add-ReportLine "## Summary counts"
Add-ReportLine ""
Add-ReportLine ("* PASS: **{0}**" -f $passN)
Add-ReportLine ("* FAIL: **{0}**" -f $failN)
Add-ReportLine ("* WARN: **{0}**" -f $warnN)
Add-ReportLine ("* Blockers: **{0}**" -f $blockers.Count)
Add-ReportLine ""

$domains = @($Checks | Select-Object -ExpandProperty Domain -Unique)
Add-ReportLine "## Domain status"
Add-ReportLine ""
Add-ReportLine "| Domain | Worst status |"
Add-ReportLine "|---|---|"
foreach ($d in $domains) {
    $items = @($Checks | Where-Object { $_.Domain -eq $d })
    $worst = "PASS"
    if (@($items | Where-Object { $_.Status -eq "FAIL" }).Count -gt 0) { $worst = "FAIL" }
    elseif (@($items | Where-Object { $_.Status -eq "WARN" }).Count -gt 0) { $worst = "WARN" }
    Add-ReportLine ("| {0} | {1} |" -f $d, $worst)
}
Add-ReportLine ""

Add-ReportLine "## Full checklist"
Add-ReportLine ""
Add-ReportLine "| Domain | Check | Status | Detail |"
Add-ReportLine "|---|---|---|---|"
foreach ($c in $Checks) {
    $detail = ([string]$c.Detail) -replace '\|', '/' -replace "[`r`n]", " "
    $detail = $detail.Trim()
    if ($detail.Length -gt 220) { $detail = $detail.Substring(0, 217) + "..." }
    Add-ReportLine ("| {0} | {1} | {2} | {3} |" -f $c.Domain, $c.Name, $c.Status, $detail)
}
Add-ReportLine ""

if ($blockers.Count -gt 0) {
    Add-ReportLine "## Required fixes before production"
    Add-ReportLine ""
    $i = 1
    foreach ($b in $blockers) {
        Add-ReportLine ("{0}. **[{1}] {2}** - {3}" -f $i, $b.Domain, $b.Name, $b.Detail)
        $i++
    }
    Add-ReportLine ""
    Add-ReportLine "### Suggested remediation map"
    Add-ReportLine ""
    Add-ReportLine "1. Install Blender 4.2 LTS+ and ensure blender.exe is on PATH or under Program Files\Blender Foundation."
    Add-ReportLine "2. Install current NVIDIA Studio/Game Ready drivers; confirm nvidia-smi works."
    Add-ReportLine "3. In Blender -> Edit -> Preferences -> System -> Cycles Render Devices: enable OptiX (preferred) or CUDA."
    Add-ReportLine "4. Place / sync DOCTOR_001 and character/environment .blend assets into the Generational tree (or pass -RepoRoot)."
    Add-ReportLine "5. Create venv: python -m venv venv then venv\Scripts\pip install -r requirements.txt."
    Add-ReportLine "6. Copy .env.example to .env and set keys as needed."
    Add-ReportLine "7. Install Git LFS and track *.blend, textures, and large media."
    Add-ReportLine "8. Re-run CERTIFY.bat until verdict is PASS."
    Add-ReportLine ""
}

Add-ReportLine "## Artifacts"
Add-ReportLine ""
Add-ReportLine ("Report: {0}" -f $OutReport)
Add-ReportLine ("Artifact dir: {0}" -f $ArtifactDir)
Add-ReportLine ""
Add-ReportLine "---"
Add-ReportLine ""
if ($Meta.Overall -eq "PASS") {
    Add-ReportLine "**FINAL: PASS**"
    Add-ReportLine ""
    Add-ReportLine "[PASS] WORKSTATION CERTIFIED FOR GENERATIONAL PRODUCTION"
}
else {
    Add-ReportLine "**FINAL: FAIL**"
    Add-ReportLine ""
    Add-ReportLine "[FAIL] CERTIFICATION FAILED - resolve blockers above and re-run CERTIFY.bat"
}

# Write UTF-8 with BOM for Windows PowerShell 5.1 compatibility on next edit cycles
$utf8Bom = New-Object System.Text.UTF8Encoding $true
[System.IO.File]::WriteAllLines($OutReport, $lines, $utf8Bom)

Write-Host ""
Write-Host "============================================================"
if ($Meta.Overall -eq "PASS") {
    Write-Host (" FINAL: PASS  (score {0}/100)" -f $Meta.Score) -ForegroundColor Green
    Write-Host " WORKSTATION CERTIFIED FOR GENERATIONAL PRODUCTION" -ForegroundColor Green
}
else {
    Write-Host (" FINAL: FAIL  (score {0}/100)" -f $Meta.Score) -ForegroundColor Red
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
