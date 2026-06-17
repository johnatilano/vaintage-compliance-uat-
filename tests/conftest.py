"""Pytest configuration and --target adapter selection."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from compliance_uat.adapters import get_target

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--target",
        action="store",
        default="mock",
        choices=["mock", "python_reference", "guard"],
        help="Privacy test adapter to exercise",
    )


@pytest.fixture(scope="session")
def target(request: pytest.FixtureRequest):
    name = request.config.getoption("--target")
    return get_target(name)


@pytest.fixture(scope="session")
def phi_samples() -> dict:
    return json.loads((FIXTURES / "phi_samples.json").read_text())


@pytest.fixture(scope="session")
def clinical_keywords() -> dict:
    return json.loads((FIXTURES / "clinical_keywords.json").read_text())
