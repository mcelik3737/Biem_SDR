$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
python -m uv sync --locked
if ($LASTEXITCODE -ne 0) { throw 'uv sync basarisiz. python -m pip install uv ile uv kurun.' }
$destination = Join-Path $PSScriptRoot 'vendor\rtl-sdr'
if (-not (Test-Path (Join-Path $destination 'package\x64\rtlsdr.dll'))) {
    New-Item -ItemType Directory -Force $destination | Out-Null
    Invoke-WebRequest 'https://github.com/rtlsdrblog/rtl-sdr-blog/releases/download/V1.4.0/Release.zip' -OutFile (Join-Path $destination 'Release.zip')
    $archiveHash = (Get-FileHash (Join-Path $destination 'Release.zip') -Algorithm SHA256).Hash
    if ($archiveHash -ne '7EF33F1304647F65E5E0FDE43637A73D54F076E91E651A3CECC4F55A17FD9815') { throw 'RTL-SDR arsiv ozeti beklenen degerle uyusmuyor.' }
    Expand-Archive (Join-Path $destination 'Release.zip') (Join-Path $destination 'package')
}
Write-Host 'Hazir. Start-Radia.cmd ile uygulamayi acin.'
