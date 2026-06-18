using System.Security.Cryptography;
using System.Text;
using VAIntage.Guard.Core.Scrubbing;

namespace VAIntage.Guard.Core.Payload;

/// <summary>
/// Cryptographic attestation that outbound JSON contains no raw PHI byte patterns.
/// SHA-256 fingerprint of the scrubbed payload + explicit PHI needle scan.
/// </summary>
public sealed class PayloadAttestation
{
    public string PayloadSha256 { get; init; } = "";
    public bool PhiBytesAbsent { get; init; }
    public IReadOnlyList<string> PhiLeaks { get; init; } = Array.Empty<string>();

    public bool Passed => PhiBytesAbsent;

    public static PayloadAttestation Attest(string payloadJson, IEnumerable<string> phiNeedles)
    {
        var needles = phiNeedles.ToList();
        var leaks = needles
            .Where(n => payloadJson.Contains(n, StringComparison.OrdinalIgnoreCase))
            .ToList();

        var hash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(payloadJson))).ToLowerInvariant();

        return new PayloadAttestation
        {
            PayloadSha256 = hash,
            PhiBytesAbsent = leaks.Count == 0,
            PhiLeaks = leaks,
        };
    }

    public static PayloadAttestation AttestScrubbedContent(string scrubbedContent, IEnumerable<string> phiNeedles)
    {
        var leaks = new SafeHarborScrubber().FindLeaks(scrubbedContent, phiNeedles);
        var hash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(scrubbedContent))).ToLowerInvariant();
        return new PayloadAttestation
        {
            PayloadSha256 = hash,
            PhiBytesAbsent = leaks.Count == 0,
            PhiLeaks = leaks,
        };
    }
}
