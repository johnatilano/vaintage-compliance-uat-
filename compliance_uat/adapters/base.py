"""Adapter interface — plug in Guard, reference stub, or mock."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ApiConfig:
    endpoint: str
    deployment: str
    store: bool
    data_logging: str
    api_version: str = ""

    def zdr_compliant(self) -> bool:
        return self.store is False and self.data_logging.lower() in {
            "disabled", "off", "false", "none",
        }


@dataclass
class DiskAuditResult:
    files_scanned: int
    new_files: int
    keyword_hits: dict[str, int] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return sum(self.keyword_hits.values()) == 0


class PrivacyTestTarget(ABC):
    """Any Layer 2 app implements this contract for the generic test suite."""

    name: str

    @abstractmethod
    def scrub(self, raw_note: str) -> str: ...

    @abstractmethod
    def get_api_config(self) -> ApiConfig: ...

    @abstractmethod
    def simulate_typing_session(self, notes: list[str]) -> None: ...

    @abstractmethod
    def dismiss_overlay(self) -> None: ...

    @abstractmethod
    def peek_memory_cache(self) -> str | None: ...

    @abstractmethod
    def watched_paths(self) -> list[Path]: ...

    def snapshot_files(self) -> set[Path]:
        """Inventory readable files under watched paths."""
        found: set[Path] = set()
        for root in self.watched_paths():
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if path.is_file():
                    found.add(path.resolve())
        return found

    def audit_disk(self, before: set[Path], after: set[Path], keywords: list[str]) -> DiskAuditResult:
        new_files = after - before
        hits: dict[str, int] = {k: 0 for k in keywords}
        scanned = 0
        text_ext = {".log", ".txt", ".json", ".db", ".sqlite", ".cache", ".md"}
        # Phase 3 proves a negative on *new* persistent writes during the session.
        for path in new_files:
            if path.suffix.lower() not in text_ext:
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="ignore").lower()
            except OSError:
                continue
            scanned += 1
            for kw in keywords:
                if kw.lower() in content:
                    hits[kw] += content.count(kw.lower())
        return DiskAuditResult(files_scanned=scanned, new_files=len(new_files), keyword_hits=hits)
