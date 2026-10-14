# B 파트 최소 통합 MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** React + TypeScript HMI가 FastAPI의 A 모의 분석 API 및 Unity 명령·상태 API와 실제 HTTP로 통신하는 Windows 실행 가능 MVP를 만든다.

**Architecture:** React는 입력과 결과·상태 표시를 담당하고, FastAPI는 검증·작업 조정·A/C 어댑터 경계를 담당한다. A/C 계약이 확정되기 전에는 명확히 표시된 Mock을 사용하며, 개발 시 두 서버를 분리하고 최종 시연 시 FastAPI가 React 빌드 결과도 제공한다.

**Tech Stack:** React, TypeScript, Vite, FastAPI, Pydantic, pytest, HTTPX, Vitest, React Testing Library, PowerShell

**Spec:** `Server/docs/architecture.md`, `Server/docs/api-contract-draft.md`, `Server/docs/open-questions.md`

## Global Constraints

- 모든 제품 코드와 B 문서는 `Server/` 아래에만 둔다.
- 현재 상위 학기 폴더의 Git 저장소에는 커밋하지 않는다. 올바른 `DTyoungpoong` 저장소 경계를 확인한 후에만 커밋한다.
- 실제 A/C 명세가 확정되기 전의 필드와 단위에는 DRAFT 또는 Mock 표시를 유지한다.
- B는 결측값을 대치하지 않고 `null`로 A 어댑터에 전달한다.
- 코드 식별자는 영어를 사용하고 HMI, 스키마 설명, Mock 데이터 사전에는 한글 의미와 단위를 제공한다.
- XAI, 데이터베이스, 인증, Docker, WebSocket은 이 MVP 범위에서 제외한다.
- 실제 비밀값이나 개인 데이터를 소스에 기록하지 않는다.
- 설치가 필요하면 공식 배포 경로와 지원 버전을 확인하고 사용자 승인을 받은 뒤 진행한다.
- 커밋 전 `git diff --cached --name-only`로 `Server/` 밖의 파일이 없는지 확인한다.

## Review Focus

- 빈 문자열과 `null` 숫자 필드를 B가 임의 대치하지 않는지 Task 1에서 검증한다.
- 0 미만 또는 100 초과 함량이 422와 한국어 설명을 반환하는지 Task 1에서 검증한다.
- A 오류가 구조화된 502로 변환되고 프런트가 마지막 성공 결과를 유지하는지 Tasks 1과 3에서 검증한다.
- Unity 명령이 없을 때 204이고 알 수 없는 명령 ID의 상태 보고를 거부하는지 Task 2에서 검증한다.
- API 연결 실패와 `source: mock` 상태를 HMI가 서로 다르게 표시하는지 Task 3에서 검증한다.

---

### Task 0: 안전한 저장소와 실행 환경 확립

**Files:**
- No product files created
- Inspect: `Server/`, local Git root, `https://github.com/kky7949/DTyoungpoong`

**Interfaces:**
- Consumes: 현재 작업 폴더와 사용자가 지정한 GitHub URL
- Produces: `Server/`가 저장소 루트의 하위 폴더인 안전한 작업 위치, 확인된 Python/Node/npm 명령

- [ ] **Step 1: 현재 Git 상태를 기록한다**

Run from `캡스톤디자인`:

```powershell
git rev-parse --show-toplevel
git remote -v
git status --short
```

Expected: 현재 Git 루트가 상위 `2026 2학기`임을 재확인하고 해당 저장소에는 아무것도 스테이징하지 않는다.

- [ ] **Step 2: 원격 저장소를 읽기 전용으로 확인한다**

```powershell
git ls-remote --symref https://github.com/kky7949/DTyoungpoong.git HEAD
```

Expected: 기본 브랜치와 접근 가능 여부가 확인된다. 인증이 필요하면 우회하지 않고 사용자에게 GitHub 인증을 요청한다.

- [ ] **Step 3: 원격 이력을 보존하는 안전한 저장소 경계를 만든다**

