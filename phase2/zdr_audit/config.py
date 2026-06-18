"""Azure OpenAI client configuration — ZDR contract for oc-4 mini."""
from __future__ import annotations

import os
from dataclasses import dataclass

from zdr_audit.guard_cli import fetch_api_config_json, resolve_guard_test_exe


@dataclass
class AzureOpenAiClientConfig:
    endpoint: str
    deployment: str
    store: bool
    data_logging: str
    api_version: str = "2024-12-01-preview"
    source: str = "environment"

    @property
    def zdr_compliant(self) -> bool:
        return self.store is False and self.data_logging.lower() in {
            "disabled", "off", "false", "none",
        }

    @classmethod
    def from_environment(cls) -> AzureOpenAiClientConfig:
        store_raw = os.environ.get("OPENAI_STORE", "false").lower()
        return cls(
            endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
            deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", ""),
            store=store_raw in {"true", "1", "yes"},
            data_logging=os.environ.get("AZURE_DATA_LOGGING", "disabled"),
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
            source="environment",
        )

    @classmethod
    def load(cls) -> AzureOpenAiClientConfig:
        """Prefer guard-test.exe config (production client path) when available."""
        if resolve_guard_test_exe():
            try:
                data = fetch_api_config_json()
                endpoint = data.get("endpoint", "")
                if endpoint:
                    return cls(
                        endpoint=endpoint,
                        deployment=data.get("deployment", ""),
                        store=bool(data.get("store", True)),
                        data_logging=str(data.get("data_logging", "unknown")),
                        api_version=data.get("api_version", "2024-12-01-preview"),
                        source="guard-test.exe",
                    )
            except (FileNotFoundError, OSError, ValueError):
                pass
        return cls.from_environment()
