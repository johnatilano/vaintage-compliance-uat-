"""Phase 3 — Negative log audit (no clinical narrative on disk)."""
from __future__ import annotations

import pytest


def test_typing_session_leaves_no_keywords_on_disk(target, clinical_keywords):
    keywords = clinical_keywords["session_keywords"]
    template = clinical_keywords["session_note_template"]
    notes = [template.format(keyword=kw) for kw in keywords]

    before = target.snapshot_files()
    target.simulate_typing_session(notes)
    after = target.snapshot_files()

    result = target.audit_disk(before, after, keywords)
    assert result.passed, f"Keywords found on disk: {result.keyword_hits}"


def test_disk_audit_manifest(target, clinical_keywords):
    from compliance_uat.ledger import write_disk_audit_manifest

    keywords = clinical_keywords["session_keywords"]
    template = clinical_keywords["session_note_template"]
    notes = [template.format(keyword=kw) for kw in keywords]

    before = target.snapshot_files()
    target.simulate_typing_session(notes)
    after = target.snapshot_files()
    result = target.audit_disk(before, after, keywords)

    path = write_disk_audit_manifest(
        adapter=target.name,
        files_scanned=result.files_scanned,
        new_files=result.new_files,
        keyword_hits=result.keyword_hits,
        passed=result.passed,
    )
    assert path.exists()


@pytest.mark.heavy
def test_heavy_typing_session_leaves_no_keywords_on_disk(
    target, clinical_keywords, run_heavy, heavy_session_count
):
    """Simulate 1,000 automated notes and prove zero clinical narrative on disk."""
    if not run_heavy:
        pytest.skip("Pass --run-heavy or set RUN_HEAVY=1 for 1000-note audit")

    keywords = clinical_keywords["session_keywords"]
    template = clinical_keywords["session_note_template"]
    notes = [
        template.format(keyword=keywords[i % len(keywords)])
        for i in range(heavy_session_count)
    ]

    before = target.snapshot_files()
    target.simulate_typing_session(notes)
    after = target.snapshot_files()

    result = target.audit_disk(before, after, keywords)
    assert result.passed, (
        f"After {heavy_session_count} notes, keywords on disk: {result.keyword_hits}"
    )

    from compliance_uat.ledger import write_disk_audit_manifest

    path = write_disk_audit_manifest(
        adapter=target.name,
        files_scanned=result.files_scanned,
        new_files=result.new_files,
        keyword_hits=result.keyword_hits,
        passed=result.passed,
    )
    assert path.exists()
