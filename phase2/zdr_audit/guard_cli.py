"""Invoke guard-test.exe for Phase 2 config and Phase 3 hooks."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def resolve_guard_test_exe() -> Path | None:
    env = os.environ.get("GUARD_TEST_EXE", "").strip()
    if env:
        p = Path(env)
        if p.is_file():
            return p

    candidates = [
        ROOT / "src/VAIntage.Guard.TestCli/bin/Release/net8.0/guard-test.exe",
        ROOT / "src/VAIntage.Guard.TestCli/bin/Debug/net8.0/guard-test.exe",
        ROOT / "src/VAIntage.Guard.TestCli/bin/Release/net8.0/guard-test",
        ROOT / "src/VAIntage.Guard.TestCli/bin/Debug/net8.0/guard-test",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def run_guard_test(*args: str) -> str:
    exe = resolve_guard_test_exe()
    if not exe:
        raise FileNotFoundError(
            "guard-test not found. Build with: dotnet build src/VAIntage.Guard.TestCli -c Release"
        )
    cmd = [str(exe), *args]
    if exe.suffix.lower() == ".py":
        cmd = [sys.executable, *cmd]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def fetch_api_config_json() -> dict:
    raw = run_guard_test("config")
    return json.loads(raw)


def simulate_typing(count: int) -> dict:
    raw = run_guard_test("simulate", "--count", str(count))
    return json.loads(raw)


def fetch_watch_paths() -> list[str]:
    raw = run_guard_test("watch-paths")
    return json.loads(raw)
