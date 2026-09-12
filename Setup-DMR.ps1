$ErrorActionPreference = 'Stop'
$destination = Join-Path $PSScriptRoot 'vendor\dsd-fme'
$binary = Join-Path $destination 'package\dsd-fme-portable\dsd-fme\dsd-fme.exe'
if (Test-Path -LiteralPath $binary) {
    Write-Host 'DMR decoder mevcut. Kurulum degistirilmedi.'
    return
}
New-Item -ItemType Directory -Force -Path $destination | Out-Null
$archivePath = Join-Path $destination 'portable.zip'
if (-not (Test-Path -LiteralPath $archivePath)) {
    Invoke-WebRequest 'https://github.com/lwvmobile/dsd-fme/releases/download/20260715/dsd-fme-x86-64-cygwin-portable-20260715.zip' -OutFile $archivePath
}
$archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
if ($archiveHash -ne '006CFA420E79033B51DED97ED4D2D0A9715E350FFCFE35C41E89B9E6EF00E9F8') {
    throw 'DMR arsiv ozeti beklenen degerle uyusmuyor.'
}
Expand-Archive -LiteralPath $archivePath -DestinationPath (Join-Path $destination 'package')
if (-not (Test-Path -LiteralPath $binary)) { throw 'DMR decoder bulunamadi.' }
Write-Host 'DMR hazir. SDR# kurulumu ve USB suruculeri degistirilmedi.'
