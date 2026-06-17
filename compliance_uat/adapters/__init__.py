"""Adapter factory for --target CLI flag."""
from __future__ import annotations

from compliance_uat.adapters.base import PrivacyTestTarget
from compliance_uat.adapters.guard_bridge import GuardBridgeTarget
from compliance_uat.adapters.mock import MockTarget
from compliance_uat.adapters.python_reference import PythonReferenceTarget

TARGETS: dict[str, type[PrivacyTestTarget]] = {
    "mock": MockTarget,
    "python_reference": PythonReferenceTarget,
    "guard": GuardBridgeTarget,
}


def get_target(name: str) -> PrivacyTestTarget:
    cls = TARGETS.get(name)
    if cls is None:
        raise ValueError(f"Unknown target {name!r}. Choose from: {', '.join(TARGETS)}")
    return cls()
