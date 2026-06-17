#!/usr/bin/env python3
"""Run all four compliance phases and write the executive ledger."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="VAIntage compliance UAT full ledger run")
    parser.add_argument(
        "--target",
        default="python_reference",
        choices=["mock", "python_reference", "guard"],
    )
    parser.add_argument("--run-live", action="store_true", help="Include live Azure ZDR ping")
    parser.add_argument("--run-heavy", action="store_true", help="Include 1000-note disk audit")
    args = parser.parse_args()

    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", f"--target={args.target}"]
    if args.run_live:
        cmd.append("--run-live")
    if args.run_heavy:
        cmd.append("--run-heavy")

    print(f"Running compliance UAT with adapter: {args.target}")
    result = subprocess.run(
        cmd,
        cwd=ROOT,
    )
    if result.returncode != 0:
        print("Tests failed — ledger may be incomplete.")
        return result.returncode

    ledger = ROOT / "compliance-ledger"
    print("\nCompliance ledger artifacts:")
    for path in sorted(ledger.glob("*")):
        if path.name == ".gitkeep":
            continue
        print(f"  • {path.name}")

    summary = {
        "adapter": args.target,
        "artifacts": [p.name for p in ledger.glob("*") if p.name != ".gitkeep"],
        "status": "PASS",
    }
    (ledger / "certification-summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print("\nCertification summary written to compliance-ledger/certification-summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
