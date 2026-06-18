"""Pytest configuration for Phase 2."""
from __future__ import annotations

import os

import pytest

from zdr_audit.env_loader import load_dotenv

load_dotenv()


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--run-live", action="store_true", help="Live Azure ZDR ping")


@pytest.fixture(scope="session")
def run_live(request: pytest.FixtureRequest) -> bool:
    return request.config.getoption("--run-live") or os.environ.get("RUN_LIVE_ZDR", "").lower() in {"1", "true", "yes"}
