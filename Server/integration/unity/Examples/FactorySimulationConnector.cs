using System;
using UnityEngine;
using Youngpoong.Integration;

// 선택 연결 템플릿입니다. 실제 설비 실행 함수는 이 파일에 추가해야 합니다.
public sealed class FactorySimulationConnector : MonoBehaviour
{
    [SerializeField] private FastApiFactoryClient client;

    private void OnEnable()
    {
        if (client != null) client.CommandReceived += StartFactory;
    }

    private void OnDisable()
    {
        if (client != null) client.CommandReceived -= StartFactory;
    }

    private void StartFactory(FactoryCommandDto command)
    {
        // 이 실행의 ID를 캡처합니다. 나중에 CurrentCommand에서 다시 읽지 않습니다.
        string commandId = command.command_id;
        ProcessConditionsDto conditions = command.process_conditions;

        Action<float> onProgress = percent =>
            client.ReportProgress(commandId, percent, "침출 공정 실행 중");
        Action onCompleted = () => client.ReportCompleted(commandId);
        Action<string> onError = reason => client.ReportError(commandId, reason);

        Debug.Log("공정 연결 대기: 황산 " + conditions.sulfuric_acid_l +
            " L / 온도 " + conditions.leaching_temperature_c +
            " °C / 시간 " + conditions.leaching_time_hr + " 시간");

        // TODO 1: conditions의 세 값을 기존 설비/시뮬레이션에 반영합니다.
        // TODO 2: 기존 공정을 시작합니다.
        // TODO 3: 기존 진행 이벤트에 onProgress(0~100)를 연결합니다.
        // TODO 4: 실제 완료 이벤트에 onCompleted, 오류 이벤트에 onError를 연결합니다.
        // 기존 공정 함수 이름은 프로젝트마다 다르므로 임의로 호출하지 않습니다.
        // 이 템플릿 그대로는 공장이 움직이지 않으며 자동 완료도 보고하지 않습니다.
    }
}
