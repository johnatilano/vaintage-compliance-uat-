"""Phase 4 — Compliance drawer vaporization (RAM cleared on dismiss)."""
from __future__ import annotations


def test_overlay_dismiss_clears_memory_cache(target, phi_samples):
    raw = phi_samples["samples"][0]["raw"]
    target.simulate_typing_session([raw])
    assert target.peek_memory_cache() is not None, "cache should hold session text"

    result = target.dismiss_overlay()
    assert target.peek_memory_cache() is None, "cache must be null after dismiss"
    assert result.cache_cleared, result.detail


def test_vaporization_invokes_gc_and_wipes_memory(target, phi_samples):
    raw = phi_samples["samples"][0]["raw"]
    target.simulate_typing_session([raw])

    result = target.dismiss_overlay()
    assert result.cache_cleared
    assert target.peek_memory_cache() is None

    if target.name == "guard":
        assert result.gc_collect_called, "Guard dismiss must invoke GC.Collect()"
        assert result.memory_wiped, "Guard dismiss must securely wipe volatile cache"
    else:
        assert result.gc_collect_called, "dismiss must invoke gc.collect()"
        assert result.memory_wiped


def test_vaporization_report(target, phi_samples):
    from compliance_uat.ledger import write_vaporization_report

    raw = phi_samples["samples"][0]["raw"]
    target.simulate_typing_session([raw])
    result = target.dismiss_overlay()
    cleared = target.peek_memory_cache() is None

    path = write_vaporization_report(
        adapter=target.name,
        passed=cleared and result.cache_cleared,
        detail=result.detail or "ConcurrentDictionary / volatile cache cleared on dismiss",
        gc_collect_called=result.gc_collect_called,
        memory_wiped=result.memory_wiped,
    )
    assert path.exists()
    assert cleared
