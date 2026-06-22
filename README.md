# VAIntage Compliance UAT — Runbook & Integration Guide

Portable **four-phase ZDR / Safe Harbor certification suite** for the Layer 2 Guard agent and **oc-4 mini** Azure OpenAI deployment.

| Phase | Language | What it proves |
|-------|----------|----------------|
| **1** | C# xUnit | Zero raw PHI in outbound JSON; `[CLIENT_REF]` tokens; SHA-256 attestation |
| **2** | Python | `store: false`, data logging disabled — reads **`guard-test config`** |
| **3** | PowerShell | 0 clinical keywords on disk after **`guard-test simulate --count 1000`** |
| **4** | C# xUnit | Session cache cleared; real **`GC.Collect()`** on production vaporization path |

**Production integration point:** `src/VAIntage.Guard.Host/GuardApplication.cs`

---

## What this repo is (and is not)

### This repo **is**
- A certification harness that exercises `GuardApplication` — the same facade integrated into the Guard desktop app
- A source of executive proof artifacts in `compliance-ledger/`
- Runnable locally on a developer machine before official sign-off

### This repo **is not**
- The production Guard WinUI application (integrate `Guard.Core` + `Guard.Host` into the production solution separately)
- Proof that Azure remote RAM is wiped (cannot be verified from a workstation)
- A substitute for running the full suite on **Windows** with staging Azure credentials configured

**Official sign-off:** Run `.\scripts\Run-FullComplianceUat.ps1` on Windows with `.env` filled in and confirm ZDR on oc-4 mini staging.

---

## Prerequisites

### Windows (primary target platform)

| Tool | Version | Install |
|------|---------|---------|
| Git | any | https://git-scm.com/download/win |
| .NET SDK | **8.x** | https://dotnet.microsoft.com/download/dotnet/8.0 |
| Python | 3.9+ | https://www.python.org/downloads/ (check "Add to PATH") |
| PowerShell | 5+ or 7 | Built into Windows; PS7 optional |

Verify:

```powershell
git --version
dotnet --version    # must be 8.x
python --version
```

### macOS (secondary / developer machines)

```bash
brew install git python@3 dotnet@8 powershell
```

**Critical Mac caveat:** Homebrew PowerShell depends on .NET 10 and can shadow `dotnet@8`. Pin .NET 8 in `~/.zshrc`:

```bash
export DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec"
export PATH="/opt/homebrew/opt/dotnet@8/bin:$PATH"
```

Verify:

```bash
dotnet --version   # 8.x
python3 --version  # 3.9+
pwsh --version     # 7.x
```

---

## First-time setup

### 1. Clone and enter the repo

```bash
git clone https://github.com/johnatilano/vaintage-compliance-uat-.git
cd vaintage-compliance-uat-
```

### 2. Python virtual environment

**Windows:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

**macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Build `guard-test` (required for Phases 2 & 3)

```bash
dotnet build src/VAIntage.Guard.TestCli -c Release
```

Smoke test:

```bash
# Windows
.\src\VAIntage.Guard.TestCli\bin\Release\net8.0\guard-test.exe config

# macOS (use wrapper — see Mac caveats below)
./scripts/guard-test-mac.sh config
```

Expected JSON (endpoint may be empty without `.env`):

```json
{"endpoint":"","deployment":"","store":false,"data_logging":"disabled","api_version":"2024-12-01-preview"}
```

The important fields are `"store": false` and `"data_logging": "disabled"`.

### 4. Azure staging credentials (optional for local dev, required for full sign-off)

```bash
cp config/staging.example.env .env
```

Fill in staging values from your Azure OpenAI administrator:

| Variable | Purpose |
|----------|---------|
| `AZURE_OPENAI_ENDPOINT` | Staging resource URL |
| `AZURE_OPENAI_DEPLOYMENT` | oc-4 mini deployment name |
| `AZURE_OPENAI_API_KEY` | Staging API key (live ping only) |
| `OPENAI_STORE` | Must be `false` |
| `AZURE_DATA_LOGGING` | Must be `disabled` |

---

## Run all four phases (one command)

### Windows (official path)

```powershell
.\scripts\Run-FullComplianceUat.ps1
```

### macOS

```bash
./scripts/Run-FullComplianceUat.sh
```

### What the orchestrator does

1. Builds `guard-test`
2. **Phase 1** — C# scrubbing + SHA-256 attestation
3. **Phase 4** — C# vaporization (production GC path)
4. **Phase 2** — Python ZDR config audit
5. **Phase 3** — PowerShell disk audit (1000-note simulation)
6. Writes `compliance-ledger/certification-summary.json`

### Reading `certification-summary.json`

| `status` | Meaning |
|----------|---------|
| `PASS` | All phases completed without failure |
| `FAIL` | At least one phase failed — check terminal output for which phase |

