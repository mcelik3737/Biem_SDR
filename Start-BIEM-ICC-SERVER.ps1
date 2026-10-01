param(
    [string]$Project = '',
    [string]$ListenAddress = '127.0.0.1',
    [int]$Port = 8765,
    [string]$Origin = '',
    [string]$Certificate = '',
    [string]$PrivateKey = ''
)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not $Project) {
    if (Test-Path -LiteralPath 'D:\Projects\Biem\_SDR\data\channels.json') {
        $Project = 'D:\Projects\Biem\_SDR'
    } else {
        $Project = $PSScriptRoot
    }
}
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    Write-Host 'Once bu klasorde uv sync calistirin.'
    exit 1
}
# Run from this checkout, never the original editable install.
$env:PYTHONPATH = Join-Path $PSScriptRoot 'src'
$serverArgs = @('-m', 'biem_radia.server', '--project', $Project, '--host', $ListenAddress, '--port', "$Port", '--open')
if ($Origin) { $serverArgs += @('--origin', $Origin) }
if ($Certificate) { $serverArgs += @('--cert', $Certificate) }
if ($PrivateKey) { $serverArgs += @('--key', $PrivateKey) }
& $python @serverArgs
exit $LASTEXITCODE
