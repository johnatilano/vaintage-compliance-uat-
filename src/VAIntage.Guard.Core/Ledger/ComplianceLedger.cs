using System.Text.Json;
using VAIntage.Guard.Core.Api;
using VAIntage.Guard.Core.Session;

namespace VAIntage.Guard.Core.Ledger;

public static class ComplianceLedger
{
    public static string RepoRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir != null)
        {
            if (File.Exists(Path.Combine(dir.FullName, "README.md"))
                && Directory.Exists(Path.Combine(dir.FullName, "fixtures")))
                return dir.FullName;
            dir = dir.Parent;
        }
        return Directory.GetCurrentDirectory();
    }

    public static string LedgerDir
    {
        get
        {
            var path = Path.Combine(RepoRoot(), "compliance-ledger");
            Directory.CreateDirectory(path);
            return path;
        }
    }

    public static string WritePayloadCapture(string scrubbed)
    {
        var path = Path.Combine(LedgerDir, "payload-capture.txt");
        File.WriteAllText(path,
            $"# VAIntage UAT Phase 1 — Request Payload Capture\n" +
            $"# Generated: {DateTime.UtcNow:O}\n\n{scrubbed}\n");
        return path;
    }

    public static string WriteVaporizationReport(VaporizationResult result)
    {
        var path = Path.Combine(LedgerDir, "vaporization-report.json");
        File.WriteAllText(path, JsonSerializer.Serialize(new
        {
            generated_at = DateTime.UtcNow.ToString("O"),
            phase = 4,
            passed = result.CacheCleared && result.GcCollectCalled && result.MemoryWiped,
            detail = result.Detail,
            gc_collect_called = result.GcCollectCalled,
            memory_wiped = result.MemoryWiped,
        }, new JsonSerializerOptions { WriteIndented = true }));
        return path;
    }

    public static string WriteCertificationSummary(IEnumerable<string> artifacts)
    {
        var path = Path.Combine(LedgerDir, "certification-summary.json");
        File.WriteAllText(path, JsonSerializer.Serialize(new
        {
            generated_at = DateTime.UtcNow.ToString("O"),
            artifacts = artifacts.ToList(),
            status = "PASS",
        }, new JsonSerializerOptions { WriteIndented = true }));
        return path;
    }
}
