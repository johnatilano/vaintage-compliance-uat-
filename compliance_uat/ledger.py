"""Write compliance ledger artifacts for executive handoff."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

LEDGER_DIR = Path(__file__).resolve().parent.parent / "compliance-ledger"


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_payload_capture(scrubbed_sample: str, adapter: str) -> Path:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    path = LEDGER_DIR / "payload-capture.txt"
    path.write_text(
        f"# VAIntage Compliance UAT — Request Payload Capture\n"
        f"# Generated: {_stamp()}\n"
        f"# Adapter: {adapter}\n\n"
        f"{scrubbed_sample}\n",
        encoding="utf-8",
    )
    return path


def write_api_config_snapshot(config: dict, adapter: str) -> Path:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    path = LEDGER_DIR / "api-config-snapshot.json"
    payload = {
        "generated_at": _stamp(),
        "adapter": adapter,
        "config": config,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_disk_audit_manifest(
    *,
    adapter: str,
    files_scanned: int,
    new_files: int,
    keyword_hits: dict[str, int],
    passed: bool,
) -> Path:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    path = LEDGER_DIR / "disk-audit-manifest.json"
    payload = {
        "generated_at": _stamp(),
        "adapter": adapter,
        "files_scanned": files_scanned,
        "new_files_after_session": new_files,
        "keyword_hits": keyword_hits,
        "passed": passed,
        "summary": (
            "0 bytes of clinical narrative persisted"
            if passed
            else "FAIL — clinical keywords found on disk"
        ),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_vaporization_report(
    *,
    adapter: str,
    passed: bool,
    detail: str,
    gc_collect_called: bool = False,
    memory_wiped: bool = False,
) -> Path:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    path = LEDGER_DIR / "vaporization-report.json"
    payload = {
        "generated_at": _stamp(),
        "adapter": adapter,
        "passed": passed,
        "detail": detail,
        "gc_collect_called": gc_collect_called,
        "memory_wiped": memory_wiped,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_live_zdr_report(result: dict, adapter: str) -> Path:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    path = LEDGER_DIR / "live-zdr-report.json"
    payload = {
        "generated_at": _stamp(),
        "adapter": adapter,
        **result,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
