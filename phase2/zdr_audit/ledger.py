"""Write Phase 2 compliance log artifacts."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from zdr_audit.config import AzureOpenAiClientConfig

ROOT = Path(__file__).resolve().parent.parent.parent
LEDGER_DIR = ROOT / "compliance-ledger"


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_api_config_snapshot(config: AzureOpenAiClientConfig) -> Path:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    path = LEDGER_DIR / "api-config-snapshot.json"
    payload = {
        "generated_at": _stamp(),
        "phase": 2,
        "config_source": config.source,
        "config": {
            "endpoint": config.endpoint,
            "deployment": config.deployment,
            "store": config.store,
            "data_logging": config.data_logging,
            "api_version": config.api_version,
            "zdr_compliant": config.zdr_compliant,
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_live_zdr_report(result: dict) -> Path:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    path = LEDGER_DIR / "live-zdr-report.json"
    payload = {"generated_at": _stamp(), "phase": 2, **result}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
