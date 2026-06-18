# VAIntage Compliance UAT — John's Four-Phase ZDR Certification Suite

Prove **Zero Data Retention (ZDR)** and **Safe Harbor** claims for the Layer 2 Guard
agent and **oc-4 mini** Azure OpenAI deployment. Each phase uses the language from
the UAT handoff document.

| Phase | Language | What it proves |
|-------|----------|----------------|
| **1** | **C# xUnit** | Zero raw PHI in outbound JSON; `[CLIENT_REF]` tokens; SHA-256 attestation |
| **2** | **Python** | `store: false`, data logging disabled — reads **`guard-test.exe config`** |
| **3** | **PowerShell** | 0 clinical keywords on disk after **`guard-test simulate --count 1000`** |
| **4** | **C# xUnit** | `ConcurrentDictionary` cleared; real **`GC.Collect()`** on production path |

**John integrates:** `src/VAIntage.Guard.Host/GuardApplication.cs` into the Guard desktop app.

---

## Prerequisites (Windows)

- [.NET 8 SDK](https://dotnet.microsoft.com/download)
- Python 3.9+
- PowerShell 5+ (or PowerShell 7)

---

## One-command full UAT (Windows)

```powershell
cd vaintage-compliance-uat
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

copy config\staging.example.env .env
# Fill AZURE_OPENAI_* — ask John if ZDR is enabled on oc-4 mini staging

.\scripts\Run-FullComplianceUat.ps1
```

This will:
1. Build **`guard-test.exe`**
2. Run Phase 1 & 4 C# xUnit tests through **`GuardApplication`** (production wiring)
3. Run Phase 2 Python audit against **`guard-test config`**
4. Run Phase 3 PowerShell disk audit calling **`guard-test simulate`**
5. Write **`compliance-ledger/certification-summary.json`**

---

## Run phases individually

### Build guard-test.exe (required for Phases 2 & 3)

```powershell
dotnet build src/VAIntage.Guard.TestCli -c Release
$env:GUARD_TEST_EXE = "src/VAIntage.Guard.TestCli/bin/Release/net8.0/guard-test.exe"
```

### Phase 1 — C# xUnit (scrubbing + payload intercept + SHA-256)

```powershell
dotnet test phase1/VAIntage.Phase1.Scrubbing.Tests -v
```

Tests **`GuardApplication.BuildOutboundPayloadJson()`** and **`AttestOutboundPayload()`**.  
Writes **`compliance-ledger/payload-capture.txt`**.

### Phase 2 — Python (ZDR config audit)

```powershell
$env:PYTHONPATH = "phase2"
pytest phase2/tests/ -v

# Optional live Azure ping:
pytest phase2/tests/ --run-live -v
```

Reads config from **`guard-test.exe config`** when built.  
Writes **`compliance-ledger/api-config-snapshot.json`**.

### Phase 3 — PowerShell (1,000-note disk audit)

```powershell
.\phase3\Run-DiskAudit.ps1 -NoteCount 1000 -GuardTestExe $env:GUARD_TEST_EXE
```

Calls **`guard-test simulate --count 1000`** and **`watch-paths`**.  
Writes **`compliance-ledger/disk-audit-manifest.json`**.

### Phase 4 — C# xUnit (compliance drawer vaporization)

```powershell
dotnet test phase4/VAIntage.Phase4.Vaporization.Tests -v
```

**Production path** test uses **`RuntimeGcCollector`** + **`SecureMemoryWiper`**.  
Writes **`compliance-ledger/vaporization-report.json`**.

---

## guard-test.exe CLI

```
guard-test scrub --text "Patient John Doe..."
guard-test config
guard-test simulate --count 1000
guard-test dismiss
guard-test cache-peek
guard-test watch-paths
```

---

## Integrate into John's Guard repo

Copy these into the Guard solution:

```
src/VAIntage.Guard.Core/     SafeHarborScrubber, OutboundPayloadHandler, etc.
src/VAIntage.Guard.Host/     GuardApplication — single production facade
```

| Guard event | Call |
|-------------|------|
| Before Azure API POST | `app.BuildOutboundPayloadJson(rawNote)` |
| Counselor typing session | `app.SimulateTypingSession(notes)` or your UI handler |
| Compliance drawer Resolve | `app.DismissComplianceDrawer()` |

Replace `GuardApplication.CreateProduction()` internals with John's DI container when ready.

---

## Compliance ledger checklist

| Deliverable | Artifact |
|-------------|----------|
| Request Payload Capture | `payload-capture.txt` |
| API Configuration Snapshot | `api-config-snapshot.json` |
| Local Disk Audit Manifest | `disk-audit-manifest.json` |
| Vaporization Report | `vaporization-report.json` |
| Executive index | `certification-summary.json` |

---

## Architecture

```
src/
  VAIntage.Guard.Core/       Scrubber, payload handler, attestation, session cache
  VAIntage.Guard.Host/       GuardApplication — production wiring facade
  VAIntage.Guard.TestCli/    guard-test.exe
phase1/                      C# xUnit — Phase 1
phase2/                      Python pytest — Phase 2
phase3/                      PowerShell — Phase 3
phase4/                      C# xUnit — Phase 4
fixtures/                    Synthetic PHI + clinical keywords
compliance-ledger/           Executive proof artifacts
```

---

## What still requires John's production Guard repo

- WinUI compliance drawer click automation (Phase 4 uses `DismissComplianceDrawer()` API)
- John's live `HttpClient` / Azure SDK wrapper (Phase 1 tests `GuardApplication` in this repo)
- Confirming Azure ZDR is enabled on oc-4 mini staging (Phase 2 live ping)
- Azure remote RAM — cannot be verified from the workstation
