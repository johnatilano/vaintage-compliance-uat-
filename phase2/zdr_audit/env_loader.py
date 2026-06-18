"""Load .env without external dependencies."""
from __future__ import annotations

import os
from pathlib import Path


def load_dotenv() -> None:
    root = Path(__file__).resolve().parent.parent.parent
    env_path = root / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))
