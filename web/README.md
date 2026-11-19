# 금속 회수율 최적화 대시보드

한림대학교 2026학년도 2학기 소프트웨어캡스톤디자인 **영풍그룹 금속 회수율 최적화 디지털 트윈** 프로젝트의 웹·서버 모듈입니다. 폐배터리 습식제련 원료를 입력해 니켈(Ni)과 코발트(Co)의 회수율을 예측하고, 선택한 공정 조건을 Unity 가상 공장에 전달합니다.

```text
A 분석 API ← HTTP → B FastAPI · React 대시보드 ← HTTP → C Unity 가상 공장
```

- **원료 입력과 추천** — 원료 성분·투입량을 입력하고, 니켈 최대·코발트 최대·동시 회수율 목표를 선택합니다.
- **회수율 비교** — AI 추천 조건이나 직접 입력한 조건의 예상 회수율을 비교합니다.
- **가상 공장 적용** — 원료, 최종 공정 조건, 예상 회수율을 Unity 명령으로 보내고 진행률을 확인합니다. 적용 기록은 현재 브라우저에 저장됩니다.

## 실행

Windows PowerShell에서 아래 명령을 사용합니다. 확인한 환경은 Python 3.15와 Node.js 24입니다. 각 명령 블록은 저장소 루트에서 시작합니다.

### 1. 설치 및 화면 빌드

```powershell
python -m venv web\backend\.venv
.\web\backend\.venv\Scripts\python.exe -m pip install -r web\backend\requirements.txt
npm.cmd --prefix web\frontend ci
npm.cmd --prefix web\frontend run build
```

### 2. 모의 분석으로 시작

```powershell
cd web\backend
$env:A_ADAPTER = 'mock'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

브라우저에서 [대시보드](http://127.0.0.1:8000/)를 엽니다. 아래 명령을 별도 PowerShell에서 실행하면 Unity 없이 명령 등록과 진행·완료 보고 흐름을 확인할 수 있습니다.

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\web\scripts\mock-unity.ps1
```

원료 입력 → **최적 공정 추천** → **추천값 적용하기** → **가상 공장에 적용** 순서로 시연할 수 있습니다. 추천 조건을 수정했다면 **회수율 예측**을 다시 실행합니다. 모의 분석은 고정 예시값을 반환하며, Mock Unity는 HTTP 보고를 대신합니다.

### 3. 실제 A 또는 Unity 연결

실제 A를 사용하려면 아래 명령으로 B를 실행합니다. 예시 주소를 팀의 A 서버 주소로 바꾸고, A의 `GET /health`에서 `model_ready: true`가 반환되는지 확인합니다.

```powershell
cd web\backend
$env:A_ADAPTER = 'live'
$env:A_API_BASE_URL = 'http://<A 서버 주소>:<포트>'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- 실제 A에서는 원료 성분 7개와 투입량이 필수입니다. 필드별 허용 범위는 대시보드에서 확인할 수 있습니다. 추천과 직접 예측의 입력·응답은 [API 계약](docs/api-contract-draft.md#실제-a-분석-공급자)을 참고합니다.
- Unity가 다른 PC에서 실행된다면 B의 `--host`를 `0.0.0.0`으로 바꾸고, 같은 팀 네트워크의 Unity에서 B의 IPv4 주소와 포트를 입력합니다. 실제 Unity가 명령을 받을 때는 Mock Unity를 종료합니다. 연결 방법은 [Unity 연동 예제 안내](integration/unity/README.md)를 참고합니다.
- [백엔드 설정 예시](backend/.env.example)와 [프런트 설정 예시](frontend/.env.example)의 값은 필요한 환경에서 설정합니다. 백엔드는 `.env.example`을 자동으로 읽지 않습니다.

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
