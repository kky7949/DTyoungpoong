using System.Globalization;
using TMPro;
using UnityEngine;

namespace Youngpoong.Integration
{
    // TextMeshPro 사용 시에만 추가하는 선택 예제입니다.
    public sealed class FastApiFactoryDisplay : MonoBehaviour
    {
        [SerializeField] private FastApiFactoryClient client;
        [SerializeField] private TMP_Text materialName;
        [SerializeField] private TMP_Text feedAmount;
        [SerializeField] private TMP_Text sulfuricAcid;
        [SerializeField] private TMP_Text temperature;
        [SerializeField] private TMP_Text leachingTime;
        [SerializeField] private TMP_Text niRecovery;
        [SerializeField] private TMP_Text coRecovery;

        private void OnEnable()
        {
            if (client == null) { Debug.LogError("FastApiFactoryDisplay의 Client를 연결하세요.", this); return; }
            client.CommandReceived += Show;
            if (client.CurrentCommand != null) Show(client.CurrentCommand);
        }
        private void OnDisable()
        {
            if (client != null) client.CommandReceived -= Show;
        }
        private static string Number(double value)
        {
            return value.ToString("0.##", CultureInfo.InvariantCulture);
        }
        private static void Set(TMP_Text field, string value)
        {
            if (field != null) field.text = value;
        }
        private void Show(FactoryCommandDto command)
        {
            Set(materialName, string.IsNullOrWhiteSpace(command.material.name) ? "미입력" : command.material.name);
            Set(feedAmount, command.material.feed_amount_kg.HasValue ? Number(command.material.feed_amount_kg.Value) + " kg" : "미입력");
            Set(sulfuricAcid, Number(command.process_conditions.sulfuric_acid_l) + " L");
            Set(temperature, Number(command.process_conditions.leaching_temperature_c) + " °C");
            Set(leachingTime, Number(command.process_conditions.leaching_time_hr) + " 시간");
            Set(niRecovery, "Ni 예상 회수율 " + Number(command.expected_recovery.ni_recovery_pct) + "%");
            Set(coRecovery, "Co 예상 회수율 " + Number(command.expected_recovery.co_recovery_pct) + "%");
        }
    }
}
