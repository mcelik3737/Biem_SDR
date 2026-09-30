param([Parameter(Mandatory=$true)][string]$ArchivePath)
$ErrorActionPreference = 'Stop'
$radiaPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $radiaPython)) { throw 'Once Setup-Radia.ps1 calistirilmali.' }
& $radiaPython -m biem_radia.map_pack $ArchivePath --project $PSScriptRoot
if ($LASTEXITCODE -ne 0) { throw 'Harita paketi yuklenemedi.' }
Write-Host 'Harita paketi yuklendi. BİEM BM-ICC-08 aciksa yeniden baslatin; Harita listesinden paketi secin.'
