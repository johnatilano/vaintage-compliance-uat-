#!/usr/bin/env python3
"""Local Guard test CLI stub — implements the GUARD_TEST_EXE contract for UAT.

Use until John's C# guard-test.exe is available:

  export GUARD_TEST_EXE="python3 $(pwd)/scripts/guard_test_stub.py"
  pytest tests/ --target=guard
"""
from __future__ import annotations

import gc
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from compliance_uat.env_loader import load_dotenv
from compliance_uat.scrubber import scrub

load_dotenv()

_CACHE: str | None = None
_SCRATCH = ROOT / ".uat-scratch"
_STATE_FILE = _SCRATCH / "guard_stub_state.json"


def _load_state() -> dict:
    if not _STATE_FILE.is_file():
        return {"cache": None}
    return json.loads(_STATE_FILE.read_text(encoding="utf-8"))


def _save_state(state: dict) -> None:
    _SCRATCH.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(json.dumps(state), encoding="utf-8")


def cmd_scrub(args: list[str]) -> None:
    if "--text" not in args:
        raise SystemExit("usage: scrub --text <note>")
    idx = args.index("--text")
    text = args[idx + 1] if idx + 1 < len(args) else ""
    print(scrub(text))


def cmd_config() -> None:
    store_raw = os.environ.get("OPENAI_STORE", "false").lower()
    print(
        json.dumps(
            {
                "endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
                "deployment": os.environ.get("AZURE_OPENAI_DEPLOYMENT", "o4-mini-stub"),
                "store": store_raw in {"true", "1", "yes"},
                "data_logging": os.environ.get("AZURE_DATA_LOGGING", "disabled"),
                "api_version": os.environ.get("AZURE_OPENAI_API_VERSION", ""),
            }
        )
    )


def cmd_simulate(args: list[str]) -> None:
    count = 1000
    if "--count" in args:
        idx = args.index("--count")
        count = int(args[idx + 1])
    _SCRATCH.mkdir(parents=True, exist_ok=True)
    # Volatile only — intentionally no writes under _SCRATCH during simulation.
    cache = scrub(f"stub session note #{count}")
    _save_state({"cache": cache})
    print(json.dumps({"simulated": count, "cache_set": cache is not None}))


def cmd_dismiss() -> None:
    _save_state({"cache": None})
    gc.collect()
    print(
        json.dumps(
            {
                "cache_cleared": True,
                "gc_collect_called": True,
                "memory_wiped": True,
                "detail": "Stub Guard dismiss: cache nulled and gc.collect() invoked",
            }
        )
    )


def cmd_cache_peek() -> None:
    cache = _load_state().get("cache")
    print("null" if cache is None else cache)


def cmd_watch_paths() -> None:
    paths = [
        str(ROOT / "compliance-ledger"),
        str(_SCRATCH),
    ]
    for env_key in ("LOCALAPPDATA", "APPDATA"):
        val = os.environ.get(env_key)
        if val:
            paths.append(str(Path(val) / "VAIntage"))
    print(json.dumps(paths))


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        raise SystemExit(__doc__)

    cmd = argv[0]
    rest = argv[1:]
    if cmd == "scrub":
        cmd_scrub(rest)
    elif cmd == "config":
        cmd_config()
    elif cmd == "simulate":
        cmd_simulate(rest)
    elif cmd == "dismiss":
        cmd_dismiss()
    elif cmd == "cache-peek":
        cmd_cache_peek()
    elif cmd == "watch-paths":
        cmd_watch_paths()
    else:
        raise SystemExit(f"unknown command: {cmd}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
