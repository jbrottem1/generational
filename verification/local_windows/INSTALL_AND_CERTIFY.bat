@echo off
REM =============================================================================
REM Generational - Install Blender (if needed) + run local workstation certification
REM LOCAL WINDOWS PC ONLY - do not run in Cursor cloud VM
REM =============================================================================
setlocal
cd /d "%~dp0"

echo.
echo  GENERATIONAL - INSTALL BLENDER + CERTIFY WORKSTATION
echo  Local Windows only
echo.

where powershell >nul 2>&1
if errorlevel 1 (
  echo ERROR: PowerShell not found.
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_and_certify.ps1" %*
set EXITCODE=%ERRORLEVEL%

echo.
if exist "%~dp0WORKSTATION_CERTIFICATION_REPORT.md" (
  echo Report: %~dp0WORKSTATION_CERTIFICATION_REPORT.md
) else (
  echo Report was not generated.
)

exit /b %EXITCODE%
