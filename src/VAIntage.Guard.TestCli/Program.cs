using System.Text.Json;
using VAIntage.Guard.Core.Api;
using VAIntage.Guard.Core.Session;
using VAIntage.Guard.Host;

namespace VAIntage.Guard.TestCli;

/// <summary>
/// guard-test.exe — UAT CLI bridge. John wires GuardApplication into production Guard;
/// this executable is the certification entry point for all four phases.
/// </summary>
internal static class Program
{
    public static int Main(string[] args)
    {
        if (args.Length == 0)
        {
            Console.Error.WriteLine(
                "Usage: guard-test <scrub|config|simulate|dismiss|cache-peek|watch-paths> [options]");
            return 1;
        }

        try
        {
            return args[0] switch
            {
                "scrub" => Scrub(args),
                "config" => Config(),
                "simulate" => Simulate(args),
                "dismiss" => Dismiss(),
                "cache-peek" => CachePeek(),
                "watch-paths" => WatchPaths(),
                _ => Unknown(args[0]),
            };
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex.Message);
            return 1;
        }
    }

    private static int Scrub(string[] args)
    {
        var idx = Array.IndexOf(args, "--text");
        if (idx < 0 || idx + 1 >= args.Length)
            throw new InvalidOperationException("usage: scrub --text <note>");

        var app = GuardApplication.CreateProduction();
        Console.WriteLine(app.Scrubber.Scrub(args[idx + 1]));
        return 0;
    }

    private static int Config()
    {
        var cfg = AzureOpenAiClientConfig.FromEnvironment();
        Console.WriteLine(JsonSerializer.Serialize(new
        {
            endpoint = cfg.Endpoint,
            deployment = cfg.Deployment,
            store = cfg.Store,
            data_logging = cfg.DataLogging,
            api_version = cfg.ApiVersion,
        }));
        return 0;
    }

    private static int Simulate(string[] args)
    {
        var count = 1000;
        var idx = Array.IndexOf(args, "--count");
        if (idx >= 0 && idx + 1 < args.Length)
            count = int.Parse(args[idx + 1]);

        var app = GuardApplication.CreateProduction();
        var simulated = app.SimulateTypingSession(count);
        Console.WriteLine(JsonSerializer.Serialize(new { simulated, cache_set = app.PeekSessionCache() != null }));
        return 0;
    }

    private static int Dismiss()
    {
        var app = GuardApplication.CreateProduction();
        var result = app.DismissComplianceDrawer();
        Console.WriteLine(JsonSerializer.Serialize(new
        {
            cache_cleared = result.CacheCleared,
            gc_collect_called = result.GcCollectCalled,
            memory_wiped = result.MemoryWiped,
            detail = result.Detail,
        }));
        return 0;
    }

    private static int CachePeek()
    {
        var state = GuardSessionState.Load();
        var app = GuardApplication.CreateProduction();
        var peek = app.PeekSessionCache() ?? state.LatestScrubbedNote;
        Console.WriteLine(string.IsNullOrEmpty(peek) ? "null" : peek);
        return 0;
    }

    private static int WatchPaths()
    {
        Console.WriteLine(JsonSerializer.Serialize(GuardApplication.GetWatchPaths()));
        return 0;
    }

    private static int Unknown(string cmd)
    {
        Console.Error.WriteLine($"unknown command: {cmd}");
        return 1;
    }
}
