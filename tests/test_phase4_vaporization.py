"""Phase 4 — Compliance drawer vaporization (RAM cleared on dismiss)."""
from __future__ import annotations


def test_overlay_dismiss_clears_memory_cache(target, phi_samples):
    raw = phi_samples["samples"][0]["raw"]
    target.simulate_typing_session([raw])
    assert target.peek_memory_cache() is not None, "cache should hold session text"

    target.dismiss_overlay()
    assert target.peek_memory_cache() is None, "cache must be null after dismiss"


def test_vaporization_report(target, phi_samples):
    from compliance_uat.ledger import write_vaporization_report

    raw = phi_samples["samples"][0]["raw"]
    target.simulate_typing_session([raw])
    target.dismiss_overlay()
    cleared = target.peek_memory_cache() is None

    path = write_vaporization_report(
        adapter=target.name,
        passed=cleared,
        detail="ConcurrentDictionary / volatile cache cleared on dismiss",
    )
    assert path.exists()
    assert cleared
