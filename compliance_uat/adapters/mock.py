"""CI-friendly adapter — proves test harness wiring without cloud or Windows."""
from __future__ import annotations

import gc
from pathlib import Path

from compliance_uat.adapters.base import ApiConfig, PrivacyTestTarget, VaporizationResult


class MockTarget(PrivacyTestTarget):
    name = "mock"

    def __init__(self) -> None:
        self._cache: str | None = None

    def scrub(self, raw_note: str) -> str:
        # Pretend scrubbing: replace any capitalized two-word name pattern.
        return raw_note.replace("John Doe", "[NAME]").replace("Mary Smith", "[NAME]")

    def get_api_config(self) -> ApiConfig:
        return ApiConfig(
            endpoint="https://mock.openai.azure.com/",
            deployment="o4-mini-mock",
            store=False,
            data_logging="disabled",
        )

    def simulate_typing_session(self, notes: list[str]) -> None:
        self._cache = notes[-1] if notes else None

    def dismiss_overlay(self) -> VaporizationResult:
        self._cache = None
        gc.collect()
        return VaporizationResult(
            cache_cleared=self._cache is None,
            gc_collect_called=True,
            memory_wiped=True,
            detail="Mock volatile cache cleared; gc.collect() invoked",
        )

    def peek_memory_cache(self) -> str | None:
        return self._cache

    def watched_paths(self) -> list[Path]:
        return [Path("compliance-ledger")]
