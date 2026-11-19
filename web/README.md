# 금속 회수율 최적화 대시보드

한림대학교 2026학년도 2학기 소프트웨어캡스톤디자인 **영풍그룹 금속 회수율 최적화 디지털 트윈** 프로젝트의 웹·서버 모듈입니다. 폐배터리 습식제련 원료를 입력해 니켈(Ni)과 코발트(Co)의 회수율을 예측하고, 선택한 공정 조건을 Unity 가상 공장에 전달합니다.

```text
A 분석 API ← HTTP → B FastAPI · React 대시보드 ← HTTP → C Unity 가상 공장
```

- **원료 입력과 추천** — 원료 성분·투입량을 입력하고, 니켈 최대·코발트 최대·동시 회수율 목표를 선택합니다.
- **회수율 비교** — AI 추천 조건이나 직접 입력한 조건의 예상 회수율을 비교합니다.
- **가상 공장 적용** — 원료, 최종 공정 조건, 예상 회수율을 Unity 명령으로 보내고 진행률을 확인합니다. 적용 기록은 현재 브라우저에 저장됩니다.

## 실행

Windows PowerShell에서 아래 명령을 사용합니다. 확인한 환경은 Python 3.15와 Node.js 24입니다. 설치와 B 서버 실행 명령은 `web/` 폴더가 보이는 저장소 루트에서 시작합니다.

**실제 통합 시연에는 A 분석 API와 C Unity 가상 공장 연결이 모두 필요합니다.** A는 Ni·Co 예상 회수율과 추천 공정 조건을 계산하고, C는 웹에서 확정한 조건을 받아 공정을 실행한 뒤 진행률과 완료를 보고합니다. B 대시보드만 열거나 모의 모드로 각 기능을 따로 확인할 수도 있습니다.

### 1. 설치 및 화면 빌드

```powershell
python -m venv web\backend\.venv
.\web\backend\.venv\Scripts\python.exe -m pip install -r web\backend\requirements.txt
npm.cmd --prefix web\frontend ci
npm.cmd --prefix web\frontend run build
```

### 2. 모의 시연

```powershell
cd web\backend
$env:A_ADAPTER = 'mock'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

브라우저에서 [대시보드](http://127.0.0.1:8000/)를 엽니다. 아래 명령을 저장소 루트에서 연 별도 PowerShell에서 실행하면 Mock Unity가 명령을 받아 진행·완료를 보고합니다.

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\web\scripts\mock-unity.ps1
```

원료 입력 → **최적 공정 추천** → **추천값 적용하기** → **가상 공장에 적용** 순서로 시연할 수 있습니다. 추천 조건을 수정했다면 **회수율 예측**을 다시 실행합니다. 모의 분석은 고정 예시값을 반환하며, Mock Unity는 HTTP 보고를 대신합니다.

### 3. 실제 A와 Unity 연결

팀 네트워크에서 A 담당자는 분석 API를 실행하고, B 담당자는 웹 서버를 실행하며, C 담당자는 HTTP 연동이 포함된 Unity 씬을 실행합니다. A와 C는 각각 B와 통신합니다. 앞에서 모의 시연을 했다면 B와 Mock Unity를 실행한 창에서 각각 `Ctrl+C`로 종료합니다.

#### 3-1. A 분석 API 준비

1. A 담당자가 분석 API를 실행한 뒤 B 담당자에게 **B PC에서 접속할 수 있는 기본 주소**(`http://<A 서버 주소>:<A 포트>`)를 전달합니다. 분석 API는 팀에서 별도로 운영합니다.
2. **B PC**에서 A 주소 뒤에 `/health`를 붙여 브라우저로 엽니다. JSON의 `model_ready`가 `true`인지 확인합니다. IP나 포트가 바뀌면 새 주소를 받습니다.

#### 3-2. B 웹 서버 한 번 실행

저장소 루트의 PowerShell에서 다음을 실행합니다. `A 서버 주소`에는 담당자로부터 받은 기본 주소를 입력합니다. `/health`와 같은 API 경로는 생략합니다.

```powershell
cd web\backend
$env:A_ADAPTER = 'live'
$env:A_API_BASE_URL = (Read-Host 'A 서버 주소').Trim().TrimEnd('/')
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`--host 0.0.0.0`으로 실행하면 다른 PC에서도 B의 실제 IP 주소로 접속할 수 있습니다. B PC에서는 [대시보드](http://127.0.0.1:8000/)를 열어 **A 연결 · B 연결**을 확인합니다. `8000`이 사용 중이면 `--port 8001`처럼 비어 있는 포트를 쓰고, 브라우저 주소와 Unity의 `Base Url`도 같은 포트로 맞춥니다.

위 명령은 PowerShell 환경 변수로 A를 설정하므로 `.env` 파일이 없어도 실행됩니다. 다른 설정을 확인하려면 [백엔드 설정 예시](backend/.env.example)와 [프런트 설정 예시](frontend/.env.example)를 참고합니다.

#### 3-3. C Unity에 B 주소 설정

1. B 담당자는 별도 PowerShell에서 `ipconfig`를 실행합니다. 팀 네트워크에 연결된 어댑터의 **IPv4 주소**를 확인합니다. Wi-Fi를 쓰면 `무선 LAN 어댑터 Wi-Fi` 항목을 봅니다. Unity 담당자에게 `http://<B PC의 IPv4 주소>:8000`을 전달합니다.
2. **Unity PC**에서 전달받은 주소 뒤에 `/health`를 붙여 브라우저로 엽니다. `{"status":"ok"}`가 나오면 B에 접속할 수 있습니다. Unity와 B가 같은 PC에 있으면 `http://127.0.0.1:8000/health`로 확인할 수 있습니다.
3. 실제 합동 테스트에 사용한 Unity 프로젝트의 연동 씬을 엽니다. Inspector에서 `FastApiFactoryClient`의 `Base Url`에 B 주소를 입력합니다. `/health`는 빼고, 포트는 B의 실행 포트와 맞춥니다. Unity Editor에서 Play를 누른 뒤 대시보드의 **C 연결**을 확인합니다. Mock Unity는 종료한 상태로 둡니다.

