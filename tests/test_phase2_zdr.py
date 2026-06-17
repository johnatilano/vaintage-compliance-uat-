"""Phase 2 — API configuration audit (ZDR / store=false)."""
from __future__ import annotations

import pytest

from compliance_uat.ledger import write_api_config_snapshot


def test_zdr_config_contract(target):
    cfg = target.get_api_config()
    if target.name == "python_reference" and not cfg.endpoint:
        pytest.skip("Set AZURE_OPENAI_* in .env for staging audit")

    assert cfg.store is False, "OPENAI store must be false for ZDR compliance"
    assert cfg.zdr_compliant(), (
        f"data_logging={cfg.data_logging!r} is not a disabled ZDR state"
    )


def test_api_config_snapshot_ledger(target):
    cfg = target.get_api_config()
    path = write_api_config_snapshot(
        {
            "endpoint": cfg.endpoint,
            "deployment": cfg.deployment,
            "store": cfg.store,
            "data_logging": cfg.data_logging,
            "api_version": cfg.api_version,
            "zdr_compliant": cfg.zdr_compliant(),
        },
        target.name,
    )
    assert path.exists()
    assert '"store": false' in path.read_text().lower() or '"store": false' in path.read_text()
