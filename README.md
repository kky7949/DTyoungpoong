# 영풍그룹 금속 회수율 최적화 디지털 트윈

한림대학교 2026학년도 2학기 소프트웨어캡스톤디자인 프로젝트입니다. 폐배터리 습식 제련 공정의 데이터를 정제하고 Ni·Co 회수율을 예측하여, 공정 조건의 분석 결과를 웹과 Unity 가상 공장에 연결하는 것을 목표로 합니다.

- 팀명: 박치기공룡
- 팀대표: 김병진 (콘텐츠IT)
- 팀원: 남기원 (스마트IOT), 김용준 (콘텐츠IT)
- 지도교수: 허종욱 교수님
- 저장소: [kky7949/DTyoungpoong](https://github.com/kky7949/DTyoungpoong)
- 현황 정리 기준: 전처리는 사전자료, Unity는 2026년 11월 11일 공개 시연 체크포인트, 웹·서버는 2026년 11월 19일 통합본

**[금속 회수율 최적화 대시보드 실행 방법](web/README.md)**

## 현재 진행상황

이 저장소의 `web/`에는 대시보드와 FastAPI 서버가 있습니다. 실제 A 분석은 팀의 별도 HTTP 서비스에 연결합니다. `unity/`에는 사용자 Play 확인을 마친 Unity 시연 체크포인트가 있습니다. 팀 환경에서 실제 Unity와의 합동 연결도 확인했습니다. 회사 제공 모델·재질·프리팹·Alembic은 원본 패키지로 별도 복원해야 합니다.

| 영역 | 프로젝트에서 확인된 진행상황 | 이 저장소의 상태 |
| --- | --- | --- |
| 데이터 전처리 | 원료 성분 211개·공정 조건 80개 결측 대치, CLEAN 420행×24열 생성, 파생변수 8개 계산·검증 | 상위 폴더와 처리 기준 안내. 실제 수행 코드는 미통합 |
| 회수율 예측 Model1 | Random Forest 파생변수·A/B/C/D 비교, 모델 B 후보 선정, 과적합 진단. 개선·최종 확정 미완료 | 상위 폴더와 실험 안내, 기존 회귀 평가 함수 1개 유지 |
| 공정 조건 최적화 | B에서 팀 A 분석 서비스의 공정 조건 추천 결과를 확인 | `web/`에 A API 연결 코드 포함. A 모델·최적화 소스는 별도 관리 |
| 디지털 트윈 웹·서버 | 원료 입력, 실제 A 예측·추천, 공정 조건 적용, 진행률 표시 | [`web/`](web/README.md)에 React·FastAPI 소스, 테스트, 실행 안내 통합 |
| Unity/3D 가상 공장 | 공장 시연 씬 Play 확인 및 팀 환경의 웹 연동 합동 확인 | `unity/`에 시연 체크포인트, `web/integration/unity/`에 연결 예제와 JSON 검증 도구 포함 |

[웹 실행 안내](web/README.md)에서 모의 시연과 실제 A·Unity 연결 절차를 확인할 수 있습니다. 초기 실험과 Unity 시연 체크포인트는 [진행상황 보고서](docs/REPORT.md)를 참고합니다.

## 폴더 구성

```text
DTyoungpoong/
├── data/
│   ├── README.md                 # 원본·정제 데이터 보관 기준
│   ├── raw/.gitkeep              # 원본 데이터 위치, 실제 데이터 Git 제외
│   └── processed/.gitkeep        # 정제 데이터 위치, 실제 데이터 Git 제외
├── module1_preprocessing/
│   └── README.md                 # 확인된 전처리 방식과 실제 코드 통합 안내
├── module2_prediction/
│   ├── README.md                 # Model1 실험·평가와 미완료 사항
│   └── evaluate.py               # 기존 RMSE·MAE·R² 계산 함수
├── module3_optimization/
│   └── README.md                 # 미진행 영역, 향후 구현 범위
├── web/
│   ├── backend/                  # FastAPI 서버 및 API 테스트
│   ├── frontend/                 # React · TypeScript 대시보드
│   ├── integration/unity/         # Unity 연결 예제 및 JSON 검증
│   └── README.md                  # 대시보드 실행 방법
├── unity/
│   ├── Assets/                   # C# 2개·씬 3개·HDRP·TMP·InputSystem 및 .meta
│   ├── Packages/                 # 버전을 고정한 패키지와 의존성 잠금 파일
│   ├── ProjectSettings/          # HDRP와 시연 씬 설정
│   ├── EXTERNAL_ASSETS.json      # 외부 패키지 해시와 경로·GUID 목록
│   ├── tools/                    # 씬 내장 메시 공개 방지 검사
│   ├── .gitignore                # 제공 원본·Alembic·캐시·녹화 제외
│   └── README.md                 # 외부 에셋 복원과 Play 검증 절차
├── notebooks/
│   └── README.md                 # 실제 실험 노트북을 추가할 때의 기준
├── docs/
│   └── REPORT.md                 # 실험 수치·진행상황·사전질문·구조 정리 내역
├── .gitignore
├── requirements.txt             # 현재 남아 있는 평가 함수의 의존성만 포함
└── README.md
```

진행되지 않은 세부 기능의 빈 스크립트·클래스·노트북은 미리 만들지 않습니다. 실제 코드와 산출물을 정리해 가져올 때 필요한 하위 구조를 추가합니다.

## 현재 사용할 수 있는 코드

대시보드는 [웹·서버 실행 안내](web/README.md)를 따릅니다. Python 평가 함수는 `module2_prediction/evaluate.py`에서 사용할 수 있습니다. Unity 시연은 [외부 에셋 복원 및 실행 안내](unity/README.md)를 따라 Unity Hub에서 `unity/` 폴더를 엽니다.

평가 함수가 필요한 경우에만 저장소 루트에서 다음과 같이 환경을 준비합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

```python
from module2_prediction.evaluate import evaluate_regression

# 실제 정답과 예측값을 같은 행 순서로 전달합니다.
metrics = evaluate_regression(y_true, y_pred, prefix="Test")
```

루트의 `requirements.txt`는 평가 함수용입니다. 웹·서버 의존성은 `web/backend/requirements.txt`와 `web/frontend/package-lock.json`에서 관리합니다.

## 다음 작업

1. 기존 전처리 코드와 실험 노트북, 산출물을 정리해 Module 1·2에 통합합니다. 대치 통계는 Train에서만 계산한 원래 절차를 유지합니다.
2. RAW 데이터사전 기준 이상치 처리 검증, 분석일자 21개 결측 처리 방침, 정규화·표준화 필요 여부를 검토합니다.
3. Model1 과적합 개선과 최종 입력·모델 선정을 진행합니다. 후보 비교와 재학습 후 Test 결과는 구분합니다.
4. 실제 A·Unity를 연결한 시연을 발표 환경에서 다시 확인합니다. 명령 수신 확인·재전송과 시연 권한 범위는 후속 검토 항목입니다.
5. Unity에 표시하는 값은 모델이 예측한 결과입니다. 씬의 설비 효과와 예측 회수율의 의미는 시연에서 구분해 설명합니다.

이 목록은 후속 작업이며 완료 목록이 아닙니다. 이번 정리에서 삭제한 초기 예제 코드는 기존 Git 이력에 남아 있습니다.
