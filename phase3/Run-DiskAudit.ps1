# Phase 3 — Negative log network inspection (PowerShell).
# Calls guard-test.exe simulate (1000 notes) and watch-paths; scans disk for clinical keywords.
#
# Usage:
#   .\phase3\Run-DiskAudit.ps1
#   .\phase3\Run-DiskAudit.ps1 -NoteCount 1000 -GuardTestExe "path\to\guard-test.exe"

param(
    [string[]]$Keywords = @("substance", "anxiety", "transportation", "methadone", "counseling"),
    [int]$NoteCount = 1000,
    [string]$LedgerDir = "compliance-ledger",
    [string]$Output = "disk-audit-manifest.json",
    [string]$GuardTestExe = $env:GUARD_TEST_EXE
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent

function Resolve-GuardTestExe {
    param([string]$Override)
    if ($Override -and (Test-Path $Override)) { return (Resolve-Path $Override).Path }
    $candidates = @(
        (Join-Path $RepoRoot "scripts/guard-test-mac.sh"),
        (Join-Path $RepoRoot "src/VAIntage.Guard.TestCli/bin/Release/net8.0/guard-test.exe"),
        (Join-Path $RepoRoot "src/VAIntage.Guard.TestCli/bin/Release/net8.0/guard-test"),
        (Join-Path $RepoRoot "src/VAIntage.Guard.TestCli/bin/Debug/net8.0/guard-test.exe"),
        (Join-Path $RepoRoot "src/VAIntage.Guard.TestCli/bin/Debug/net8.0/guard-test")
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { return (Resolve-Path $c).Path }
    }
    throw "guard-test not found. Run: dotnet build src/VAIntage.Guard.TestCli -c Release"
}

function Invoke-GuardTest {
    param([string]$Exe, [string[]]$GuardArgs)
    if ($Exe -match '\.(sh|bash)$') {
        $out = & bash $Exe @GuardArgs 2>&1
    } else {
        $out = & $Exe @GuardArgs 2>&1
    }
    if ($LASTEXITCODE -ne 0) { throw "guard-test failed: $out" }
    return ($out | Out-String).Trim()
}

$guardTest = Resolve-GuardTestExe -Override $GuardTestExe
Write-Host "Using guard-test: $guardTest"

$watchJson = Invoke-GuardTest -Exe $guardTest -GuardArgs @("watch-paths")
$WatchPaths = @($watchJson | ConvertFrom-Json) | Where-Object { $_ -and (Test-Path $_ -PathType Container -ErrorAction SilentlyContinue) }

function Get-FileInventory($paths) {
    $files = @{}
    foreach ($root in $paths) {
        Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
            $files[$_.FullName] = $_.LastWriteTimeUtc.Ticks
        }
    }
    return $files
}

Write-Host "Phase 3 — snapshot before guard-test simulate..."
$before = Get-FileInventory $WatchPaths

Write-Host "Invoking guard-test simulate --count $NoteCount ..."
$simJson = Invoke-GuardTest -Exe $guardTest -GuardArgs @("simulate", "--count", "$NoteCount")
$sim = $simJson | ConvertFrom-Json

Write-Host "Phase 3 — snapshot after typing simulation..."
$after = Get-FileInventory $WatchPaths

$newFiles = $after.Keys | Where-Object { -not $before.ContainsKey($_) }
$textExt = @(".log", ".txt", ".json", ".db", ".sqlite", ".cache", ".md")
$hits = @{}
foreach ($kw in $Keywords) { $hits[$kw] = 0 }
$scanned = 0

foreach ($path in $newFiles) {
    $ext = [System.IO.Path]::GetExtension($path).ToLowerInvariant()
    if ($textExt -notcontains $ext) { continue }
    try {
        $content = Get-Content $path -Raw -ErrorAction Stop
    } catch {
        continue
    }
    $scanned++
    $lower = $content.ToLowerInvariant()
    foreach ($kw in $Keywords) {
        $pattern = [regex]::Escape($kw.ToLowerInvariant())
        $count = ([regex]::Matches($lower, $pattern)).Count
        if ($count -gt 0) { $hits[$kw] += $count }
    }
}

$passed = (($hits.Values | Measure-Object -Sum).Sum -eq 0)
$ledgerPath = Join-Path $RepoRoot $LedgerDir
New-Item -ItemType Directory -Force -Path $ledgerPath | Out-Null
$outPath = Join-Path $ledgerPath $Output

$report = @{
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    phase = 3
    guard_test_exe = $guardTest
    notes_simulated = $NoteCount
    simulate_result = $sim
    files_scanned = $scanned
    new_files_after_session = @($newFiles).Count
    keyword_hits = $hits
    passed = $passed
    summary = if ($passed) { "0 bytes of clinical narrative persisted" } else { "FAIL — clinical keywords found on disk" }
    watch_paths = @($WatchPaths)
}
$report | ConvertTo-Json -Depth 6 | Set-Content $outPath -Encoding UTF8

Write-Host "Disk audit manifest -> $outPath (passed=$passed)"
if (-not $passed) { exit 1 }
exit 0
