@echo off
REM =============================================================================
REM Generational - ONE-COMMAND Local Windows Workstation Certification
REM Run this on your PC (PowerShell / CMD). Do NOT run in Cursor cloud.
REM =============================================================================
setlocal
cd /d "%~dp0"

echo.
echo  GENERATIONAL WORKSTATION CERTIFICATION
echo  Local Windows audit only - not the Cursor cloud VM
echo.

where powershell >nul 2>&1
if errorlevel 1 (
  echo ERROR: PowerShell not found. Install Windows PowerShell 5.1+ or PowerShell 7+.
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0certify_workstation.ps1" %*
set EXITCODE=%ERRORLEVEL%

echo.
if exist "%~dp0WORKSTATION_CERTIFICATION_REPORT.md" (
  echo Report: %~dp0WORKSTATION_CERTIFICATION_REPORT.md
) else (
  echo Report was not generated.
)

exit /b %EXITCODE%