원격을 임시 폴더에 clone해 기존 트리와 현재 `Server/`를 비교한다. 충돌이 있으면 덮어쓰지 말고 차이를 보고한다. 충돌이 없을 때만 현재 프로젝트를 독립 저장소로 연결하거나 사용자가 승인한 clone을 작업 위치로 사용한다.

Expected: `git rev-parse --show-toplevel`이 `캡스톤디자인` 또는 승인한 clone을 가리키고, `git remote get-url origin`이 지정 URL을 반환한다.

- [ ] **Step 4: 런타임을 확인한다**

```powershell
python --version
node --version
npm --version
```

Expected: Python 3.14.7을 재확인한다. Node/npm이 계속 없으면 설치하지 말고 공식 Node.js LTS 설치 승인을 요청한다.

- [ ] **Step 5: 진행 안전 조건을 확인한다**

```powershell
git status --short
git diff --cached --name-only
```

Expected: 다른 과목 파일이 표시되거나 스테이징되지 않는다. 충족하지 못하면 Task 1로 진행하지 않는다.

### Task 1: FastAPI 상태 확인 및 A 모의 분석 API

**Files:**
- Create: `Server/.gitignore`
- Create: `Server/backend/requirements.txt`
- Create: `Server/backend/.env.example`
- Create: `Server/backend/app/__init__.py`
- Create: `Server/backend/app/main.py`
- Create: `Server/backend/app/api/health.py`
- Create: `Server/backend/app/api/status.py`
- Create: `Server/backend/app/api/process.py`
- Create: `Server/backend/app/schemas/common.py`
- Create: `Server/backend/app/schemas/process.py`
- Create: `Server/backend/app/integrations/a_base.py`
- Create: `Server/backend/app/integrations/a_mock.py`
- Create: `Server/backend/app/services/process_coordinator.py`
- Create: `Server/backend/app/mock_data/analysis.json`
- Create: `Server/backend/tests/test_health.py`
- Create: `Server/backend/tests/test_system_status.py`
- Create: `Server/backend/tests/test_process_analysis.py`

**Interfaces:**
- Consumes: `AnalyzeRequest`
- Produces: `app.main:app`, `GET /health`, `GET /api/v1/system/status`, `AnalysisProvider.analyze(request: AnalyzeRequest) -> AnalyzeResponse`, `POST /api/v1/process/analyze`

- [ ] **Step 1: 백엔드 환경과 의존성 파일을 준비한다**

`Server/backend/.venv`를 만들고 FastAPI, Uvicorn, Pydantic, pytest, HTTPX의 실제 설치 버전을 `requirements.txt`에 기록한다. `.gitignore`에서 `.venv`, 캐시, `.env`, `node_modules`, `dist`를 제외한다.

- [ ] **Step 2: 실패하는 상태 확인 테스트를 작성하고 실행한다**

`test_health_returns_ok()`는 `/health`의 상태 200과 정확한 JSON `{"status":"ok"}`를 단언한다.

```powershell
Server\backend\.venv\Scripts\python -m pytest Server\backend\tests\test_health.py -v
```

Expected: 앱 또는 라우트가 없어 FAIL.

- [ ] **Step 3: 최소 FastAPI 앱과 상태 라우트를 구현한다**

앱 제목은 `Youngpoong Digital Twin B API`로 한다. `health.py`는 프로세스 상태를, `status.py`는 `backend`, `a_adapter`, `c_adapter`, `capabilities`를 API 초안 형식으로 반환한다. `test_system_status_reports_mock_adapters()`는 A/C가 Mock이고 XAI가 비활성임을 단언한다.

- [ ] **Step 4: 분석 API의 실패 테스트를 작성하고 실행한다**

