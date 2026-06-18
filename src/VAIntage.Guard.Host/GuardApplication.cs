using System.Text.Json;
using VAIntage.Guard.Core.Api;
using VAIntage.Guard.Core.Memory;
using VAIntage.Guard.Core.Payload;
using VAIntage.Guard.Core.Scrubbing;
using VAIntage.Guard.Core.Session;

namespace VAIntage.Guard.Host;

/// <summary>
/// Production wiring facade — single entry point John integrates into Guard desktop agent.
/// All UAT phases exercise this type (not ad-hoc stubs).
/// </summary>
public sealed class GuardApplication
{
    public SafeHarborScrubber Scrubber { get; }
    public AzureOpenAiClientConfig Config { get; }
    public OutboundPayloadHandler PayloadHandler { get; }
    public VolatileSessionCache SessionCache { get; }
    public ComplianceDrawerService DrawerService { get; }
    public IGcCollector GcCollector { get; }
    public ISecureMemoryWiper MemoryWiper { get; }

    private GuardApplication(
        AzureOpenAiClientConfig config,
        IGcCollector gc,
        ISecureMemoryWiper wiper)
    {
        Config = config;
        GcCollector = gc;
        MemoryWiper = wiper;
        Scrubber = new SafeHarborScrubber();
        PayloadHandler = new OutboundPayloadHandler(Scrubber, config);
        SessionCache = new VolatileSessionCache();
        DrawerService = new ComplianceDrawerService(SessionCache, gc, wiper);
    }

    /// <summary>Production path — real GC.Collect() and secure memory wipe.</summary>
    public static GuardApplication CreateProduction() =>
        new(AzureOpenAiClientConfig.FromEnvironment(), new RuntimeGcCollector(), new SecureMemoryWiper());

    /// <summary>Phase 1 — outbound API payload (scrubbed JSON with store:false).</summary>
    public string BuildOutboundPayloadJson(string rawClinicalNote) =>
        PayloadHandler.BuildPayloadJson(rawClinicalNote);

    /// <summary>Phase 1 — cryptographic attestation of serialized payload.</summary>
    public PayloadAttestation AttestOutboundPayload(string rawClinicalNote, IEnumerable<string> phiNeedles)
    {
        var json = BuildOutboundPayloadJson(rawClinicalNote);
        return PayloadAttestation.Attest(json, phiNeedles);
    }

    /// <summary>Phase 3 — simulate counselor typing; notes stay in volatile cache only.</summary>
    public int SimulateTypingSession(int noteCount, IReadOnlyList<string>? notes = null)
    {
        notes ??= BuildDefaultClinicalNotes(noteCount);
        var count = new TypingSimulator(SessionCache, Scrubber).Simulate(notes);
        var state = new GuardSessionState
        {
            LatestScrubbedNote = SessionCache.PeekLatest(),
            NotesSimulated = count,
        };
        state.Save();
        return count;
    }

    /// <summary>Phase 4 — compliance drawer Resolve/dismiss.</summary>
    public VaporizationResult DismissComplianceDrawer()
    {
        var result = DrawerService.Resolve();
        GuardSessionState.Clear();
        return result;
    }

    public string? PeekSessionCache() => SessionCache.PeekLatest();

    public static IReadOnlyList<string> GetWatchPaths()
    {
        var root = GuardSessionState.RepoRoot();
        var paths = new List<string>
        {
            Path.Combine(root, "compliance-ledger"),
            Path.Combine(root, ".uat-scratch"),
        };

        var local = Environment.GetEnvironmentVariable("LOCALAPPDATA");
        if (!string.IsNullOrWhiteSpace(local))
            paths.Add(Path.Combine(local, "VAIntage"));

        var roaming = Environment.GetEnvironmentVariable("APPDATA");
        if (!string.IsNullOrWhiteSpace(roaming))
            paths.Add(Path.Combine(roaming, "VAIntage"));

        var temp = Path.GetTempPath();
        if (!string.IsNullOrWhiteSpace(temp))
            paths.Add(temp);

        var install = Environment.GetEnvironmentVariable("ProgramFiles");
        if (!string.IsNullOrWhiteSpace(install))
            paths.Add(Path.Combine(install, "VAIntage"));

        return paths;
    }

    private static List<string> BuildDefaultClinicalNotes(int count)
    {
        var fixturePath = Path.Combine(GuardSessionState.RepoRoot(), "fixtures", "clinical_keywords.json");
        var keywords = new[] { "substance", "anxiety", "transportation", "methadone", "counseling" };
        var template = "Patient reports {keyword} concerns during today's session. No illicit use reported.";

        if (File.Exists(fixturePath))
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(fixturePath));
            if (doc.RootElement.TryGetProperty("session_keywords", out var kwEl))
                keywords = kwEl.EnumerateArray().Select(e => e.GetString()!).ToArray();
            if (doc.RootElement.TryGetProperty("session_note_template", out var tplEl))
                template = tplEl.GetString() ?? template;
        }

        return Enumerable.Range(0, count)
            .Select(i => template.Replace("{keyword}", keywords[i % keywords.Length]))
            .ToList();
    }
}
