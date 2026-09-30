param([string]$SdrDirectory = 'D:\Depo\SDR\sdr-install\sdrsharp')
$ErrorActionPreference = 'Stop'
$destination = Join-Path $PSScriptRoot 'vendor\tetra'
New-Item -ItemType Directory -Force -Path $destination | Out-Null
foreach ($name in @('SDRSharp.Radio.dll','SDRSharp.Common.dll','SDRSharp.Tetra.dll','tetraVoiceDec.dll','shark.dll')) {
    $source = Join-Path $SdrDirectory $name
    if (-not (Test-Path -LiteralPath $source)) { throw "TETRA bagimliligi bulunamadi: $source" }
    Copy-Item -LiteralPath $source -Destination (Join-Path $destination $name)
}
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe'
& $compiler /nologo /unsafe /platform:x86 /r:System.Web.Extensions.dll ('/out:' + (Join-Path $destination 'TetraBridge.exe')) (Join-Path $PSScriptRoot 'native\TetraBridge.cs')
if ($LASTEXITCODE -ne 0) { throw 'TETRA bridge derlenemedi.' }
Get-ChildItem -LiteralPath $destination -Filter '*.dll' | Get-FileHash -Algorithm SHA256 | Select-Object Path,Hash | ConvertTo-Json | Set-Content (Join-Path $destination 'manifest.json')
Write-Host 'TETRA yerel adaptoru hazir. SDR# kaynak kurulumu degistirilmedi.'
