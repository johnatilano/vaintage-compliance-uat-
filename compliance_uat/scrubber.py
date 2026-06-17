"""Reference Safe Harbor scrubber (HIPAA 18-identifier subset).

Production Guard (C#) must produce equivalent output. This module is the
contract reference for Phase 1 assertions.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ScrubRule:
    name: str
    pattern: re.Pattern[str]
    token: str


# Order matters: more specific patterns before generic name capture.
SCRUB_RULES: tuple[ScrubRule, ...] = (
    ScrubRule("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
    ScrubRule("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[EMAIL]"),
    ScrubRule("phone", re.compile(
        r"\b(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b"
        r"|\b\d{3}-\d{4}\b"
    ), "[PHONE]"),
    ScrubRule("mrn", re.compile(r"\bMRN\s*#?\s*\d{4,}\b", re.I), "[MRN]"),
    ScrubRule("date", re.compile(r"\b(?:DOB[:\s]*)?(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", re.I), "[DATE]"),
    ScrubRule(
        "address",
        re.compile(r"\b\d{1,5}\s+\w+(?:\s+\w+){0,3}\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Drive|Dr|Ln|Lane)\b", re.I),
        "[ADDRESS]",
    ),
    ScrubRule("zip", re.compile(r"\b\d{5}(?:-\d{4})?\b"), "[ZIP]"),
    ScrubRule(
        "name",
        re.compile(
            r"\b(?:Patient\s+)?(?:Mr\.|Mrs\.|Ms\.|Dr\.)?\s*"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"
        ),
        "[NAME]",
    ),
)


def scrub(raw: str) -> str:
    """Return de-identified text with structural tokens."""
    out = raw
    for rule in SCRUB_RULES:
        if rule.name == "name":
            out = rule.pattern.sub(rule.token, out)
        else:
            out = rule.pattern.sub(rule.token, out)
    # Collapse duplicate whitespace introduced by replacements.
    return re.sub(r"\s{2,}", " ", out).strip()


def contains_raw_identifiers(raw: str, scrubbed: str, needles: list[str]) -> list[str]:
    """Return identifier substrings still present in scrubbed output."""
    leaks = []
    for needle in needles:
        if needle.lower() in scrubbed.lower():
            leaks.append(needle)
    return leaks
