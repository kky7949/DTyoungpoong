using System.Globalization;

namespace Youngpoong.Integration
{
    public static class FactoryPanelText
    {
        public static string Conditions(FactoryCommandDto command)
        {
            if (command == null)
                return "<size=32><b>공정 조건</b></size>\n\n황산 투입량: -- L\n침출 온도: -- °C\n침출 시간: -- h";

            return "<size=32><b>공정 조건</b></size>\n\n황산 투입량: " + Number(command.process_conditions.sulfuric_acid_l) + " L" +
                "\n침출 온도: " + Number(command.process_conditions.leaching_temperature_c) + " °C" +
                "\n침출 시간: " + Number(command.process_conditions.leaching_time_hr) + " h";
        }

        public static string Material(FactoryCommandDto command)
        {
            if (command == null)
                return "<size=28><b>원료 조건</b></size>\n\n원료명: 미수신\n원료 투입량: -- kg\n" +
                    "니켈(Ni): --\n코발트(Co): --\n리튬(Li): --\n망간(Mn): --\n구리(Cu): --\n철(Fe): --\n알루미늄(Al): --";

            MaterialDto material = command.material;
            return "<size=28><b>원료 조건</b></size>\n\n원료명: " + Plain(material.name) +
                "\n원료 투입량: " + (material.feed_amount_kg.HasValue ? Number(material.feed_amount_kg.Value) + " kg" : "미입력") +
                "\n니켈(Ni): " + Content(material.ni_content_pct) +
                "\n코발트(Co): " + Content(material.co_content_pct) +
                "\n리튬(Li): " + Content(material.li_content_pct) +
                "\n망간(Mn): " + Content(material.mn_content_pct) +
                "\n구리(Cu): " + Content(material.cu_content_pct) +
                "\n철(Fe): " + Content(material.fe_content_pct) +
                "\n알루미늄(Al): " + Content(material.al_content_pct);
        }

        public static string Results(FactoryCommandDto command, string connection, float progress, bool apiRun)
        {
            string prediction = command == null ? "Ni: -- %\nCo: -- %" :
                "Ni: " + Number(command.expected_recovery.ni_recovery_pct) + " %\nCo: " +
                Number(command.expected_recovery.co_recovery_pct) + " %";
            string identifier = command == null ? "미수신" : Plain(command.command_id);
            if (identifier.Length > 18) identifier = identifier.Substring(0, 18) + "…";
            return "<size=32><b>예상 회수율</b></size>\n\n" + prediction +
                "\n\n<size=20>웹 최종 적용 조건의 예측값\nUnity 실측 결과가 아닙니다.</size>" +
                "\n\n<b>연동 상태</b>\n<size=20>" + Plain(connection, 140) +
                "\n명령: " + identifier + "\n" + (apiRun ? "웹 공정" : "시연") +
                " 진행: " + progress.ToString("0", CultureInfo.InvariantCulture) + " %</size>";
        }

        public static string CompletedResults(FactoryCommandDto command, string connection)
        {
            string values = command == null
                ? "<size=26>웹 예측값 미수신</size>"
                : "<size=25>니켈(Ni)</size>\n<size=56><b>" + Number(command.expected_recovery.ni_recovery_pct) + "%</b></size>\n\n" +
                  "<size=25>코발트(Co)</size>\n<size=56><b>" + Number(command.expected_recovery.co_recovery_pct) + "%</b></size>\n\n" +
                  "<size=20>웹에서 받은 예측값</size>";
            return "<size=25><b>공정 시연 완료</b></size>\n<size=37><b>예상 회수율</b></size>\n\n" + values +
                "\n\n<size=20>" + Plain(connection, 140) + "</size>";
        }

        private static string Number(double value) { return value.ToString("0.####", CultureInfo.InvariantCulture); }
        private static string Content(double? value) { return value.HasValue ? Number(value.Value) + "%" : "미입력"; }

        // Treat server text as text rather than TMP rich-text markup. Keep the exhibition panel bounded.
        private static string Plain(string value, int limit = 44)
        {
            if (string.IsNullOrWhiteSpace(value)) return "미입력";
            value = value.Replace('<', '＜').Replace('>', '＞').Replace('\n', ' ').Replace('\r', ' ').Replace('\t', ' ');
            return value.Length > limit ? value.Substring(0, limit) + "…" : value;
        }
    }
}
