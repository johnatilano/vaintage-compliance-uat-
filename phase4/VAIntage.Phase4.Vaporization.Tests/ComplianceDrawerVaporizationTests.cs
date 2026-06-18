using System.Text.Json;
using VAIntage.Guard.Core.Ledger;
using VAIntage.Guard.Core.Memory;
using VAIntage.Guard.Core.Session;
using VAIntage.Guard.Host;
using Xunit;

namespace VAIntage.Phase4.Vaporization.Tests;

internal sealed class TestGcCollector : IGcCollector
{
    public int Calls { get; private set; }
    public void Collect() => Calls++;
}

internal sealed class TestMemoryWiper : ISecureMemoryWiper
{
    public int WipeCalls { get; private set; }
    public void Wipe(ref string? value) { WipeCalls++; value = null; }
}

/// <summary>
/// Phase 4 — production path (RuntimeGcCollector) and unit path (test doubles).
/// </summary>
public class ComplianceDrawerVaporizationTests
{
    private static string SampleRaw() =>
        JsonSerializer.Deserialize<PhiFixtures>(
            File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "fixtures", "phi_samples.json")),
            new JsonSerializerOptions { PropertyNameCaseInsensitive = true })!.Samples[0].Raw;

    [Fact]
    public void ProductionPath_DismissComplianceDrawer_ClearsConcurrentDictionary()
    {
        var app = GuardApplication.CreateProduction();
        app.SimulateTypingSession(1, [SampleRaw()]);
        Assert.NotNull(app.PeekSessionCache());

        var result = app.DismissComplianceDrawer();

        Assert.Null(app.PeekSessionCache());
        Assert.True(result.CacheCleared);
        Assert.True(result.GcCollectCalled);
        Assert.True(result.MemoryWiped);
    }

    [Fact]
    public void UnitPath_Resolve_InvokesTestDoubles_ForDrawerLogic()
    {
        var cache = new VolatileSessionCache();
        var gc = new TestGcCollector();
        var wiper = new TestMemoryWiper();
        var drawer = new ComplianceDrawerService(cache, gc, wiper);

        cache.Put("session", SampleRaw(), new VAIntage.Guard.Core.Scrubbing.SafeHarborScrubber());
        var result = drawer.Resolve();

        Assert.Null(cache.PeekLatest());
        Assert.Equal(1, gc.Calls);
        Assert.True(wiper.WipeCalls >= 1);
        Assert.True(result.CacheCleared);
    }

    [Fact]
    public void VaporizationReport_WritesComplianceLedgerArtifact()
    {
        var app = GuardApplication.CreateProduction();
        app.SimulateTypingSession(1, [SampleRaw()]);
        var result = app.DismissComplianceDrawer();
        var path = ComplianceLedger.WriteVaporizationReport(result);

        Assert.True(File.Exists(path));
        Assert.Null(app.PeekSessionCache());
    }

    private sealed class PhiFixtures { public List<PhiSample> Samples { get; set; } = []; }
    private sealed class PhiSample { public string Raw { get; set; } = ""; }
}
