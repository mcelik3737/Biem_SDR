$ErrorActionPreference = 'Stop'
$radiaPython = Join-Path $PSScriptRoot '.venv\Scripts\pythonw.exe'
if (-not (Test-Path -LiteralPath $radiaPython)) { throw 'Once Setup-Radia.ps1 calistirilmali.' }
$radiaProject = $PSScriptRoot
if (Test-Path -LiteralPath 'D:\Projects\Biem\_SDR\data\channels.json') { $radiaProject = 'D:\Projects\Biem\_SDR' }
$env:PYTHONPATH = Join-Path $PSScriptRoot 'src'
$radiaArgs = '-m biem_radia.app --project "' + $radiaProject + '"'
Start-Process -FilePath $radiaPython -ArgumentList $radiaArgs -WorkingDirectory $PSScriptRoot -Verb RunAs -WindowStyle Hidden
