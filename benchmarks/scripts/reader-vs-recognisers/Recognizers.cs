// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 Sūveryn Labs Ltd.
// suveryn-tracker#170: one JSON request per line on stdin {"text","culture"}; one JSON answer per line on stdout.
using System.Text.Json;
using Microsoft.Recognizers.Text.Number;
using Microsoft.Recognizers.Text.DateTime;
string? line;
var opts = new JsonSerializerOptions { Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping };
while ((line = Console.ReadLine()) != null) {
    var req = JsonDocument.Parse(line).RootElement;
    var text = req.GetProperty("text").GetString()!; var culture = req.GetProperty("culture").GetString()!;
    var nums = NumberRecognizer.RecognizeNumber(text, culture).Select(r => r.Resolution != null && r.Resolution.ContainsKey("value") ? r.Resolution["value"]?.ToString() : null).ToList();
    var dts = DateTimeRecognizer.RecognizeDateTime(text, culture).Select(r => r.Resolution != null && r.Resolution.ContainsKey("values")
        ? ((IEnumerable<object>)r.Resolution["values"]).Select(v => ((IDictionary<string, string>)v)).Select(d => new Dictionary<string, string>(d)).ToList()
        : new List<Dictionary<string, string>>()).ToList();
    Console.WriteLine(JsonSerializer.Serialize(new { nums, dts }, opts));
}
