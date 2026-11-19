# B 파트 시스템 아키텍처

- 문서 상태: 현재 B 구조와 Unity 연동 초안
- 작성일: 2026-10-14
- 현재 구현 반영일: 2026-11-19
- 구현 위치: `web/`

## 1. 목적

B 파트는 React + TypeScript 기반 HMI와 FastAPI 백엔드로 구성한다. B는 A의 데이터 전처리·AI 예측·공정 최적화 결과와 C의 Unity 가상 공장을 연결하는 통합 허브 역할을 한다.

모의 분석과 Mock Unity로 시연할 수 있다. 실제 분석은 B에서 A HTTP API를 호출하고, Unity는 B의 명령·상태 API를 사용한다.

## 2. 범위

### B가 담당하는 것

- 원료와 공정 조건을 입력하는 HMI
- 입력 형식과 명백한 범위 오류 검증
- A에 예측·최적화 작업 요청
- 예측값과 추천 조건 표시
- 선택한 조건을 가상 공장에 적용하는 명령 관리
- Unity 명령 제공과 공정 상태 수집
- A·B·C 연결 상태 표시

### B가 담당하지 않는 것

- A의 전처리, 머신러닝, 최적화 및 XAI 계산
- Unity의 공장 모델, 그래픽, 애니메이션과 내부 시뮬레이션
- 실제 생산설비, PLC 또는 산업용 센서 연결
- 인증, 데이터베이스, Docker 등 MVP에 필요하지 않은 인프라

## 3. 실행 토폴로지

개발 중에는 React 개발 서버와 FastAPI를 같은 Windows PC에서 실행한다.

```text
PC 브라우저 :5173 ──HTTP──> FastAPI :8000
```

최종 시연에서는 같은 Wi-Fi의 태블릿도 HMI에 접속할 수 있게 한다. React 프로덕션 빌드는 FastAPI가 정적 파일로 제공하여 접속 주소를 하나로 단순화한다.

```text
태블릿 브라우저
       │ 같은 신뢰된 Wi-Fi
       ▼
시연 PC의 FastAPI :8000
   ├─ React 정적 파일
   ├─ A Adapter
   └─ C 명령/상태 API ← Unity
```

MVP에는 인증을 추가하지 않는다. LAN 공개 실행은 신뢰된 시연 네트워크로 제한하고, 실제 외부망 배포가 필요해지면 인증과 HTTPS를 별도 설계한다.

## 4. 논리 구조

```text
React HMI
   │ REST API
   ▼
FastAPI
   ├─ API 및 Pydantic 검증
   ├─ Process Coordinator
   │    └─ AnalysisProvider
   │         ├─ 모의 분석
   │         └─ 실제 A HTTP API
   └─ FactoryStore · Unity 명령/상태 API
        └─ Unity 또는 Mock Unity가 B를 조회하고 상태를 보고
```

대시보드는 하나의 B 분석 API로 두 작업을 요청한다. `ProcessCoordinator`는 `AnalysisProvider.analyze()`를 호출하고, 실제 A 공급자가 입력에 따라 추천 또는 예측 API를 선택한다.

## 5. 주요 폴더 구조

```text
web/
├─ AGENTS.md
├─ README.md
├─ .gitignore
├─ frontend/
│  ├─ package.json
│  ├─ vite.config.ts
│  ├─ .env.example
│  └─ src/
│     ├─ main.tsx
│     ├─ App.tsx
│     ├─ api/
│     ├─ components/
│     └─ features/dashboard/
├─ backend/
│  ├─ requirements.txt
│  ├─ .env.example
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ config.py
│  │  ├─ api/
│  │  ├─ schemas/
│  │  ├─ services/
│  │  ├─ integrations/
│  │  └─ mock_data/
│  └─ tests/
└─ docs/
   ├─ architecture.md
   ├─ api-contract-draft.md
   └─ open-questions.md
```

## 6. A 연동 흐름

1. HMI가 원료 및 현재 공정 조건을 FastAPI에 보낸다.
2. B는 자료형과 범위를 검사한다. 실제 A 모드에서는 원료 성분 7개와 원료 투입량이 모두 필요하다.
3. 공정 조건 세 값이 비어 있으면 B는 A의 추천 API를 호출한다. 세 값이 들어 있으면 예측 API를 호출한다.
4. A가 모델 입력을 구성하고 회수율을 계산한다.
5. A가 해당 요청의 예측 또는 추천 결과를 반환한다.
6. B가 결과와 데이터 출처를 HMI에 전달한다.

B는 모의 분석과 실제 HTTP 분석을 같은 공급자 인터페이스로 호출한다. API는 모의 결과를 `source: mock`으로 구분한다. 대시보드의 A 연결 표시는 실제 A 서버의 준비 상태를 반영한다.

XAI는 MVP 범위가 아니다. 형식이 합의된 후 선택적 응답 필드와 별도 HMI 영역으로 추가한다. 현재는 임의 형식이나 가짜 설명을 만들지 않는다.

## 7. C 연동 흐름

