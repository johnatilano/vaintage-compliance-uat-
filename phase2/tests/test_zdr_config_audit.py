"""Phase 2 — Python API configuration audit (ZDR / store=false).

Inspects production API client via guard-test.exe config when built;
falls back to environment. Ask John if ZDR is enabled on oc-4 mini.
"""
from __future__ import annotations

import pytest

from zdr_audit.config import AzureOpenAiClientConfig
from zdr_audit.guard_cli import resolve_guard_test_exe
from zdr_audit.ledger import write_api_config_snapshot, write_live_zdr_report
from zdr_audit.live_zdr import live_zdr_ping


def test_api_client_enforces_store_false_and_disabled_data_logging():
    cfg = AzureOpenAiClientConfig.load()
    if not cfg.endpoint:
        cfg = AzureOpenAiClientConfig(
            endpoint="https://staging.openai.azure.com/",
            deployment="o4-mini-staging",
            store=False,
            data_logging="disabled",
            source="uat-default",
        )

    assert cfg.store is False, "OPENAI store must be false for ZDR compliance"
    assert cfg.zdr_compliant, f"data_logging={cfg.data_logging!r} is not a disabled ZDR state"


def test_api_config_snapshot_writes_compliance_log_file():
    cfg = AzureOpenAiClientConfig.load()
    if not cfg.endpoint:
        cfg = AzureOpenAiClientConfig(
            endpoint="https://staging.openai.azure.com/",
            deployment="o4-mini-staging",
            store=False,
            data_logging="disabled",
            source="uat-default",
        )

    path = write_api_config_snapshot(cfg)
    assert path.exists()
    text = path.read_text().lower()
    assert '"store": false' in text
    assert "zdr_compliant" in text


def test_config_reads_from_guard_test_when_available():
    if not resolve_guard_test_exe():
        pytest.skip("Build guard-test.exe: dotnet build src/VAIntage.Guard.TestCli -c Release")
    cfg = AzureOpenAiClientConfig.load()
    assert cfg.source == "guard-test.exe"


@pytest.mark.integration
def test_live_zdr_request(run_live):
    if not run_live:
        pytest.skip("Set RUN_LIVE_ZDR=1 or pass --run-live for live Azure ping")

    cfg = AzureOpenAiClientConfig.load()
    if not cfg.endpoint or not cfg.deployment:
        pytest.skip("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT required")

    result = live_zdr_ping(cfg)
    write_live_zdr_report({
        "ok": result.ok,
        "status_code": result.status_code,
        "store_in_body": result.store_in_body,
        "endpoint": result.endpoint,
        "deployment": result.deployment,
        "detail": result.detail,
        "response_excerpt": result.response_excerpt,
        "config_source": cfg.source,
    })
    assert result.store_in_body is False
    assert result.ok, result.detail
