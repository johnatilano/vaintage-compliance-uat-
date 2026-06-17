"""Phase 1 — Safe Harbor scrubbing (no PHI in outbound payload)."""
from __future__ import annotations

import pytest

from compliance_uat.ledger import write_payload_capture
from compliance_uat.scrubber import contains_raw_identifiers


def test_scrub_removes_known_identifiers(target, phi_samples):
    sample = phi_samples["samples"][0]
    scrubbed = target.scrub(sample["raw"])
    leaks = contains_raw_identifiers(
        sample["raw"], scrubbed, phi_samples["must_not_appear_after_scrub"]
    )
    # mock adapter only stubs two names; python_reference should pass fully
    if target.name == "mock":
        assert "John Doe" not in scrubbed
    else:
        assert leaks == [], f"PHI leaked after scrub: {leaks}"


def test_scrub_uses_structural_tokens(target, phi_samples):
    if target.name == "mock":
        pytest.skip("mock adapter uses minimal replacements")

    sample = phi_samples["samples"][0]
    scrubbed = target.scrub(sample["raw"])
    assert any(tok in scrubbed for tok in phi_samples["expected_tokens"])


def test_all_samples_scrub_clean_for_reference(target, phi_samples):
    if target.name != "python_reference":
        pytest.skip("full identifier sweep runs on python_reference adapter")

    needles = phi_samples["must_not_appear_after_scrub"]
    for sample in phi_samples["samples"]:
        scrubbed = target.scrub(sample["raw"])
        leaks = contains_raw_identifiers(sample["raw"], scrubbed, needles)
        assert leaks == [], f"{sample['id']}: leaked {leaks}"


def test_payload_capture_ledger(target, phi_samples):
    sample = phi_samples["samples"][0]
    scrubbed = target.scrub(sample["raw"])
    path = write_payload_capture(scrubbed, target.name)
    assert path.exists()
    text = path.read_text()
    assert "[NAME]" in text or target.name == "mock"
