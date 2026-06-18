namespace VAIntage.Guard.Core.Api;

public sealed class AzureOpenAiClientConfig
{
    public string Endpoint { get; init; } = "";
    public string Deployment { get; init; } = "";
    public string ApiVersion { get; init; } = "2024-12-01-preview";
    public bool Store { get; init; }
    public string DataLogging { get; init; } = "disabled";

    public bool IsZdrCompliant =>
        Store == false && DataLogging.Equals("disabled", StringComparison.OrdinalIgnoreCase);

    public static AzureOpenAiClientConfig FromEnvironment()
    {
        var storeRaw = Environment.GetEnvironmentVariable("OPENAI_STORE") ?? "false";
        return new AzureOpenAiClientConfig
        {
            Endpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT") ?? "",
            Deployment = Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT") ?? "",
            ApiVersion = Environment.GetEnvironmentVariable("AZURE_OPENAI_API_VERSION") ?? "2024-12-01-preview",
            Store = storeRaw is "true" or "1" || storeRaw.Equals("yes", StringComparison.OrdinalIgnoreCase),
            DataLogging = Environment.GetEnvironmentVariable("AZURE_DATA_LOGGING") ?? "disabled",
        };
    }
}
