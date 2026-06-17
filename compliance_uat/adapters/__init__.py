"""Adapter factory for --target CLI flag."""
from __future__ import annotations

import os
from pathlib import Path

from compliance_uat.adapters.base import PrivacyTestTarget
from compliance_uat.adapters.guard_bridge import GuardBridgeTarget
from compliance_uat.adapters.mock import MockTarget
from compliance_uat.adapters.python_reference import PythonReferenceTarget

ROOT = Path(__file__).resolve().parent.parent.parent
GUARD_STUB = ROOT / "scripts" / "guard_test_stub.py"

TARGETS: dict[str, type[PrivacyTestTarget]] = {
    "mock": MockTarget,
    "python_reference": PythonReferenceTarget,
    "guard": GuardBridgeTarget,
}


def get_target(name: str) -> PrivacyTestTarget:
    cls = TARGETS.get(name)
    if cls is None:
        raise ValueError(f"Unknown target {name!r}. Choose from: {', '.join(TARGETS)}")
    if name == "guard" and not os.environ.get("GUARD_TEST_EXE") and GUARD_STUB.is_file():
        os.environ["GUARD_TEST_EXE"] = str(GUARD_STUB)
    return cls()
