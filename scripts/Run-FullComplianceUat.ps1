# Run all four UAT phases — build guard-test.exe first.
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root
$Ledger = Join-Path $Root "compliance-ledger"
New-Item -ItemType Directory -Force -Path $Ledger | Out-Null
$fail = 0

Write-Host "=== Building guard-test.exe ==="
dotnet build (Join-Path $Root "src/VAIntage.Guard.TestCli") -c Release
$GuardTest = Join-Path $Root "src/VAIntage.Guard.TestCli/bin/Release/net8.0/guard-test.exe"
$env:GUARD_TEST_EXE = $GuardTest

Write-Host "`n=== Phase 1 (C# xUnit) — client-side scrubbing + SHA-256 attestation ==="
try {
    dotnet test (Join-Path $Root "phase1/VAIntage.Phase1.Scrubbing.Tests") --verbosity minimal
} catch { $fail = 1; Write-Warning $_ }

Write-Host "`n=== Phase 2 (Python) — ZDR API configuration via guard-test config ==="
try {
    if (Test-Path ".venv/Scripts/Activate.ps1") { . .venv/Scripts/Activate.ps1 }
    pip install -q -e ".[dev]"
    $env:PYTHONPATH = "phase2"
    python -m pytest phase2/tests/ -q
} catch { $fail = 1; Write-Warning $_ }

Write-Host "`n=== Phase 3 (PowerShell) — disk audit via guard-test simulate ==="
try {
    & (Join-Path $Root "phase3/Run-DiskAudit.ps1") -NoteCount 1000 -GuardTestExe $GuardTest
} catch { $fail = 1; Write-Warning $_ }

Write-Host "`n=== Phase 4 (C# xUnit) — compliance drawer vaporization (production GC path) ==="
try {
    dotnet test (Join-Path $Root "phase4/VAIntage.Phase4.Vaporization.Tests") --verbosity minimal
} catch { $fail = 1; Write-Warning $_ }

$summary = @{
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    guard_test_exe = $GuardTest
    artifacts = @(Get-ChildItem $Ledger -File | Where-Object { $_.Name -ne ".gitkeep" } | ForEach-Object { $_.Name })
    status = if ($fail -eq 0) { "PASS" } else { "FAIL" }
}
$summaryPath = Join-Path $Ledger "certification-summary.json"
$summary | ConvertTo-Json -Depth 4 | Set-Content $summaryPath -Encoding UTF8
Write-Host "`nCertification summary -> $summaryPath"
if ($fail -ne 0) { exit 1 }
