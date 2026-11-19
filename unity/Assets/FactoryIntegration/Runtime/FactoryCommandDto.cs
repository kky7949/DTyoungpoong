using System;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace Youngpoong.Integration
{
    [Serializable]
    public sealed class FactoryCommandDto
    {
        [JsonProperty(Required = Required.Always)] public string command_id;
        [JsonProperty(Required = Required.Always)] public string command;
        [JsonProperty(Required = Required.Always)] public MaterialDto material;
        [JsonProperty(Required = Required.Always)] public ProcessConditionsDto process_conditions;
        [JsonProperty(Required = Required.Always)] public RecoveryDto expected_recovery;

        public void Validate()
        {
            if (string.IsNullOrWhiteSpace(command_id) || command != "apply_and_start")
                throw new ArgumentException("지원하지 않거나 ID가 없는 명령입니다.");
            if (material == null || process_conditions == null || expected_recovery == null)
                throw new ArgumentException("명령의 필수 정보가 없습니다.");
            if (material.feed_amount_kg.HasValue) Nonnegative(material.feed_amount_kg.Value);
            OptionalPercentage(material.ni_content_pct);
            OptionalPercentage(material.co_content_pct);
            OptionalPercentage(material.li_content_pct);
            OptionalPercentage(material.mn_content_pct);
            OptionalPercentage(material.cu_content_pct);
            OptionalPercentage(material.fe_content_pct);
            OptionalPercentage(material.al_content_pct);
            Nonnegative(process_conditions.sulfuric_acid_l);
            Finite(process_conditions.leaching_temperature_c);
            Nonnegative(process_conditions.leaching_time_hr);
            Percentage(expected_recovery.ni_recovery_pct);
            Percentage(expected_recovery.co_recovery_pct);
        }

        private static void Finite(double value)
        {
            if (double.IsNaN(value) || double.IsInfinity(value))
                throw new ArgumentException("유한한 숫자가 필요합니다.");
        }

        private static void Nonnegative(double value)
        {
            Finite(value);
            if (value < 0) throw new ArgumentException("음수를 사용할 수 없습니다.");
        }

        private static void Percentage(double value)
        {
            Nonnegative(value);
            if (value > 100) throw new ArgumentException("백분율은 0~100%입니다.");
        }

        private static void OptionalPercentage(double? value)
        {
            if (value.HasValue) Percentage(value.Value);
        }
    }

    [Serializable]
    public sealed class MaterialDto
    {
        [JsonProperty(Required = Required.AllowNull)] public string name;
        [JsonProperty(Required = Required.AllowNull)] public double? feed_amount_kg;
        // Percentage points as sent by B: 12.17 means 12.17%. Omitted fields remain null.
        [JsonProperty] public double? ni_content_pct;
        [JsonProperty] public double? co_content_pct;
        [JsonProperty] public double? li_content_pct;
        [JsonProperty] public double? mn_content_pct;
        [JsonProperty] public double? cu_content_pct;
        [JsonProperty] public double? fe_content_pct;
        [JsonProperty] public double? al_content_pct;
    }

    [Serializable]
    public sealed class ProcessConditionsDto
    {
        [JsonProperty(Required = Required.Always)] public double sulfuric_acid_l;
        [JsonProperty(Required = Required.Always)] public double leaching_temperature_c;
        [JsonProperty(Required = Required.Always)] public double leaching_time_hr;
    }

    [Serializable]
    public sealed class RecoveryDto
    {
        [JsonProperty(Required = Required.Always)] public double ni_recovery_pct;
        [JsonProperty(Required = Required.Always)] public double co_recovery_pct;
    }

    // Pure protocol validation, shared by the HTTP client and local protocol tests.
    internal static class FactoryStatusProtocol
    {
        internal static void ValidateAcknowledgement(string json, string sentId, string sentState, float sentProgress)
        {
            JObject response = JObject.Parse(json);
            JToken id = response["command_id"];
            JToken state = response["state"];
            JToken percentage = response["progress_pct"];
            if (id == null || id.Type != JTokenType.String || id.Value<string>() != sentId ||
                state == null || state.Type != JTokenType.String || state.Value<string>() != sentState ||
                percentage == null || (percentage.Type != JTokenType.Integer && percentage.Type != JTokenType.Float))
                throw new ArgumentException("상태 응답의 명령 ID·상태·진행률이 전송한 보고와 일치하지 않습니다.");

            double acknowledged = percentage.Value<double>();
            if (double.IsNaN(acknowledged) || double.IsInfinity(acknowledged) ||
                acknowledged < 0 || acknowledged > 100 || Math.Abs(acknowledged - sentProgress) > 0.001)
                throw new ArgumentException("상태 응답의 진행률이 전송한 보고와 일치하지 않습니다.");
        }
    }
}
