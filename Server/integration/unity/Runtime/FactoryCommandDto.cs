using System;
using Newtonsoft.Json;

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
            Percentage(material.ni_content_pct);
            Percentage(material.co_content_pct);
            Percentage(material.li_content_pct);
            Percentage(material.mn_content_pct);
            Percentage(material.cu_content_pct);
            Percentage(material.fe_content_pct);
            Percentage(material.al_content_pct);
            Nonnegative(process_conditions.sulfuric_acid_l);
            Finite(process_conditions.leaching_temperature_c);
            Nonnegative(process_conditions.leaching_time_hr);
            Percentage(expected_recovery.ni_recovery_pct);
            Percentage(expected_recovery.co_recovery_pct);
        }

        private static void Finite(double value)
        {
            if (double.IsNaN(value) || double.IsInfinity(value)) throw new ArgumentException("유한한 숫자가 필요합니다.");
        }
        private static void Nonnegative(double value)
        {
            Finite(value);
            if (value < 0) throw new ArgumentException("음수를 사용할 수 없습니다.");
        }
        private static void Percentage(double? value)
        {
            if (!value.HasValue) return;
            Nonnegative(value.Value);
            if (value.Value > 100) throw new ArgumentException("백분율은 0~100%입니다.");
        }
    }

    [Serializable]
    public sealed class MaterialDto
    {
        [JsonProperty(Required = Required.AllowNull)] public string name;
        [JsonProperty(Required = Required.AllowNull)] public double? feed_amount_kg;
        public double? ni_content_pct;
        public double? co_content_pct;
        public double? li_content_pct;
        public double? mn_content_pct;
        public double? cu_content_pct;
        public double? fe_content_pct;
        public double? al_content_pct;
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
}
