using System.Text.Json;

namespace VAIntage.Guard.Core.Session;

/// <summary>
/// Cross-process session state for guard-test.exe CLI (volatile metadata on disk for UAT only).
/// </summary>
public sealed class GuardSessionState
{
    public string? LatestScrubbedNote { get; set; }
    public int NotesSimulated { get; set; }

    public static string StateFilePath()
    {
        var root = RepoRoot();
        var scratch = Path.Combine(root, ".uat-scratch");
        Directory.CreateDirectory(scratch);
        return Path.Combine(scratch, "guard_session.json");
    }

    public static GuardSessionState Load()
    {
        var path = StateFilePath();
        if (!File.Exists(path)) return new GuardSessionState();
        return JsonSerializer.Deserialize<GuardSessionState>(File.ReadAllText(path)) ?? new GuardSessionState();
    }

    public void Save()
    {
        File.WriteAllText(StateFilePath(), JsonSerializer.Serialize(this));
    }

    public static void Clear()
    {
        var path = StateFilePath();
        if (File.Exists(path)) File.Delete(path);
    }

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
}
