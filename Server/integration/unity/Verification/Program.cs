using System;
using System.IO;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Youngpoong.Integration;

// Unity 실행 테스트가 아닌, 실제 B JSON과 C# DTO의 직렬화 계약 검사입니다.
public static class Program
{
    private static void Check(bool success, string label)
    {
        if (!success) throw new Exception(label);
        Console.WriteLine("PASS " + label);
    }
    public static void Main(string[] args)
    {
        string json = File.ReadAllText(args[0]);
        FactoryCommandDto command = JsonConvert.DeserializeObject<FactoryCommandDto>(json);
        command.Validate();
        Check(command.command_id == "contract-check" && command.command == "apply_and_start", "command identity");
        Check(command.material.name == null && !command.material.feed_amount_kg.HasValue, "missing material remains null");
        Check(command.material.ni_content_pct == 12.17 && command.material.co_content_pct == 2.41 &&
            command.material.mn_content_pct == 10.49 && command.material.cu_content_pct == 1.9 &&
            command.material.al_content_pct == 3.43, "all supplied material percentages are read");
        Check(command.material.li_content_pct == 0 && !command.material.fe_content_pct.HasValue,
            "material zero and null stay distinct");
        Check(command.process_conditions.sulfuric_acid_l == 900.5 && command.process_conditions.leaching_temperature_c == 60 && command.process_conditions.leaching_time_hr == 4.5, "custom final conditions");
        Check(command.expected_recovery.ni_recovery_pct == 88.8 && command.expected_recovery.co_recovery_pct == 79.5, "final prediction");
        JObject changed = JObject.Parse(json);
        changed["material"]["feed_amount_kg"] = 0;
        command = JsonConvert.DeserializeObject<FactoryCommandDto>(changed.ToString());
        command.Validate();
        Check(command.material.feed_amount_kg.HasValue && command.material.feed_amount_kg.Value == 0, "zero is not null");
        ((JObject)changed["material"]).Remove("ni_content_pct");
        command = JsonConvert.DeserializeObject<FactoryCommandDto>(changed.ToString());
        command.Validate();
        Check(!command.material.ni_content_pct.HasValue, "older commands may omit material percentages");
        changed.Remove("expected_recovery");
        bool rejected = false;
        try { JsonConvert.DeserializeObject<FactoryCommandDto>(changed.ToString()); }
        catch (JsonException) { rejected = true; }
        Check(rejected, "missing prediction rejected");
    }
}
