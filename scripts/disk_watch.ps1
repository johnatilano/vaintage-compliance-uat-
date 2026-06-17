# Phase 3 helper — run on Windows during Guard typing simulation.
# Usage: .\scripts\disk_watch.ps1 -Keywords @("substance","anxiety")

param(
    [string[]]$WatchPaths = @(
        "$env:LOCALAPPDATA\VAIntage",
        "$env:APPDATA\VAIntage",
        $env:TEMP
    ),
    [string[]]$Keywords = @("substance", "anxiety", "transportation", "methadone"),
    [string]$Output = "compliance-ledger\disk-watch-manual.json"
)

$hits = @{}
foreach ($kw in $Keywords) { $hits[$kw] = 0 }

$scanned = 0
foreach ($root in $WatchPaths) {
    if (-not (Test-Path $root)) { continue }
    Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        $scanned++
        $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
        if ($null -eq $content) { return }
        foreach ($kw in $Keywords) {
            $count = ([regex]::Matches($content, [regex]::Escape($kw), "IgnoreCase")).Count
            if ($count -gt 0) { $hits[$kw] += $count }
        }
    }
}

$report = @{
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    files_scanned = $scanned
    keyword_hits = $hits
    passed = (($hits.Values | Measure-Object -Sum).Sum -eq 0)
}
$report | ConvertTo-Json -Depth 4 | Set-Content $Output -Encoding UTF8
Write-Host "Disk watch complete -> $Output (passed=$($report.passed))"
