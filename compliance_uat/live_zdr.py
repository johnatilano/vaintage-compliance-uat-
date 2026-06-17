"""Optional live Azure OpenAI ping to prove ZDR request path (Phase 2 integration)."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from compliance_uat.adapters.base import ApiConfig
from compliance_uat.payload import build_chat_completion_payload


@dataclass(frozen=True)
class LiveZdrResult:
    ok: bool
    status_code: int | None
    store_in_body: bool
    endpoint: str
    deployment: str
    detail: str
    response_excerpt: str = ""


def live_zdr_ping(cfg: ApiConfig, *, scrubbed_prompt: str = "UAT ZDR connectivity probe.") -> LiveZdrResult:
    """POST a minimal chat completion with store=false to the configured deployment."""
    api_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
    if not api_key:
        return LiveZdrResult(
            ok=False,
            status_code=None,
            store_in_body=cfg.store,
            endpoint=cfg.endpoint,
            deployment=cfg.deployment,
            detail="AZURE_OPENAI_API_KEY not set",
        )
    if not cfg.endpoint or not cfg.deployment:
        return LiveZdrResult(
            ok=False,
            status_code=None,
            store_in_body=cfg.store,
            endpoint=cfg.endpoint,
            deployment=cfg.deployment,
            detail="AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_DEPLOYMENT not set",
        )

    api_version = cfg.api_version or "2024-12-01-preview"
    url = (
        f"{cfg.endpoint.rstrip('/')}/openai/deployments/{cfg.deployment}"
        f"/chat/completions?api-version={api_version}"
    )
    body = build_chat_completion_payload(scrubbed_prompt, deployment=cfg.deployment, store=False)
    payload = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "api-key": api_key,
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return LiveZdrResult(
                ok=True,
                status_code=resp.status,
                store_in_body=False,
                endpoint=cfg.endpoint,
                deployment=cfg.deployment,
                detail="Live chat completion accepted with store=false",
                response_excerpt=raw[:500],
            )
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        return LiveZdrResult(
            ok=False,
            status_code=exc.code,
            store_in_body=False,
            endpoint=cfg.endpoint,
            deployment=cfg.deployment,
            detail=f"HTTP {exc.code}: {exc.reason}",
            response_excerpt=raw[:500],
        )
    except urllib.error.URLError as exc:
        return LiveZdrResult(
            ok=False,
            status_code=None,
            store_in_body=False,
            endpoint=cfg.endpoint,
            deployment=cfg.deployment,
            detail=f"Network error: {exc.reason}",
        )