저장소의 [`unity/`](../unity/README.md)는 시연 씬 체크포인트입니다. 새로 받은 체크포인트로 연동하려면 팀이 사용한 HTTP 연동 버전을 받거나, [Unity 연동 예제 안내](integration/unity/README.md)를 따라 명령 수신과 상태 보고를 씬에 연결합니다.

#### 3-4. 실제 연동 확인

1. 대시보드 오른쪽 위에 **A 연결 · B 연결 · C 연결**이 모두 표시되는지 확인합니다.
2. 원료 성분 7개와 투입량을 입력한 뒤 **최적 공정 추천**을 눌러 추천 조건과 Ni·Co 예상 회수율을 확인합니다. 허용 범위는 대시보드와 [API 계약](docs/api-contract-draft.md#실제-a-분석-공급자)을 참고합니다.
3. **추천값 적용하기**로 조건을 채웁니다. 공정 조건을 직접 입력하거나 수정했다면 **회수율 예측**을 눌러 현재 조건의 예상 회수율을 확인합니다.
4. **가상 공장에 적용**을 누릅니다. Unity가 웹에서 확정한 조건과 예상 회수율을 받는지 확인하고, 웹의 공장 상태가 **실행 중 → 완료 100%**로 바뀌는지 봅니다.

| 증상 | 확인할 항목 |
| --- | --- |
| A 미연결 | B PC에서 A의 `/health`가 열리고 `model_ready: true`인지 확인합니다. B를 시작한 PowerShell의 `A_ADAPTER`와 `A_API_BASE_URL`을 확인합니다. B의 `/api/v1/system/status`에서 `a_adapter: live`, `a_ready: true`를 확인할 수 있습니다. |
| Unity PC에서 B의 `/health` 접속 실패 | B가 `--host 0.0.0.0`으로 실행 중인지, IPv4와 포트가 맞는지, 두 PC가 서로 접속할 수 있는 팀 네트워크에 있는지 확인합니다. Windows 방화벽이 해당 포트를 차단하는지도 확인합니다. |
| B의 `/health`는 열리지만 C 미연결 | Unity의 `Base Url`, Editor Play 상태, Console 오류를 확인합니다. B의 `/api/v1/factory/state`에서 `connection_status`를 확인할 수 있습니다. |
| C 연결인데 공정이 진행되지 않음 | Mock Unity가 종료됐는지 확인하고, Unity Console에서 명령 수신 여부와 실제 설비의 진행·완료 보고가 연결됐는지 확인합니다. |

## 검증

```powershell
.\web\backend\.venv\Scripts\python.exe -m pytest web\backend\tests -q -p no:cacheprovider
npm.cmd --prefix web\frontend run test -- --run
npm.cmd --prefix web\frontend run lint
npm.cmd --prefix web\frontend run build
```

B 서버 실행 중 [API 문서](http://127.0.0.1:8000/docs)에서 요청 스키마를 확인할 수 있습니다. [시스템 구조](docs/architecture.md)와 [API 계약](docs/api-contract-draft.md)에 구성과 요청·응답 예시를 정리했습니다.

| 대상 | 검증 범위 |
| --- | --- |
| B와 A | 실제 A 서버의 예측·추천을 B에서 호출하고 대표 입력의 결과를 대조했습니다. |
| B와 Unity | B의 명령·상태 API를 테스트했습니다. [Unity C# 코드](integration/unity/README.md)는 연동 **예제**입니다. |
| Unity 데이터 계약 | [`Verification/`](integration/unity/Verification/)은 B의 명령 JSON을 C# 모델이 읽는지 확인하는 **독립 .NET 검증 도구**입니다. 실제 Unity 씬과 시뮬레이션은 C 프로젝트에서 별도로 확인해야 합니다. |

실제 Unity와의 합동 연결은 팀 시연 환경에서 확인했습니다. 위 C# 예제와 .NET 검증 도구는 저장소에서 제공하는 재현 자료입니다.

B의 작업 명령과 상태는 메모리에 저장됩니다. 서버를 재시작하면 초기화됩니다. 대기·실행 중에는 한 번에 한 공정만 허용합니다.
