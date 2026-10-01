param([switch]$Listen)
$ErrorActionPreference = 'Stop'
$diagnosticPython = Join-Path $PSScriptRoot '.venv\Scripts\pythonw.exe'
if (-not (Test-Path -LiteralPath $diagnosticPython)) { throw 'BM-ICC-08 Python bulunamadi.' }
$previousDiagnostic = $env:BIEM_DMR_DIAGNOSTIC
try {
    # Existing backend limits raw discriminator capture to 120 seconds per session.
    $env:BIEM_DMR_DIAGNOSTIC = '1'
    $diagnosticProject = $PSScriptRoot
    if (Test-Path -LiteralPath 'D:\Projects\Biem\_SDR\data\channels.json') { $diagnosticProject = 'D:\Projects\Biem\_SDR' }
    $env:PYTHONPATH = Join-Path $PSScriptRoot 'src'
    $diagnosticArgs = '-m biem_radia.app --project "' + $diagnosticProject + '"'
    if ($Listen) { $diagnosticArgs += ' --listen' }
    Start-Process -FilePath $diagnosticPython -ArgumentList $diagnosticArgs -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
} finally {
    $env:BIEM_DMR_DIAGNOSTIC = $previousDiagnostic
}
