@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Once Setup-Radia.ps1 dosyasini PowerShell ile calistirin.
  pause
  exit /b 1
)
set "BIEM_PROJECT=%~dp0."
if exist "D:\Projects\Biem\_SDR\data\channels.json" set "BIEM_PROJECT=D:\Projects\Biem\_SDR"
set "PYTHONPATH=%~dp0src"
start "" ".venv\Scripts\pythonw.exe" -m biem_radia.app --project "%BIEM_PROJECT%"