각 테스트는 정상 요청의 200 및 `source == "mock"`, `ni_content_pct: null` 허용, `ni_content_pct: 101`의 422와 한국어 설명, Provider 예외의 구조화된 502, 응답에 `xai`가 없음을 단언한다. FastAPI의 요청 검증 예외는 `common.py`의 공통 오류 모델과 exception handler를 통해 `error.code`, 한국어 `error.message`, `details`, `request_id` 구조로 변환한다.

```powershell
Server\backend\.venv\Scripts\python -m pytest Server\backend\tests\test_process_analysis.py -v
```

Expected: 스키마·Provider·라우트가 없어 FAIL.

- [ ] **Step 5: 분석 스키마를 구현한다**

`MaterialInput`, `ProcessConditions`, `AnalyzeRequest`, `RecoveryPrediction`, `Recommendation`, `AnalyzeResponse`를 정의한다. 수치 입력은 `float | None`이고, 함량과 회수율은 값이 있을 때 0~100 범위다. `Field(description=...)`에 한글 이름과 단위를 기록한다.

- [ ] **Step 6: A Provider와 Mock을 구현한다**

`AnalysisProvider`는 `analyze(request: AnalyzeRequest) -> AnalyzeResponse` Protocol이다. `MockAnalysisProvider`는 `analysis.json`을 읽고 `source="mock"` 응답을 만들며 입력의 `None`을 B에서 대치하지 않는다. JSON `_meta`에는 `data_type`, `description_ko`, `field_labels_ko`를 둔다.

- [ ] **Step 7: Coordinator와 분석 라우트를 구현한다**

`ProcessCoordinator.analyze(request)`가 Provider를 호출하고 Provider 오류를 `A_ADAPTER_ERROR` 코드의 502로 변환한다.

- [ ] **Step 8: 전체 백엔드 테스트를 통과시킨다**

```powershell
Server\backend\.venv\Scripts\python -m pytest Server\backend\tests -v
```

Expected: health와 analysis 테스트 모두 PASS.

- [ ] **Step 9: Server 파일만 커밋한다**

```powershell
git add -- Server/.gitignore Server/backend
git diff --cached --name-only
git commit -m "feat(server): add mock process analysis API"
```

### Task 2: Unity 명령·상태 Mock API

**Files:**
- Create: `Server/backend/app/schemas/factory.py`
- Create: `Server/backend/app/services/factory_store.py`
- Create: `Server/backend/app/api/factory.py`
- Create: `Server/backend/tests/test_factory_flow.py`
- Create: `Server/scripts/mock-unity.ps1`
- Modify: `Server/backend/app/main.py`

**Interfaces:**
- Consumes: `ApplyFactoryRequest`, `FactoryStatusUpdate`
- Produces: `FactoryStore.queue_command()`, `next_command()`, `update_state()`, `get_state()` 및 factory API 네 개

- [ ] **Step 1: 실패하는 Factory 흐름 테스트를 작성한다**

적용 요청이 queued 명령을 만드는지, 다음 명령이 한 번만 반환되는지, 빈 큐가 204인지, 올바른 명령이 running/completed로 갱신되는지, 모르는 명령 ID가 400인지 각각 단언한다.

- [ ] **Step 2: 테스트 실패를 확인한다**

```powershell
Server\backend\.venv\Scripts\python -m pytest Server\backend\tests\test_factory_flow.py -v
```

Expected: factory 구현이 없어 FAIL.

- [ ] **Step 3: 스키마와 메모리 저장소를 구현한다**

`FactoryStore`는 큐와 최신 상태를 Lock으로 보호한다. 상태는 `disconnected`, `idle`, `queued`, `running`, `completed`, `error`로 제한하고 재시작 시 초기화됨을 명시한다.

- [ ] **Step 4: Factory API 네 개를 구현한다**

`POST /api/v1/factory/apply`, `GET /api/v1/factory/commands/next`, `POST /api/v1/factory/status`, `GET /api/v1/factory/state`를 API 초안과 일치시킨다.

- [ ] **Step 5: Mock Unity 스크립트를 구현한다**

