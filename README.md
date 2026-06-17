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

# Full sign-off including 1000-note audit + live Azure (when creds ready)
python scripts/run_full_ledger.py --target=python_reference --run-heavy --run-live
```

Outputs land in `compliance-ledger/`:

| Artifact | Phase | Proves |
|----------|-------|--------|
| `payload-capture.txt` | 1 | Outbound text is de-identified |
| `api-config-snapshot.json` | 2 | `store: false` / ZDR flags |
| `live-zdr-report.json` | 2 | Live Azure accepted `store=false` request |
| `disk-audit-manifest.json` | 3 | No clinical keywords on disk |
| `vaporization-report.json` | 4 | RAM cleared + GC on drawer dismiss |
| `certification-summary.json` | All | Handoff index |

## What running the test suite entails

Running the suite is a **local, automated compliance check**. No cloud calls, UI
clicks, or production Guard install are required unless you opt in.

### One-time setup

1. Create a venv and install dev dependencies (`pip install -e ".[dev]"`).
2. Copy `config/staging.example.env` → `.env` and fill in Azure values for Phase 2 live tests.

### Pick an adapter (`--target`)

| Adapter | Purpose |
|---------|---------|
| `mock` | CI smoke — proves harness wiring only |
| `python_reference` | Demos and scrubber contract reference |
| `guard` | Final sign-off against Guard (C# exe or local stub) |

### What pytest runs (13 tests across 4 phases)

**Phase 1 — Scrubbing**
- Feeds synthetic PHI (e.g. “Patient John Doe, DOB 11/14/1983…”) through `scrub()`
- Asserts zero raw identifiers remain
- Asserts structural tokens (`[NAME]`, `[DATE]`, `[PHONE]`, etc.)
- **New:** serializes the outbound JSON request body and asserts no PHI in transit + `store: false`
- Writes `payload-capture.txt`

**Phase 2 — ZDR configuration**
- Reads API client config and asserts `store=false` + data logging disabled
- Writes `api-config-snapshot.json`
- **New (optional):** live POST to Azure OpenAI with `store=false` when `--run-live` or `RUN_LIVE_ZDR=1`

**Phase 3 — Disk audit**
- Snapshots watched folders → simulates typing clinical keywords → re-snapshots
- Scans **new** text files for keywords (`substance`, `anxiety`, `transportation`, …)
- Writes `disk-audit-manifest.json`
- **New (optional):** 1,000-note heavy session when `--run-heavy` or `RUN_HEAVY=1`

**Phase 4 — Vaporization**
- Loads text into volatile cache → dismisses overlay → asserts cache is `None`
- **New:** asserts `gc.collect()` / `GC.Collect()` was invoked and memory wiped
- Writes `vaporization-report.json`

### Optional flags

```bash
pytest tests/ --target=python_reference --run-heavy    # 1000-note disk audit
pytest tests/ --target=python_reference --run-live     # live Azure ZDR ping
pytest tests/ --target=guard                           # Guard stub or C# exe
```

Environment gates (in `.env`):

| Variable | Purpose |
|----------|---------|
| `RUN_HEAVY=1` | Enable 1000-note test without CLI flag |
| `HEAVY_SESSION_COUNT` | Override note count (default 1000) |
| `RUN_LIVE_ZDR=1` | Enable live Azure test without CLI flag |
| `AZURE_OPENAI_API_KEY` | Required for live ping |
| `GUARD_TEST_EXE` | Path to C# guard-test.exe (auto-falls back to Python stub) |

### What it still cannot prove

- No inspection of Azure’s remote RAM or servers
- No UI automation of the real compliance drawer (Guard adapter simulates dismiss via CLI)
- Live Azure test requires staging credentials and John confirming ZDR is enabled

## Adapters

| Adapter | When to use |
|---------|-------------|
| `mock` | GitHub Actions CI — proves harness wiring |
| `python_reference` | UAT demos, contract reference for John's scrubber |
| `guard` | Final sign-off against real Guard test exe |

### Guard adapter

Set `GUARD_TEST_EXE` to a Guard test build that supports:

```
guard-test.exe scrub --text "..."
guard-test.exe config
guard-test.exe simulate --count 1000
guard-test.exe dismiss          → JSON: cache_cleared, gc_collect_called, memory_wiped
guard-test.exe cache-peek
guard-test.exe watch-paths
```

Until the C# build exists, the harness auto-uses `scripts/guard_test_stub.py`:

```bash
pytest tests/ --target=guard
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
  payload.py       outbound JSON body builder (Phase 1 intercept)
  live_zdr.py      optional live Azure ZDR ping (Phase 2)
  ledger.py        writes executive proof artifacts
scripts/
  guard_test_stub.py   Python Guard CLI stub for --target=guard
  run_full_ledger.py   runs all phases + certification summary
tests/             generic assertions (same for every adapter)
```

## Relationship to LambentDataScrapers

| Repo | Tests |
|------|-------|
| LambentDataScrapers | Rules engine — `uat_engine1.py`, `uat_engine2.py` |
| vaintage-compliance-uat | Privacy / ZDR — this repo |

John's C# scrubber must match `compliance_uat/scrubber.py` output for Phase 1 sign-off.
