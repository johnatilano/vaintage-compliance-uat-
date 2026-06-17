"""Pytest configuration and --target adapter selection."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from compliance_uat.adapters import get_target
from compliance_uat.env_loader import load_dotenv

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"

load_dotenv()


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--target",
        action="store",
        default="mock",
        choices=["mock", "python_reference", "guard"],
        help="Privacy test adapter to exercise",
    )
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="Run live Azure OpenAI ZDR integration test (Phase 2)",
    )
    parser.addoption(
        "--run-heavy",
        action="store_true",
        default=False,
        help="Run 1000-note heavy disk audit (Phase 3)",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "integration: live Azure OpenAI ZDR ping")
    config.addinivalue_line("markers", "heavy: 1000-note disk audit session")


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


@pytest.fixture(scope="session")
def run_live(request: pytest.FixtureRequest) -> bool:
    flag = request.config.getoption("--run-live")
    env = os.environ.get("RUN_LIVE_ZDR", "").lower() in {"1", "true", "yes"}
    return flag or env


@pytest.fixture(scope="session")
def run_heavy(request: pytest.FixtureRequest) -> bool:
    flag = request.config.getoption("--run-heavy")
    env = os.environ.get("RUN_HEAVY", "").lower() in {"1", "true", "yes"}
    return flag or env


@pytest.fixture(scope="session")
def heavy_session_count() -> int:
    raw = os.environ.get("HEAVY_SESSION_COUNT", "1000")
    return int(raw)
