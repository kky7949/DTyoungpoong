# Youngpoong Digital Twin - B 파트 MVP

React + TypeScript HMI와 FastAPI 백엔드가 실제 HTTP로 통신하는 실행 가능한 최소 버전이다. 아직 확정되지 않은 A(AI)와 C(Unity) 연동은 **모의 데이터(Mock Data)** 어댑터로 분리되어 있다.

## 현재 가능한 기능

- 공정 조건 입력 및 결측값 `null` 전송
- 현재 회수율 예측과 추천 공정 조건 표시(모의 데이터)
- 추천 조건을 Unity 명령 큐에 등록
- Mock Unity 또는 실제 Unity가 명령을 조회하고 상태를 보고하는 흐름
- A/C/XAI 지원 상태와 모의 데이터 여부 표시
- React 개발 서버와 FastAPI를 나눠 실행하거나, 빌드 후 `8000`번 한 주소로 실행

## 핵심 개념

- **React**: 브라우저 화면과 버튼·입력 상태를 담당한다.
- **FastAPI**: 화면의 요청을 검증하고 A/C 사이의 데이터를 중계한다.
- **REST/JSON**: 두 프로그램이 HTTP 주소와 구조화된 데이터로 통신하는 방식이다.
- **CORS**: 개발 중 서로 다른 포트(`5173`, `8000`)의 통신을 브라우저가 허용하도록 하는 설정이다.

## 준비물

- Windows PowerShell
- Python 3.11 이상
- Node.js 24 LTS 권장

아래 명령은 저장소 루트의 `Server` 폴더에서 실행한다.

```powershell
cd Server
```

## 최초 설치

### 1. 백엔드

```powershell
py -m venv backend\.venv
backend\.venv\Scripts\python -m pip install -r backend\requirements.txt
```

### 2. 프런트엔드

```powershell
npm --prefix frontend ci
```

## 개발 모드 실행

PowerShell 창 1에서 FastAPI를 실행한다.

```powershell
cd Server\backend
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

PowerShell 창 2에서 React 개발 서버를 실행한다.

```powershell
cd Server
npm --prefix frontend run dev
```

브라우저에서 `http://localhost:5173`에 접속한다. Vite가 `/health`와 `/api` 요청을 FastAPI `8000`번 포트로 전달한다.

## 한 주소로 실행

프런트엔드를 먼저 빌드한 후 FastAPI를 시작한다.

```powershell
cd Server
npm --prefix frontend run build
cd backend
.\.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

PC에서는 `http://localhost:8000`으로 접속한다. 같은 신뢰된 Wi-Fi의 태블릿은 `http://<PC의 IPv4 주소>:8000`으로 접속할 수 있다. Windows 방화벽 창이 나타나면 **개인 네트워크에서만** 허용한다. 학교 또는 공용망에 인증 없이 공개하지 않는다.

## Mock Unity 실행

FastAPI가 실행 중인 상태에서 별도 PowerShell 창을 연다.

```powershell
cd Server
powershell -ExecutionPolicy Bypass -File .\scripts\mock-unity.ps1
```

HMI에서 분석 후 `가상 공장에 적용`을 누르면 스크립트가 명령을 가져가 `running`, `completed` 상태를 보고한다. 이 스크립트는 Unity가 사용할 HTTP 흐름을 대신 시험할 뿐 실제 시뮬레이션은 수행하지 않는다.

## 테스트와 빌드

```powershell
cd Server
backend\.venv\Scripts\python -m pytest backend\tests -v
npm --prefix frontend test -- --run
npm --prefix frontend run lint
npm --prefix frontend run build
```

API 문서는 서버 실행 중 `http://localhost:8000/docs`에서 확인할 수 있다.

## 환경변수

- `FRONTEND_ORIGINS`: 개발용 React 주소를 쉼표로 구분한다. 기본값은 `localhost:5173`, `127.0.0.1:5173`이다.
- `VITE_API_BASE_URL`: 프런트가 다른 PC의 FastAPI를 직접 호출할 때만 설정한다. 기본은 같은 주소이며 개발 중에는 Vite 프록시가 동작한다.

예시는 `backend/.env.example`, `frontend/.env.example`에 있으며 실제 비밀값은 커밋하지 않는다.

## 현재 한계

- A의 실제 모델과 Unity 프로젝트는 아직 연결되지 않았다.
- 공정 필드와 단위는 A/C 담당자와 확정 전인 초안이다.
- 명령과 상태는 메모리에 저장되어 FastAPI 재시작 시 사라진다.
- XAI는 형식이 확정된 뒤 추가할 선택 기능이며 현재 가짜 설명을 만들지 않는다.

자세한 구조는 `docs/architecture.md`, 임시 API는 `docs/api-contract-draft.md`, 팀 확인사항은 `docs/open-questions.md`를 참고한다.
