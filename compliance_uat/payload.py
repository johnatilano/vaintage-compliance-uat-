"""Serialize outbound API request bodies the way Guard sends them to Azure OpenAI."""
from __future__ import annotations

import json
from typing import Any


def build_chat_completion_payload(
    scrubbed_content: str,
    *,
    deployment: str = "",
    store: bool = False,
) -> dict[str, Any]:
    """Mirror Azure OpenAI chat-completions JSON shape with ZDR store flag."""
    body: dict[str, Any] = {
        "messages": [{"role": "user", "content": scrubbed_content}],
        "store": store,
    }
    if deployment:
        body["model"] = deployment
    return body


def serialize_outbound_payload(
    scrubbed_content: str,
    *,
    deployment: str = "",
    store: bool = False,
) -> str:
    """Return the exact JSON string that would be posted to the cloud endpoint."""
    return json.dumps(
        build_chat_completion_payload(
            scrubbed_content,
            deployment=deployment,
            store=store,
        ),
        separators=(",", ":"),
    )
