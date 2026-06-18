using System.Text.Json;
using System.Text.Json.Serialization;
using VAIntage.Guard.Core.Api;
using VAIntage.Guard.Core.Scrubbing;

namespace VAIntage.Guard.Core.Payload;

/// <summary>
/// Outbound API payload handler — UAT Phase 1 intercepts serialized JSON from this type.
/// </summary>
public sealed class OutboundPayloadHandler
{
    private readonly SafeHarborScrubber _scrubber;
    private readonly AzureOpenAiClientConfig _config;
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    public OutboundPayloadHandler(SafeHarborScrubber scrubber, AzureOpenAiClientConfig config)
    {
        _scrubber = scrubber;
        _config = config;
    }

    public string BuildPayloadJson(string rawClinicalNote)
    {
        var scrubbed = _scrubber.Scrub(rawClinicalNote);
        var body = new ChatCompletionRequest
        {
            Model = string.IsNullOrWhiteSpace(_config.Deployment) ? null : _config.Deployment,
            Store = false,
            Messages = [new ChatMessage { Role = "user", Content = scrubbed }],
        };
        return JsonSerializer.Serialize(body, JsonOptions);
    }

    public ChatCompletionRequest ParsePayload(string json) =>
        JsonSerializer.Deserialize<ChatCompletionRequest>(json, JsonOptions)
        ?? throw new InvalidOperationException("Invalid payload JSON.");

    public sealed class ChatCompletionRequest
    {
        public string? Model { get; set; }
        public bool Store { get; set; }
        public List<ChatMessage> Messages { get; set; } = [];
    }

    public sealed class ChatMessage
    {
        public string Role { get; set; } = "user";
        public string Content { get; set; } = "";
    }
}
