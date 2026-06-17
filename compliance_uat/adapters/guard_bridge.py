"""Bridge to John Robinson's C# Guard test build (stub until wired)."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from compliance_uat.adapters.base import ApiConfig, PrivacyTestTarget, VaporizationResult


class GuardBridgeTarget(PrivacyTestTarget):
    """Delegates to GUARD_TEST_EXE when available.

    Expected CLI contract (to be implemented in Guard):
      guard-test.exe scrub --text "..."
      guard-test.exe config
      guard-test.exe simulate --count 1000
      guard-test.exe dismiss
      guard-test.exe cache-peek
    """

    name = "guard"

    def __init__(self) -> None:
        exe = os.environ.get("GUARD_TEST_EXE", "")
        self._exe = Path(exe) if exe else None
        if not self._exe or not self._exe.is_file():
            raise FileNotFoundError(
                "GUARD_TEST_EXE not set or file missing. "
                "Point it at John's Guard test executable, or use "
                "scripts/guard_test_stub.py until the C# build is ready."
            )
        self._use_python = self._exe.suffix.lower() == ".py"

    def _run(self, *args: str) -> str:
        assert self._exe is not None
        cmd = [str(self._exe), *args]
        if self._use_python:
            import sys
            cmd = [sys.executable, *cmd]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def scrub(self, raw_note: str) -> str:
        return self._run("scrub", "--text", raw_note)

    def get_api_config(self) -> ApiConfig:
        import json
        raw = self._run("config")
        data = json.loads(raw)
        return ApiConfig(
            endpoint=data.get("endpoint", ""),
            deployment=data.get("deployment", ""),
            store=bool(data.get("store", True)),
            data_logging=str(data.get("data_logging", "unknown")),
            api_version=data.get("api_version", ""),
        )

    def simulate_typing_session(self, notes: list[str]) -> None:
        self._run("simulate", "--count", str(len(notes)))

    def dismiss_overlay(self) -> VaporizationResult:
        import json

        raw = self._run("dismiss")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return VaporizationResult(
                cache_cleared=True,
                gc_collect_called=False,
                detail=raw or "dismiss completed (no JSON metadata)",
            )
        return VaporizationResult(
            cache_cleared=bool(data.get("cache_cleared", True)),
            gc_collect_called=bool(data.get("gc_collect_called", False)),
            memory_wiped=bool(data.get("memory_wiped", False)),
            detail=str(data.get("detail", "")),
        )

    def peek_memory_cache(self) -> str | None:
        out = self._run("cache-peek")
        return None if out in {"", "null", "None"} else out

    def watched_paths(self) -> list[Path]:
        import json
        raw = self._run("watch-paths")
        return [Path(p) for p in json.loads(raw)]
