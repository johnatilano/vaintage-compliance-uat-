# VAIntage Compliance UAT

Portable test harness for proving **Zero Data Retention (ZDR)** and **Safe Harbor**
privacy claims for the Layer 2 Guard agent. Runs against any app that implements
the `PrivacyTestTarget` adapter interface.

This repo is **separate** from:

- [`LambentDataScrapers`](https://github.com/jyfygdzdhp-star/LambentDataScrapers) — Layer 1 rules Brain
- John's C# Guard repo — Layer 2 production desktop agent

## Quick start

```bash
cd vaintage-compliance-uat
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# CI / smoke (no cloud, no Windows)
pytest tests/ --target=mock

# Demo / stakeholder proof (reference scrubber)
pytest tests/ --target=python_reference

# Full ledger for executives
python scripts/run_full_ledger.py --target=python_reference
```

Outputs land in `compliance-ledger/`:

| Artifact | Phase | Proves |
|----------|-------|--------|
| `payload-capture.txt` | 1 | Outbound text is de-identified |
| `api-config-snapshot.json` | 2 | `store: false` / ZDR flags |
| `disk-audit-manifest.json` | 3 | No clinical keywords on disk |
| `vaporization-report.json` | 4 | RAM cleared on drawer dismiss |
| `certification-summary.json` | All | Handoff index |

## Adapters

| Adapter | When to use |
|---------|-------------|
| `mock` | GitHub Actions CI — proves harness wiring |
| `python_reference` | UAT demos, contract reference for John's scrubber |
| `guard` | Final sign-off against real Guard test exe |

### Guard adapter (when John is ready)

Set `GUARD_TEST_EXE` to a Guard test build that supports:

```
guard-test.exe scrub --text "..."
guard-test.exe config
guard-test.exe simulate --count 1000
guard-test.exe dismiss
guard-test.exe cache-peek
guard-test.exe watch-paths
```

## Phase 2 staging config

```bash
cp config/staging.example.env .env
# Fill in Azure staging values — ask John if ZDR is enabled
```

## Windows disk watch (manual Phase 3)

During a live Guard typing session on Windows:

```powershell
.\scripts\disk_watch.ps1
```

## Architecture

```
fixtures/          synthetic PHI + clinical keywords (never real patients)
compliance_uat/
  adapters/        plug in mock | python_reference | guard
  scrubber.py      reference Safe Harbor implementation (contract)
  ledger.py        writes executive proof artifacts
tests/             generic assertions (same for every adapter)
```

## Relationship to LambentDataScrapers

| Repo | Tests |
|------|-------|
| LambentDataScrapers | Rules engine — `uat_engine1.py`, `uat_engine2.py` |
| vaintage-compliance-uat | Privacy / ZDR — this repo |

John's C# scrubber must match `compliance_uat/scrubber.py` output for Phase 1 sign-off.

## Push as its own GitHub repo

```bash
cd vaintage-compliance-uat
git init
git add .
git commit -m "Add portable ZDR compliance UAT harness"
git remote add origin https://github.com/YOUR_ORG/vaintage-compliance-uat.git
git push -u origin main
```
