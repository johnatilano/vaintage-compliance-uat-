# VAIntage Compliance UAT

Four-phase **Zero Data Retention (ZDR)** certification suite for the Layer 2 Guard
agent and oc-4 mini cloud reasoning engine. Each phase uses the language specified
in the UAT handoff document.

| Phase | Language | Folder | Proves |
|-------|----------|--------|--------|
| **1** Client-side scrubbing | **C# xUnit** | `phase1/` | Zero PHI in outbound JSON; `[CLIENT_REF]` tokens |
| **2** ZDR API config audit | **Python** | `phase2/` | `store: false`, data logging disabled |
| **3** Negative disk audit | **PowerShell** | `phase3/` | 0 clinical keywords on disk after 1,000 notes |
| **4** Drawer vaporization | **C# xUnit** | `phase4/` | `ConcurrentDictionary` cleared, `GC.Collect()`, memory wipe |

Shared library for John to copy into Guard: `src/VAIntage.Guard.Core/`

## Quick start (Windows — John's machine)

```powershell
# Prerequisites: .NET 8 SDK, Python 3.9+, PowerShell 5+

cd vaintage-compliance-uat
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# Run all four phases + certification ledger
.\scripts\Run-FullComplianceUat.ps1
```

## Run phases individually

**Phase 1 — C# xUnit (scrubbing / payload intercept):**
```powershell
dotnet test phase1/VAIntage.Phase1.Scrubbing.Tests -v
```

**Phase 2 — Python (ZDR config audit):**
```powershell
$env:PYTHONPATH = "phase2"
pytest phase2/tests/ -v

# Optional live Azure ping (ask John if ZDR is enabled):
pytest phase2/tests/ --run-live -v
```

**Phase 3 — PowerShell (disk audit, 1,000 notes):**
```powershell
.\phase3\Run-DiskAudit.ps1 -NoteCount 1000
```

**Phase 4 — C# xUnit (compliance drawer vaporization):**
```powershell
dotnet test phase4/VAIntage.Phase4.Vaporization.Tests -v
```

## Compliance ledger (executive handoff)

After a full run, artifacts land in `compliance-ledger/`:

| Artifact | Phase |
|----------|-------|
| `payload-capture.txt` | 1 |
| `api-config-snapshot.json` | 2 |
| `disk-audit-manifest.json` | 3 |
| `vaporization-report.json` | 4 |
| `certification-summary.json` | All |

## Phase 2 staging config

```powershell
copy config\staging.example.env .env
# Fill AZURE_OPENAI_* — ask John if ZDR is enabled on oc-4 mini
```

## Integrate into John's Guard repo

Copy `src/VAIntage.Guard.Core/` into the Guard solution:

| Type | Wire into Guard |
|------|-----------------|
| `SafeHarborScrubber` | Before any cloud API call |
| `OutboundPayloadHandler` | Outbound HTTP handler |
| `AzureOpenAiClientConfig` | App settings / env |
| `VolatileSessionCache` | Volatile session RAM |
| `ComplianceDrawerService` | Resolve / drawer dismiss click |

### Phase 3 on live Guard

Replace `Invoke-VolatileTypingSimulation` in `phase3/Run-DiskAudit.ps1` with a call
to Guard's real automation typing API, then run the script during UAT.

## Architecture

```
fixtures/                 synthetic PHI + clinical keywords
config/                   staging.env template
src/VAIntage.Guard.Core/  shared C# library (John integrates)
phase1/                   C# xUnit — scrubbing
phase2/                   Python pytest — ZDR config
phase3/                   PowerShell — disk audit
phase4/                   C# xUnit — vaporization
scripts/                  full UAT orchestrator
compliance-ledger/        executive proof artifacts
```

## What this cannot prove

- Azure remote RAM or server-side logging
- Cryptographic proof (string audit only)
- Production Guard until John wires `Guard.Core` types into the desktop app
