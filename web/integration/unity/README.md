# Unity HTTP 연동 예제 및 데이터 계약 검증

이 폴더의 `Runtime/`과 `Examples/`는 **Unity HTTP 연동 예제**다. `Verification/`은 B 명령 JSON의 C# 역직렬화를 확인하는 **독립 .NET 검증 도구**다. Unity Editor 컴파일, Play, 실제 씬 동작은 C 프로젝트에서 별도로 확인한다.

## 1. 전달할 파일

`Runtime/`의 파일을 Unity 프로젝트의 `Assets/Scripts/BIntegration/` 등으로 복사한다.

- `FactoryCommandDto.cs`: 받은 JSON의 데이터 구조와 범위를 검증한다. 원료 이름·투입량·성분 7개의 null을 보존한다.
- `FastApiFactoryClient.cs`: 명령 조회, 실행 상태·완료·오류 보고, 현재 Play 세션의 중복 실행 방지.
- `FastApiFactoryDisplay.cs`: 선택 사항. TextMeshPro UI 7개에 값을 표시한다. TMP를 사용하지 않는 프로젝트에서는 복사하지 않고 기존 UI에 CommandReceived를 연결한다.

`Verification/`은 B 담당자의 .NET 데이터 계약 검사 도구다. **Unity Assets에 복사하지 않는다.**

## 2. JSON 패키지 준비

Unity Package Manager의 패키지 이름으로 설치 기능에서 `com.unity.nuget.newtonsoft-json`을 추가한다. 이미 설치돼 있으면 추가하지 않는다. 사용 중인 Unity와 호환되는 버전을 선택하며 이 예제는 특정 Unity 버전과 계약을 묶지 않는다.

투입량과 원료 성분 필드는 `double?`로 읽어 null과 0을 구분한다. 이전 서버에서 성분 필드가 생략되어도 읽을 수 있다. Unity 화면에 성분을 표시하려면 `command.material`의 필드를 해당 UI에 연결한다. 전체 명령 JSON은 [B API 계약](../../docs/api-contract-draft.md)을 참고한다.