`mock-unity.ps1`은 다음 명령을 폴링하고 명령 수신 시 running과 completed를 차례로 보고한다. URL 매개변수 기본값은 `http://127.0.0.1:8000`이다.

- [ ] **Step 6: 전체 백엔드 테스트와 커밋을 수행한다**

```powershell
Server\backend\.venv\Scripts\python -m pytest Server\backend\tests -v
git add -- Server/backend Server/scripts/mock-unity.ps1
git diff --cached --name-only
git commit -m "feat(server): add mock Unity command flow"
```

Expected: 모든 테스트 PASS, 스테이징 경로는 `Server/`뿐이다.

### Task 3: React HMI 대시보드

**Files:**
- Create: `Server/frontend/` with official Vite React TypeScript scaffold
- Create: `Server/frontend/.env.example`
- Create: `Server/frontend/src/api/types.ts`
- Create: `Server/frontend/src/api/client.ts`
- Create: `Server/frontend/src/components/SystemStatus.tsx`
- Create: `Server/frontend/src/features/dashboard/ProcessForm.tsx`
- Create: `Server/frontend/src/features/dashboard/AnalysisResults.tsx`
- Create: `Server/frontend/src/features/dashboard/FactoryPanel.tsx`
- Create: `Server/frontend/src/features/dashboard/Dashboard.test.tsx`
- Modify: `Server/frontend/src/App.tsx`
- Modify: `Server/frontend/src/main.tsx`
- Modify: `Server/frontend/src/index.css`
- Create: `Server/backend/app/config.py`
- Modify: `Server/backend/app/main.py`

**Interfaces:**
- Consumes: health, system status, process analyze, factory apply/state API
- Produces: `apiClient` 함수와 반응형 한국어 HMI 단일 화면

- [ ] **Step 1: 공식 React TypeScript 프로젝트와 테스트 환경을 만든다**

Node/npm을 재확인하고 Vite React TypeScript 템플릿을 `Server/frontend`에 생성한다. Vitest, jsdom, React Testing Library, user-event를 개발 의존성으로 추가하고 lockfile을 유지한다.

- [ ] **Step 2: 실패하는 대시보드 테스트를 작성한다**

테스트는 B/A/C 상태, 연결 실패, 빈 숫자 입력의 `null` payload, 로딩 중 버튼 비활성화, Mock 배지와 한글 라벨·단위, 422 오류, 실패 후 마지막 성공 결과 유지, 추천 전 적용 버튼 비활성화, factory running/completed 갱신을 단언한다.

- [ ] **Step 3: 테스트 실패를 확인한다**

```powershell
npm --prefix Server/frontend test -- --run
```

Expected: API client와 컴포넌트가 없어 FAIL.

- [ ] **Step 4: API 타입과 client를 구현한다**

백엔드의 nullable 필드명과 정확히 일치시키고 영어 필드에 한글 JSDoc을 넣는다. API 기본 주소는 `VITE_API_BASE_URL`, 미설정 시 same-origin이다. 빈 숫자 입력은 `0`이 아니라 `null`로 직렬화한다.

- [ ] **Step 5: 상태, 입력, 결과, Factory 컴포넌트를 구현한다**

HMI에는 `일부 결측값은 AI 전처리 과정에서 보정됩니다.` 문구, 모의 데이터 배지, 현재 예측, 추천 조건, 예상 회수율, 가상 공장 적용과 상태를 표시한다. 색상뿐 아니라 텍스트로 상태를 구분한다.

- [ ] **Step 6: 반응형 스타일과 오류 보존 동작을 구현한다**

데스크톱은 입력·결과 두 열, 좁은 화면은 한 열이다. 요청 실패 시 입력과 마지막 성공 결과를 지우지 않고 오류 메시지를 함께 표시한다.

- [ ] **Step 7: 개발 CORS 설정을 구현한다**

`FRONTEND_ORIGINS` 환경변수로 허용 origin을 읽는다. `.env.example`에는 localhost와 127.0.0.1 예시만 두고 태블릿용 PC IP는 실행 시 추가한다.

