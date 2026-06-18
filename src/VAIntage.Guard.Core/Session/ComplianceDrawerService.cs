using System.Collections.Concurrent;
using VAIntage.Guard.Core.Memory;
using VAIntage.Guard.Core.Scrubbing;

namespace VAIntage.Guard.Core.Session;

public sealed class VolatileSessionCache
{
    private readonly ConcurrentDictionary<string, string> _entries = new();
    private string? _lastKey;

    public void Put(string key, string rawNote, SafeHarborScrubber scrubber)
    {
        _entries[key] = scrubber.Scrub(rawNote);
        _lastKey = key;
    }

    public string? PeekLatest() =>
        _lastKey != null && _entries.TryGetValue(_lastKey, out var v) ? v : null;

    public bool HasEntries => !_entries.IsEmpty;

    public void Clear(ISecureMemoryWiper wiper)
    {
        foreach (var key in _entries.Keys.ToList())
        {
            if (_entries.TryRemove(key, out var value))
                wiper.Wipe(ref value);
        }
        _entries.Clear();
        _lastKey = null;
    }
}

public sealed class VaporizationResult
{
    public bool CacheCleared { get; init; }
    public bool GcCollectCalled { get; init; }
    public bool MemoryWiped { get; init; }
    public string Detail { get; init; } = "";
}

/// <summary>
/// Compliance drawer Resolve/dismiss — Phase 4 vaporization event.
/// </summary>
public sealed class ComplianceDrawerService
{
    private readonly VolatileSessionCache _cache;
    private readonly IGcCollector _gc;
    private readonly ISecureMemoryWiper _wiper;

    public ComplianceDrawerService(VolatileSessionCache cache, IGcCollector gc, ISecureMemoryWiper wiper)
    {
        _cache = cache;
        _gc = gc;
        _wiper = wiper;
    }

    public VaporizationResult Resolve()
    {
        _cache.Clear(_wiper);
        _gc.Collect();
        return new VaporizationResult
        {
            CacheCleared = !_cache.HasEntries,
            GcCollectCalled = true,
            MemoryWiped = true,
            Detail = "Compliance drawer dismissed: ConcurrentDictionary cleared, GC.Collect invoked, memory wiped.",
        };
    }
}