공식 참고:
- [Unity의 Newtonsoft Json 패키지](https://docs.unity3d.com/Packages/com.unity.nuget.newtonsoft-json@3.2/manual/index.html)
- [패키지 이름으로 설치](https://docs.unity3d.com/6000.0/Documentation/Manual/upm-ui-quick.html)
- [UnityWebRequest](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Networking.UnityWebRequest.html)

## 3. 씬 설정과 서버 주소

1. 빈 GameObject `BConnection`을 만든다.
2. `FastApiFactoryClient`를 붙인다. 실행 중인 씬 전체에 하나만 둔다.
3. Inspector의 `Base Url`에 서버 주소를 입력한다.
   - B와 같은 PC: `http://127.0.0.1:8000` (기본 실행 예시)
   - 다른 PC: `http://<B PC의 IPv4 주소>:<B 포트>`
4. 조회/보고 간격은 기본 1초, 요청 제한 시간은 기본 5초다. B의 연결 끊김 기준은 현재 10초이므로 실행 중에도 통신이 이어져야 한다.
5. B 담당자는 다른 PC 연결 시 FastAPI를 `--host 0.0.0.0`으로 실행하고 **Mock Unity 스크립트를 종료**한다.
6. Unity PC 브라우저에서 B의 서버 주소에 `/health`를 붙여 응답을 확인한다.

첫 시험은 Editor에서 진행한다. 모바일·WebGL·IL2CPP 빌드는 HTTP 허용 정책·CORS·코드 스트리핑 등의 차이가 있어 이 예제에서 검증하지 않았다.

## 4. 화면 표시

TextMeshPro 사용 시 `FastApiFactoryDisplay`를 붙이고 다음 Inspector 필드를 연결한다.

| 필드 | 연결할 UI |
|---|---|
| Client | 씬의 FastApiFactoryClient 컴포넌트 |
| Material Name | 원료 이름 TMP 텍스트 |
| Feed Amount | 원료 투입량 TMP 텍스트 |
| Sulfuric Acid | 황산량 TMP 텍스트 |
| Temperature | 침출 온도 TMP 텍스트 |
| Leaching Time | 침출 시간 TMP 텍스트 |
| Ni Recovery | Ni 예상 회수율 TMP 텍스트 |
| Co Recovery | Co 예상 회수율 TMP 텍스트 |

해당 텍스트가 없으면 항목별 TMP 텍스트를 만들고 연결한다. 원료 이름·투입량 null은 미입력, 투입량 0은 0 kg으로 표시한다. 회수율은 **예상 회수율**로 표시하며 실측 결과로 바꾸지 않는다.

## 5. 실제 공장 동작 연결

기존 설비 제어 스크립트에서 다음처럼 이벤트에 연결한다. 아래 코드는 연결 위치 설명이며 실제 설비 API 이름은 C 프로젝트에 맞춘다.

```csharp
using Youngpoong.Integration;

// client는 Inspector 등에서 연결한 FastApiFactoryClient입니다.
// OnEnable:
client.CommandReceived += StartFactory;
// OnDisable:
client.CommandReceived -= StartFactory;

void StartFactory(FactoryCommandDto command)
{
    // command.command_id를 이 실행 작업에 보관합니다.
    // command.process_conditions.sulfuric_acid_l       : L
    // command.process_conditions.leaching_temperature_c : °C
    // command.process_conditions.leaching_time_hr       : 시간(hour)
    // 위 조건으로 실제 씬/시뮬레이션을 시작합니다.
    // 여기서 완료를 바로 보고하지 않습니다.
}

// 실제 공정 진행 콜백: 이 작업에 보관한 commandId 사용
client.ReportProgress(commandId, 35f, "침출 공정 실행 중");
// 실제 완료 콜백
client.ReportCompleted(commandId);
// 실제 오류 콜백
client.ReportError(commandId, "설비 오류 내용");
```

- 호출은 Unity 메인 스레드에서 한다. HTTP·시뮬레이션을 `Thread.Sleep`이나 긴 동기 루프로 막지 않는다.
- 진행률은 0~100이며 이전 값보다 줄어들 수 없다. 완료는 100%로 보고한다.
- 비동기 작업 콜백에는 해당 작업의 commandId를 따로 보관한다. 이후 새 작업의 ID를 읽어 사용하면 안 된다.
- 전달받은 DTO의 command_id와 조건값은 수정하지 않는다. 실제 시뮬레이션 시간과 표시된 침출 시간(hour)의 배속은 C에서 구분한다.
- 이 예제는 명령 수신 시 `running 0% / Unity 동작 연결 대기`를 보고한다. 실제 동작을 연결하지 않으면 0%로 남는다. 자동 완료·가짜 진행률은 생성하지 않는다.

## 6. 첫 연결 시험

1. Mock Unity가 종료돼 있는지 확인한다.
2. Editor Play → 웹에서 `C 연결`을 확인한다. 명령이 없을 때 HTTP 204는 정상이다.
3. 웹에서 원료 입력 → 추천값 적용하기 또는 직접 입력·예측 → 가상 공장에 적용.
4. Unity Console의 B 명령 수신 JSON과 UI 값이 웹 조건과 일치하는지 확인한다.
5. 통신만 시험할 때는 **Play 중 FastApiFactoryClient 컴포넌트의 메뉴**에서 `통신 시험/현재 명령 수동 완료`를 선택한다. 웹이 완료 100%로 바뀌는지 본다. 실제 공정 완료를 검증한 것은 아니다.
6. 실제 공장 동작 연결 후에는 ReportProgress/ReportCompleted/ReportError가 실제 콜백에서 호출되는지 시험한다.

## 7. 오류·재시작 시 주의

- 요청이 실패하면 HTTP 상태·메시지·본문을 Console에 남긴다. 통신 장애는 다음 주기에 재시도한다.
- 상태 보고의 400/409/422는 명령 ID·상태 순서·형식 오류로 간주해 통신을 중단한다. 시뮬레이션을 자동 재실행하지 않는다. B 담당자와 현재 명령을 확인한다.
- 상태 POST는 한 번에 하나만 보내므로 이전 running 응답과 완료 보고가 순서 없이 겹치지 않는다. 실행 중에는 상태 POST가 연결 유지 역할을 한다. 완료/오류가 접수되면 다음 명령 조회로 돌아간다.
- B는 명령을 조회하면 큐에서 제거하며 수신 확인·자동 재전송·취소 API는 없다. GET 응답 유실이나 실행 중 Play 종료·씬 교체·B 재시작 이후 자동 복구를 보장하지 않는다. 시험 전에 종료 보고를 보내고, 막혔다면 B 담당자와 서버 초기화를 맞춘다.
- 중복 실행 방지는 현재 Unity Play 세션의 메모리에만 있다. 재시작 이후 영구적인 exactly-once 처리를 제공하지 않는다.
- C 연결 표시는 공장 상태 API의 `connection_status`를 사용한다. B의 공장 상태·접수 응답의 고정값 `source: mock`은 연결 여부와 별개다. 실제 씬 실행은 Unity 로그와 상태 보고로 확인한다.

## 8. 검증 범위

.NET SDK 10 환경에서 저장소 루트의 PowerShell로 명령 JSON 검증을 실행한다.

```powershell
dotnet run --project web\integration\unity\Verification\DtoContractCheck.csproj -- web\integration\unity\Verification\server-command.json
```

검증 도구는 명령 ID, 원료 성분과 결측값, 최종 공정 조건, 예상 회수율을 확인한다. 실제 씬과 UI 동작은 Unity Editor에서 확인한다. [FactorySimulationConnector.cs](Examples/FactorySimulationConnector.cs)는 실제 시뮬레이션을 연결할 위치를 보여 주는 예제다.
