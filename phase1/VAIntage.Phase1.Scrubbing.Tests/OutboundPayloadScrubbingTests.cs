using System.Text.Json;
using VAIntage.Guard.Core.Ledger;
using VAIntage.Guard.Core.Payload;
using VAIntage.Guard.Core.Scrubbing;
using VAIntage.Guard.Host;
using Xunit;

namespace VAIntage.Phase1.Scrubbing.Tests;

/// <summary>
/// Phase 1 — C# xUnit integration test via production GuardApplication wiring.
/// Intercepts outbound API payload handler; SHA-256 attestation; zero raw PHI in JSON.
/// </summary>
public class OutboundPayloadIntegrationTests
{
    private static PhiFixtures Fixtures() =>
        JsonSerializer.Deserialize<PhiFixtures>(
            File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "fixtures", "phi_samples.json")),
            new JsonSerializerOptions { PropertyNameCaseInsensitive = true })!;

    [Fact]
    public void GuardApplication_OutboundJson_ContainsZeroRawPhi_AndClientRefToken()
    {
        var fixtures = Fixtures();
        var app = GuardApplication.CreateProduction();
        var raw = fixtures.Samples[0].Raw;

        var payloadJson = app.BuildOutboundPayloadJson(raw);

        foreach (var needle in fixtures.MustNotAppearAfterScrub)
            Assert.DoesNotContain(needle, payloadJson, StringComparison.OrdinalIgnoreCase);

        Assert.Contains(SafeHarborScrubber.ClientRefToken, payloadJson);

        var body = app.PayloadHandler.ParsePayload(payloadJson);
        Assert.False(body.Store);
    }

    [Fact]
    public void GuardApplication_PayloadAttestation_Sha256_WithNoPhiBytes()
    {
        var fixtures = Fixtures();
        var app = GuardApplication.CreateProduction();
        var attestation = app.AttestOutboundPayload(fixtures.Samples[0].Raw, fixtures.MustNotAppearAfterScrub);

        Assert.True(attestation.Passed, string.Join(", ", attestation.PhiLeaks));
        Assert.False(string.IsNullOrEmpty(attestation.PayloadSha256));
        Assert.Equal(64, attestation.PayloadSha256.Length);
        Assert.Empty(attestation.PhiLeaks);
    }

    [Fact]
    public void PayloadCapture_WritesDeIdentifiedRequestToComplianceLedger()
    {
        var app = GuardApplication.CreateProduction();
        var fixtures = Fixtures();
        var scrubbed = app.Scrubber.Scrub(fixtures.Samples[0].Raw);
        var path = ComplianceLedger.WritePayloadCapture(scrubbed);

        Assert.True(File.Exists(path));
        var text = File.ReadAllText(path);
        Assert.Contains(SafeHarborScrubber.ClientRefToken, text);
        Assert.DoesNotContain("John Doe", text, StringComparison.OrdinalIgnoreCase);
    }

    private sealed class PhiFixtures
    {
        public List<PhiSample> Samples { get; set; } = [];
        public List<string> MustNotAppearAfterScrub { get; set; } = [];
    }

    private sealed class PhiSample { public string Raw { get; set; } = ""; }
}
