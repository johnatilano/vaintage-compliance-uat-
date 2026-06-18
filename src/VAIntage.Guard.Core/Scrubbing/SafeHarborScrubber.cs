namespace VAIntage.Guard.Core.Scrubbing;

/// <summary>
/// HIPAA Safe Harbor scrubbing. Person names become [CLIENT_REF] per UAT spec.
/// John: wire this before any outbound Azure OpenAI payload is serialized.
/// </summary>
public sealed class SafeHarborScrubber
{
    public const string ClientRefToken = "[CLIENT_REF]";
    public const string DateToken = "[DATE]";
    public const string PhoneToken = "[PHONE]";
    public const string EmailToken = "[EMAIL]";
    public const string SsnToken = "[SSN]";
    public const string MrnToken = "[MRN]";
    public const string AddressToken = "[ADDRESS]";
    public const string ZipToken = "[ZIP]";

    private static readonly (string Pattern, string Token)[] Rules =
    [
        (@"\b\d{3}-\d{2}-\d{4}\b", SsnToken),
        (@"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", EmailToken),
        (@"\b(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b|\b\d{3}-\d{4}\b", PhoneToken),
        (@"\bMRN\s*#?\s*\d{4,}\b", MrnToken),
        (@"\b(?:DOB[:\s]*)?(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", DateToken),
        (@"\b\d{1,5}\s+\w+(?:\s+\w+){0,3}\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Drive|Dr|Ln|Lane)\b", AddressToken),
        (@"\b\d{5}(?:-\d{4})?\b", ZipToken),
        (@"\b(?:Patient\s+)?(?:Mr\.|Mrs\.|Ms\.|Dr\.)?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", ClientRefToken),
    ];

    public string Scrub(string raw)
    {
        var output = raw;
        foreach (var (pattern, token) in Rules)
            output = System.Text.RegularExpressions.Regex.Replace(
                output, pattern, token, System.Text.RegularExpressions.RegexOptions.IgnoreCase);
        return System.Text.RegularExpressions.Regex.Replace(output, @"\s{2,}", " ").Trim();
    }

    public IReadOnlyList<string> FindLeaks(string scrubbed, IEnumerable<string> needles) =>
        needles.Where(n => scrubbed.Contains(n, StringComparison.OrdinalIgnoreCase)).ToList();
}