B가 공정 시작을 통제하지만, 네트워크 연결은 Unity가 FastAPI에 요청하는 폴링 방식으로 시작한다. Unity 내부에 HTTP 서버를 넣지 않아도 되므로 초기 구현과 오류 처리가 단순하다.

1. 사용자가 추천 조건을 반영하거나, 직접 수정한 조건을 다시 예측한 뒤 공장 적용을 선택한다.
2. FastAPI가 공정 조건과 시작 명령을 메모리에 보관한다.
3. Unity가 FastAPI에 처리할 다음 명령이 있는지 주기적으로 요청한다.
4. FastAPI가 공정 조건과 시작 명령을 반환한다.
5. Unity가 실행 중·완료·오류 상태를 FastAPI에 보고한다.
6. HMI가 FastAPI에서 최신 공정 상태를 주기적으로 조회한다.

MVP에서는 데이터베이스를 추가하지 않는다. FastAPI 재시작 시 명령과 상태가 초기화되는 것은 허용한다. 영속 보관 요구가 생길 때 저장소 도입을 별도로 검토한다.

Unity의 정확한 버전, 공정 필드, 단위, 상태 갱신 주기는 C 구현 과정에서 합의한다. B의 HTTP 계약은 특정 Unity 버전에 의존하지 않게 유지한다.

## 8. HMI 구성

첫 MVP는 반응형 단일 대시보드로 구성한다.

1. A/B/C 연결 상태
2. 원료 및 현재 공정 조건 입력
3. 예측·최적화 실행 버튼과 로딩 상태
4. 현재 예상 회수율
5. 추천 공정 조건과 추천 조건의 예상 회수율
6. 가상 공장 적용 버튼
7. 공정 대기·실행 중·완료·오류 상태

사용자 메시지와 필드 라벨은 한국어로 제공하고, 표준 프로그래밍 식별자는 영어를 사용한다. 입력 오류가 발생해도 사용자가 입력한 값과 마지막 성공 결과를 불필요하게 지우지 않는다.

## 9. Mock 데이터 원칙

- 공식 표현은 `모의 데이터(Mock Data)`로 통일한다.
- 모의 분석 응답에 `source: "mock"`을 포함한다. C 연결은 공장 상태의 `connection_status`로 판단한다.
- HMI의 반복 `모의 데이터` 배지·안내는 사용자 요청으로 제거했다. API와 문서의 출처 구분을 유지하고 회의·시연에서 Mock 범위를 설명한다.
- 영어 필드명에는 Pydantic 설명, TypeScript 주석 또는 데이터 사전으로 한글 이름과 단위를 제공한다.
- JSON은 주석을 지원하지 않으므로 `_meta.description_ko`와 `_meta.field_labels_ko`를 사용한다.
- Mock 값은 실제 AI 성능이나 실제 공정 결과로 표현하지 않는다.

## 10. 오류 처리

- 입력 오류: 해당 필드와 수정 방법을 한국어로 표시한다.
- B 연결 실패: HMI가 서버 연결 실패를 표시하고 재시도를 허용한다.
- A 처리 실패: 예측·최적화 실패로 구분하여 표시한다.
- Unity 미연결: 연결 표시와 마지막 보고 상태를 구분한다. 대기 중인 명령의 접수는 Unity 실행 완료와 구분한다.
- 백엔드는 구조화된 오류 코드와 사용자용 메시지를 반환한다.
- 로그에 비밀번호, API 키 또는 개인 데이터를 기록하지 않는다.

## 11. 연동 검증 범위

- 실제 A 예측·추천 결과를 B 응답과 대조했다.
- B의 Unity 명령·상태 흐름은 API 테스트로 검증했다. 실제 Unity 프로젝트에서의 씬 동작은 별도로 확인한다.

## 12. 검증 기준

- FastAPI 상태 확인, 정상 분석, 잘못된 입력에 대한 자동 테스트
- React TypeScript 검사와 프로덕션 빌드
- PowerShell을 이용한 API 스모크 테스트
- 브라우저에서 입력·로딩·결과·오류 상태 확인
- 신뢰된 같은 Wi-Fi의 태블릿 접속 확인
- API의 분석 출처와 화면의 서버 연결 상태 구분
- Git 스테이징에 `web/` 외 파일이 포함되지 않았는지 확인

## 13. 현재 구현 상태

B는 실제 A HTTP API의 예측·추천 결과를 화면에 표시하고, 선택한 조건을 Unity 명령에 담는다. 실행·검증 방법은 [README](../README.md), 요청·응답은 [API 계약](api-contract-draft.md), C# 연결 방법은 [Unity 예제 안내](../integration/unity/README.md)를 참고한다.


## 14. Unity 표시용 명령 데이터 확장

대시보드는 유효 분석의 원료 이름·투입량·성분 7개와 최종 조건·예상 회수율을 적용 API에 보낸다. FactoryStore는 세 객체를 깊은 복사로 큐에 저장한다. Unity 명령의 원료 성분은 기본 0~100% 검증과 null을 허용한다. 실제 A 분석에서는 모델의 더 좁은 입력 범위와 필수 조건을 별도로 확인한다.
