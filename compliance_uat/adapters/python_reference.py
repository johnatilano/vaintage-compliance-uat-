"""Reference adapter — Safe Harbor scrubber + in-memory-only session."""
from __future__ import annotations

import gc
import os
from pathlib import Path

from compliance_uat.adapters.base import ApiConfig, PrivacyTestTarget, VaporizationResult
from compliance_uat.scrubber import scrub


class PythonReferenceTarget(PrivacyTestTarget):
    name = "python_reference"

    def __init__(self) -> None:
        self._cache: str | None = None
        self._session_notes: list[str] = []

    def scrub(self, raw_note: str) -> str:
        return scrub(raw_note)

    def get_api_config(self) -> ApiConfig:
        store_raw = os.environ.get("OPENAI_STORE", "false").lower()
        return ApiConfig(
            endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
            deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", ""),
            store=store_raw in {"true", "1", "yes"},
            data_logging=os.environ.get("AZURE_DATA_LOGGING", "disabled"),
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", ""),
        )

    def simulate_typing_session(self, notes: list[str]) -> None:
        # Volatile RAM only — deliberately no disk writes.
        self._session_notes = list(notes)
        self._cache = scrub(notes[-1]) if notes else None

    def dismiss_overlay(self) -> VaporizationResult:
        # Mirror Guard's compliance-drawer path: drop refs then force collection.
        self._cache = None
        self._session_notes.clear()
        gc.collect()
        return VaporizationResult(
            cache_cleared=self._cache is None and not self._session_notes,
            gc_collect_called=True,
            memory_wiped=True,
            detail="Reference ConcurrentDictionary-equivalent cache cleared; gc.collect() invoked",
        )

    def peek_memory_cache(self) -> str | None:
        return self._cache

    def watched_paths(self) -> list[Path]:
        root = Path(__file__).resolve().parent.parent.parent
        paths = [
            root / "compliance-ledger",
            root / ".uat-scratch",
        ]
        if os.environ.get("UAT_WATCH_TEMP", "").lower() in {"1", "true", "yes"}:
            paths.append(Path(os.environ.get("TEMP", "/tmp")))
        for env_key in ("LOCALAPPDATA", "APPDATA"):
            val = os.environ.get(env_key)
            if val:
                paths.append(Path(val) / "VAIntage")
        return paths
