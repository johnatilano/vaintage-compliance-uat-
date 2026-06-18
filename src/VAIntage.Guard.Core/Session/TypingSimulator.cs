using VAIntage.Guard.Core.Scrubbing;

namespace VAIntage.Guard.Core.Session;

/// <summary>
/// Heavy automation typing simulation — volatile RAM only via session cache.
/// </summary>
public sealed class TypingSimulator
{
    private readonly VolatileSessionCache _cache;
    private readonly SafeHarborScrubber _scrubber;

    public TypingSimulator(VolatileSessionCache cache, SafeHarborScrubber scrubber)
    {
        _cache = cache;
        _scrubber = scrubber;
    }

    public int Simulate(IReadOnlyList<string> notes)
    {
        for (var i = 0; i < notes.Count; i++)
            _cache.Put($"note-{i}", notes[i], _scrubber);
        return notes.Count;
    }
}
