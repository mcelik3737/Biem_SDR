@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Once Setup-Radia.ps1 dosyasini PowerShell ile calistirin.
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" -m biem_radia.app --project "%~dp0."