**Common false alarm:** `status: FAIL` with Phase 3 showing `passed=True` usually means **Phase 2** failed a metadata test, not that ZDR logic is broken. See [Phase 2 caveats](#phase-2-caveats-without-azure-credentials).

---

## Run phases individually

Set `GUARD_TEST_EXE` first:

```powershell
# Windows
$env:GUARD_TEST_EXE = "src/VAIntage.Guard.TestCli/bin/Release/net8.0/guard-test.exe"
```

```bash
# macOS
export GUARD_TEST_EXE="$PWD/scripts/guard-test-mac.sh"
```

### Phase 1 — Scrubbing + payload intercept + SHA-256

```bash
dotnet test phase1/VAIntage.Phase1.Scrubbing.Tests -v
```

- Tests `GuardApplication.BuildOutboundPayloadJson()` and `AttestOutboundPayload()`
- Writes `compliance-ledger/payload-capture.txt`
- **Does not require Azure credentials**

### Phase 2 — ZDR API configuration audit

```bash
# Windows
$env:PYTHONPATH = "phase2"
pytest phase2/tests/ -v

# macOS
PYTHONPATH=phase2 pytest phase2/tests/ -v
```

- Reads config from `guard-test config` when built
- Writes `compliance-ledger/api-config-snapshot.json`
- Optional live Azure ping: `RUN_LIVE_ZDR=1 pytest phase2/tests/ --run-live -v`

#### Phase 2 caveats (without Azure credentials)

If `.env` has no `AZURE_OPENAI_ENDPOINT`, you will typically see:

```
1 failed, 2 passed, 1 skipped
```

| Test | Without Azure | Meaning |
|------|---------------|---------|
| `test_api_client_enforces_store_false...` | **Pass** | ZDR contract values are correct |
| `test_api_config_snapshot_writes...` | **Pass** | Ledger artifact written |
| `test_config_reads_from_guard_test_when_available` | **Fail** | Config source metadata — expects non-empty endpoint from `guard-test` |
| `test_live_zdr_request` | **Skipped** | Needs `RUN_LIVE_ZDR=1` + real creds |

**This is expected for local dev without staging creds.** The core ZDR checks (`store: false`, logging disabled) still pass. Add Azure staging values to `.env` for a clean Phase 2 run and live ping.

### Phase 3 — 1,000-note disk audit

```powershell
# Windows
.\phase3\Run-DiskAudit.ps1 -NoteCount 1000 -GuardTestExe $env:GUARD_TEST_EXE
```

```bash
# macOS
pwsh -File phase3/Run-DiskAudit.ps1 -NoteCount 1000 -GuardTestExe "$PWD/scripts/guard-test-mac.sh"
```

- Calls `guard-test watch-paths` then `guard-test simulate --count 1000`
- Scans **only watched paths** for new files containing clinical keywords
- Writes `compliance-ledger/disk-audit-manifest.json`

#### What Phase 3 actually scans

**Not the whole disk.** Only directories returned by `guard-test watch-paths`:

| Path | Platform |
|------|----------|
| `compliance-ledger/` | All |
| `.uat-scratch/` | All |
| System temp | All |
| `%LOCALAPPDATA%/VAIntage` | Windows |
| `%APPDATA%/VAIntage` | Windows |
| `%ProgramFiles%/VAIntage` | Windows |

Success looks like:

```text
Disk audit manifest -> .../disk-audit-manifest.json (passed=True)
```

#### Mac Phase 3 caveats

1. **PowerShell + .NET 10:** Homebrew `pwsh` can load .NET 10 instead of 8. Use `scripts/guard-test-mac.sh` (runs `dotnet exec guard-test.dll` via dotnet@8).
2. **PowerShell `$Args` bug:** Fixed in `Run-DiskAudit.ps1` — parameter is `$GuardArgs`, not `$Args`.
3. **Do not commit `obj/` files:** `**/obj/` is in `.gitignore`. NuGet lockfiles under `obj/` are machine-specific build output.

### Phase 4 — Compliance drawer vaporization

```bash
dotnet test phase4/VAIntage.Phase4.Vaporization.Tests -v
```

- Uses production path: `RuntimeGcCollector` + `SecureMemoryWiper`
- Writes `compliance-ledger/vaporization-report.json`
- **Does not require Azure credentials**

---

## `guard-test` CLI reference

Built from `src/VAIntage.Guard.TestCli/`. All UAT phases call into `GuardApplication`.

```
guard-test scrub --text "Patient Jane Doe visited on 01/15/2024..."
guard-test config
guard-test simulate --count 1000
guard-test dismiss
guard-test cache-peek
guard-test watch-paths
```

| Command | Phase | Purpose |
|---------|-------|---------|
| `scrub` | 1 | Scrub raw clinical text to Safe Harbor tokens |
| `config` | 2 | Emit Azure OpenAI client config JSON |
| `simulate` | 3 | Simulate counselor typing session into volatile cache |
| `dismiss` | 4 | Dismiss compliance drawer — wipe cache + GC |
| `cache-peek` | 4 | Inspect volatile session cache (debug) |
| `watch-paths` | 3 | List directories to scan for disk audit |

---

## Integrate into the production Guard application

### What to copy

```
src/VAIntage.Guard.Core/     Scrubber, payload handler, attestation, session cache
src/VAIntage.Guard.Host/     GuardApplication — single production facade
```

Add both projects to the production Guard solution (or merge into existing projects).

### Where to call `GuardApplication`

```csharp
var app = GuardApplication.CreateProduction();
```

| Guard event | Call |
|-------------|------|
| Before Azure API POST | `app.BuildOutboundPayloadJson(rawNote)` |
| Counselor typing / session buffer | Route notes through `SafeHarborScrubber` + `VolatileSessionCache` (see `SimulateTypingSession`) |
| Compliance drawer Resolve / dismiss | `app.DismissComplianceDrawer()` |

### Production replacements over time

| UAT stand-in | Production replacement |
|--------------|------------------------|
| `AzureOpenAiClientConfig.FromEnvironment()` | DI container + Azure SDK config |
| `GuardApplication.CreateProduction()` | Service container registration |
| `guard-test` CLI | Not shipped — dev/certification only |
| Phase 4 test calling `DismissComplianceDrawer()` | WinUI drawer click handler calling same API |

### Environment variables in production

Guard reads the same contract as Phase 2:

```
OPENAI_STORE=false
AZURE_DATA_LOGGING=disabled
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_DEPLOYMENT=...
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

---

## Compliance ledger (executive deliverables)

After a full run, check `compliance-ledger/`:

| Artifact | Phase | Contents |
|----------|-------|----------|
| `payload-capture.txt` | 1 | Scrubbed outbound JSON sample |
| `api-config-snapshot.json` | 2 | ZDR config proof (`store`, `data_logging`) |
| `disk-audit-manifest.json` | 3 | Keyword scan results + `passed` flag |
| `vaporization-report.json` | 4 | Cache wipe + GC attestation |
| `certification-summary.json` | All | Index + overall `PASS`/`FAIL` |

`compliance-ledger/` is gitignored (except `.gitkeep`). Archive artifacts separately when submitting sign-off evidence.

---

## Certification checklist

- [ ] Run `.\scripts\Run-FullComplianceUat.ps1` on **Windows**
- [ ] `.env` filled with staging `AZURE_OPENAI_*` values
- [ ] `certification-summary.json` shows `status: PASS`
- [ ] `api-config-snapshot.json` shows `store: false`, `data_logging: disabled`
- [ ] `disk-audit-manifest.json` shows `passed: true`
- [ ] Confirm ZDR enabled on oc-4 mini staging (verify with Azure administrator)
- [ ] Optional: `RUN_LIVE_ZDR=1` live Azure ping passes
- [ ] Copy `VAIntage.Guard.Core` + `GuardApplication` into production Guard solution
- [ ] Wire WinUI compliance drawer to `DismissComplianceDrawer()`

### What cannot be certified from a workstation

- Azure server-side RAM / remote memory state after request completes
- Production WinUI click paths (UAT calls the API directly)
- Production `HttpClient` / Azure SDK wrapper (UAT tests `GuardApplication` in isolation)

---

## Troubleshooting

### `You must install or update .NET` / framework 8.0.0 not found (Mac)

PowerShell is using .NET 10. Fix:

```bash
export DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec"
export PATH="/opt/homebrew/opt/dotnet@8/bin:$PATH"
./scripts/guard-test-mac.sh config   # should return JSON
pwsh -File phase3/Run-DiskAudit.ps1 -NoteCount 1000
```

### `guard-test failed: Usage: guard-test <scrub|config|...>` (Mac)

Subcommands not reaching `guard-test`. Ensure you are on current `main` (PowerShell `$Args` fix merged). Use `guard-test-mac.sh` as `-GuardTestExe`.

### Phase 2: `assert 'environment' == 'guard-test.exe'`

No Azure endpoint in `.env`. Core ZDR checks still pass. Add staging creds or treat as expected for offline dev.

### `dotnet test` prints help instead of running tests

Pass the project path:

```bash
dotnet test phase1/VAIntage.Phase1.Scrubbing.Tests -v
```

### `obj/*.nuget.dgspec.json` shows Homebrew paths in IDE

Normal local build output. Covered by `**/obj/` in `.gitignore` — do not commit.

### Full suite `FAIL` but Phase 3 shows `passed=True`

Phase 2 metadata test failed. Check pytest output above Phase 3 in the terminal.

---

## Architecture

```
src/
  VAIntage.Guard.Core/       Scrubber, payload handler, attestation, session cache
  VAIntage.Guard.Host/       GuardApplication — production wiring facade
  VAIntage.Guard.TestCli/    guard-test CLI (certification entry point)
phase1/                      C# xUnit — Phase 1
phase2/                      Python pytest — Phase 2
phase3/                      PowerShell — Phase 3
phase4/                      C# xUnit — Phase 4
fixtures/                    Synthetic PHI + clinical keywords
scripts/                     Orchestrators + guard-test-mac.sh
compliance-ledger/           Executive proof artifacts (gitignored output)
config/                      staging.example.env template
```

Solution file: `VAIntageComplianceUat.sln`

---

## Quick reference

```powershell
# Windows — full certification run
python -m venv .venv && .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
copy config\staging.example.env .env   # fill in Azure values
.\scripts\Run-FullComplianceUat.ps1
```

```bash
# macOS — full dev run
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
./scripts/Run-FullComplianceUat.sh
```
