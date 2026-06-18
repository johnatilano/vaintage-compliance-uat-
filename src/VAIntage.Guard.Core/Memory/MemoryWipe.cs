namespace VAIntage.Guard.Core.Memory;

public interface IGcCollector { void Collect(); }
public sealed class RuntimeGcCollector : IGcCollector { public void Collect() => GC.Collect(); }

public interface ISecureMemoryWiper { void Wipe(ref string? value); }

public sealed class SecureMemoryWiper : ISecureMemoryWiper
{
    public void Wipe(ref string? value)
    {
        if (string.IsNullOrEmpty(value)) { value = null; return; }
        var chars = value.ToCharArray();
        Array.Fill(chars, '\0');
        value = null;
    }
}