- [ ] **Step 8: 프런트 및 백엔드 검증을 통과시킨다**

```powershell
npm --prefix Server/frontend test -- --run
npm --prefix Server/frontend run build
Server\backend\.venv\Scripts\python -m pytest Server\backend\tests -v
```

Expected: 모든 테스트 PASS, TypeScript 오류 없이 `dist` 생성.

- [ ] **Step 9: Server 파일만 커밋한다**

```powershell
git add -- Server/frontend Server/backend/app/config.py Server/backend/app/main.py Server/backend/.env.example
git diff --cached --name-only
git commit -m "feat(server): add integrated HMI dashboard"
```

### Task 4: 단일 주소 실행과 최종 검증·문서화

**Files:**
- Modify: `Server/backend/app/main.py`
- Create: `Server/backend/tests/test_static_app.py`
- Create: `Server/README.md`
- Create: `Server/docs/progress.md`
- Modify: `Server/docs/api-contract-draft.md`
- Modify: `Server/docs/open-questions.md`

**Interfaces:**
- Consumes: FastAPI 앱과 `Server/frontend/dist`
- Produces: 개발·Mock Unity·빌드·태블릿 시연을 위한 Windows 실행 절차

- [ ] **Step 1: 실패하는 정적 앱 테스트를 작성한다**

프런트 빌드가 있을 때 `/`가 HTML을 반환하고 `/health`와 `/api/v1/*`가 가려지지 않는지 단언한다.

- [ ] **Step 2: 조건부 정적 파일 제공을 구현한다**

`frontend/dist`가 있을 때만 FastAPI가 React를 제공한다. 개발 중 dist가 없어도 API 서버는 정상 시작한다.

- [ ] **Step 3: 전체 자동 검증을 실행한다**

```powershell
Server\backend\.venv\Scripts\python -m pytest Server\backend\tests -v
npm --prefix Server/frontend test -- --run
npm --prefix Server/frontend run build
```

Expected: 백엔드·프런트 테스트 PASS, 프로덕션 빌드 성공.

- [ ] **Step 4: API와 Mock Unity 스모크 테스트를 실행한다**

Uvicorn을 시작하고 PowerShell `Invoke-RestMethod`로 health, analyze, factory apply/state를 호출한다. Mock Unity 스크립트로 명령 수신 및 running/completed 보고를 확인한다.

- [ ] **Step 5: PC 브라우저와 태블릿을 검증한다**

PC에서 전체 흐름을 확인한 뒤 신뢰된 같은 Wi-Fi에서 `http://<시연-PC-IP>:8000`에 접속한다. Windows 방화벽 승인이 필요하면 우회하지 않고 사용자에게 요청한다.

- [ ] **Step 6: README와 진행 문서를 작성한다**

README에 최초 설치, 개발 서버, Mock Unity, 빌드, 단일 주소 실행, 태블릿 접속, 환경변수, 문제 해결을 Windows 명령으로 기록한다. `progress.md`에는 실제 완료·실패·수동 확인 항목만 기록한다.

- [ ] **Step 7: 최종 변경 범위와 비밀값을 검사한다**

```powershell
git status --short
git diff --check
git diff --cached --name-only
rg -n -i "api[_-]?key|secret|password|token" Server --glob '!package-lock.json'
```

Expected: 의도한 `Server/` 파일만 변경, whitespace 오류와 실제 비밀값 없음.

- [ ] **Step 8: 문서와 통합 결과를 커밋한다**

```powershell
git add -- Server
git diff --cached --name-only
git commit -m "docs(server): add MVP setup and verification guide"
```

- [ ] **Step 9: 완료 보고를 작성한다**

변경 파일, 실행한 명령, 테스트·빌드 결과, PC/태블릿 수동 검증, Git 커밋, 남은 A/C 질문과 실패를 구분하여 보고한다. 원격 push는 사용자가 명시적으로 요청한 경우에만 수행한다.
