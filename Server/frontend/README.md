# HMI 프런트엔드

React + TypeScript + Vite 기반 B 파트 HMI이다. 설치·실행·테스트 방법은 상위 `Server/README.md`를 따른다.

- API 타입과 통신: `src/api/`
- 상태 표시: `src/components/`
- 공정 입력·분석 결과·Unity 상태: `src/features/dashboard/`
- API 주소: `VITE_API_BASE_URL`(미설정 시 same-origin)
