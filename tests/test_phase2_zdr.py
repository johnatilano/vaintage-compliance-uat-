"""Phase 2 — API configuration audit (ZDR / store=false)."""
from __future__ import annotations

import pytest

from compliance_uat.ledger import write_api_config_snapshot, write_live_zdr_report
from compliance_uat.live_zdr import live_zdr_ping


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


@pytest.mark.integration
def test_live_zdr_request(target, run_live):
    """Optional live POST to Azure OpenAI with store=false (requires credentials)."""
    if not run_live:
        pytest.skip("Pass --run-live or set RUN_LIVE_ZDR=1 to exercise live Azure path")
    if target.name == "mock":
        pytest.skip("mock adapter has no live cloud endpoint")

    cfg = target.get_api_config()
    if not cfg.endpoint or not cfg.deployment:
        pytest.skip("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT required")

    result = live_zdr_ping(cfg)
    report_path = write_live_zdr_report(
        {
            "ok": result.ok,
            "status_code": result.status_code,
            "store_in_body": result.store_in_body,
            "endpoint": result.endpoint,
            "deployment": result.deployment,
            "detail": result.detail,
            "response_excerpt": result.response_excerpt,
        },
        target.name,
    )
    assert report_path.exists()
    assert result.store_in_body is False
    assert result.ok, result.detail
