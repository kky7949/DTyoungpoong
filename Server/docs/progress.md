# B 파트 구현 진행 현황

- 최종 갱신: 2026-10-14
- 브랜치: `codex/b-mvp`
- 상태: 모의 A/C를 이용한 Native MVP 구현 및 자동 검증 완료

## 완료

- FastAPI 상태 확인 및 시스템 상태 API
- nullable 입력 검증과 예측·최적화 통합 API
- 한글 설명이 포함된 A 파트 모의 데이터 및 교체 가능한 어댑터
- Unity 명령 등록·조회·상태 보고·최신 상태 API
- Mock Unity PowerShell 클라이언트
- React + TypeScript 반응형 HMI
- 로딩·연결 실패·검증 오류·마지막 성공 결과 보존 처리
- A/C 모의 데이터 및 XAI 미지원 상태의 텍스트 표시
- Vite 개발 프록시와 FastAPI CORS 설정
- React 빌드를 FastAPI가 조건부로 제공하는 단일 주소 실행

## 자동 검증

- 백엔드: health, 상태, 분석, 오류, Unity 흐름, CORS, 정적 앱 총 11개 테스트 통과
- 프런트엔드: 연결 상태, 실패 상태, 결측값, 결과, 오류 보존, Unity 적용 흐름 총 5개 테스트 통과
- TypeScript 프로덕션 빌드와 Oxlint 통과
- 실제 Uvicorn HTTP 스모크 테스트: `/` 200, 분석 `source=mock`, 명령 `queued`, Mock Unity 완료 `100%`

검증 결과와 정확한 실행 명령은 각 구현 커밋 및 최종 작업 보고에 기록한다.

## 아직 수동 확인이 필요한 항목

- PC 브라우저에서의 최종 시각 확인(자동화 환경에 사용 가능한 브라우저가 없어 미실행)
- 같은 Wi-Fi 태블릿에서 `http://<PC-IP>:8000` 접속
- Windows 방화벽 허용 여부
- 실제 A 서비스 또는 Python 모델 연결
- 실제 Unity 빌드 연결

## 후속 작업

1. `open-questions.md`의 필드·단위·주기·Unity 버전을 A/C 담당자와 확정한다.
2. Mock 어댑터와 동일한 인터페이스로 실제 A 어댑터를 추가한다.
3. Unity에서 명령 조회와 상태 보고 HTTP 클라이언트를 구현한다.
4. XAI 출력 명세가 확정되면 선택 필드와 화면 영역을 추가한다.
