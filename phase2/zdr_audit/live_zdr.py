"""Optional live Azure OpenAI ping with store=false."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

from zdr_audit.config import AzureOpenAiClientConfig


@dataclass(frozen=True)
class LiveZdrResult:
    ok: bool
    status_code: int | None
    store_in_body: bool
    endpoint: str
    deployment: str
    detail: str
    response_excerpt: str = ""


def live_zdr_ping(cfg: AzureOpenAiClientConfig, *, prompt: str = "UAT ZDR connectivity probe.") -> LiveZdrResult:
    api_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
    if not api_key:
        return LiveZdrResult(False, None, False, cfg.endpoint, cfg.deployment, "AZURE_OPENAI_API_KEY not set")
    if not cfg.endpoint or not cfg.deployment:
        return LiveZdrResult(False, None, False, cfg.endpoint, cfg.deployment, "AZURE_OPENAI_* not configured")

    url = (
        f"{cfg.endpoint.rstrip('/')}/openai/deployments/{cfg.deployment}"
        f"/chat/completions?api-version={cfg.api_version}"
    )
    body = {"messages": [{"role": "user", "content": prompt}], "store": False}
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, method="POST",
        headers={"Content-Type": "application/json", "api-key": api_key},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return LiveZdrResult(True, resp.status, False, cfg.endpoint, cfg.deployment, "Live request accepted", raw[:500])
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        return LiveZdrResult(False, exc.code, False, cfg.endpoint, cfg.deployment, f"HTTP {exc.code}", raw[:500])
    except urllib.error.URLError as exc:
        return LiveZdrResult(False, None, False, cfg.endpoint, cfg.deployment, str(exc.reason))
