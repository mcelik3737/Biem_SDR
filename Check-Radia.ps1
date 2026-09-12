$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$checks = @(
    @('ruff', 'check', 'src', 'tests'),
    @('ruff', 'format', '--check', 'src', 'tests'),
    @('ty', 'check'),
    @('basedpyright'),
    @('pytest', '-q', '--cov=biem_radia', '--cov-branch')
)
foreach ($check in $checks) {
    & python -m uv run @check
    if ($LASTEXITCODE -ne 0) { throw "Kontrol basarisiz: $($check -join ' ')" }
}
