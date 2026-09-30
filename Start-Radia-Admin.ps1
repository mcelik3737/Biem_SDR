$ErrorActionPreference = 'Stop'
$radiaPython = Join-Path $PSScriptRoot '.venv\Scripts\pythonw.exe'
if (-not (Test-Path -LiteralPath $radiaPython)) { throw 'Once Setup-Radia.ps1 calistirilmali.' }
$radiaArgs = '-m biem_radia.app --project "' + $PSScriptRoot + '"'
Start-Process -FilePath $radiaPython -ArgumentList $radiaArgs -WorkingDirectory $PSScriptRoot -Verb RunAs -WindowStyle Hidden
