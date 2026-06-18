#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
LEDGER="$ROOT/compliance-ledger"
mkdir -p "$LEDGER"
FAIL=0

run_or_fail() {
  echo "=== $1 ==="
  shift
  if "$@"; then echo "OK: $1"; else echo "FAIL: $1"; FAIL=1; fi
  echo
}

if command -v dotnet >/dev/null 2>&1; then
  echo "=== Building guard-test.exe ==="
  dotnet build "$ROOT/src/VAIntage.Guard.TestCli" -c Release
  if [[ -x "$ROOT/scripts/guard-test-mac.sh" ]]; then
    export GUARD_TEST_EXE="$ROOT/scripts/guard-test-mac.sh"
  else
    export GUARD_TEST_EXE="$ROOT/src/VAIntage.Guard.TestCli/bin/Release/net8.0/guard-test"
    [[ -f "$GUARD_TEST_EXE" ]] || export GUARD_TEST_EXE="${GUARD_TEST_EXE}.exe"
  fi
  echo
  run_or_fail "Phase 1 (C# xUnit)" dotnet test "$ROOT/phase1/VAIntage.Phase1.Scrubbing.Tests" --verbosity minimal
  run_or_fail "Phase 4 (C# xUnit)" dotnet test "$ROOT/phase4/VAIntage.Phase4.Vaporization.Tests" --verbosity minimal
else
  echo "SKIP Phases 1 & 4: install .NET 8 SDK"; FAIL=1; echo
fi

[[ -d .venv ]] && source .venv/bin/activate
pip install -q -e ".[dev]" 2>/dev/null || true
run_or_fail "Phase 2 (Python)" env PYTHONPATH=phase2 python -m pytest phase2/tests/ -q

if command -v pwsh >/dev/null 2>&1 && [[ -n "${GUARD_TEST_EXE:-}" ]]; then
  run_or_fail "Phase 3 (PowerShell)" pwsh -File "$ROOT/phase3/Run-DiskAudit.ps1" -NoteCount "${HEAVY_SESSION_COUNT:-1000}" -GuardTestExe "$GUARD_TEST_EXE"
else
  echo "SKIP Phase 3: run phase3/Run-DiskAudit.ps1 on Windows with PowerShell"; echo
fi

python3 -c "
import json
from datetime import datetime, timezone
from pathlib import Path
ledger = Path('$LEDGER')
summary = {
    'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    'guard_test_exe': '${GUARD_TEST_EXE:-}',
    'artifacts': [p.name for p in ledger.glob('*') if p.is_file()],
    'status': 'PASS' if $FAIL == 0 else 'FAIL',
}
(ledger / 'certification-summary.json').write_text(json.dumps(summary, indent=2))
print('Certification summary ->', ledger / 'certification-summary.json')
"

exit $FAIL
