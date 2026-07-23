# Optional: run from PowerShell as .\CERTIFY.ps1
# Equivalent to CERTIFY.bat
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$here\certify_workstation.ps1" @args
exit $LASTEXITCODE
