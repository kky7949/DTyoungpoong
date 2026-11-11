# 영풍그룹 금속 회수율 최적화 디지털 트윈

한림대학교 2026학년도 2학기 소프트웨어캡스톤디자인 프로젝트입니다. 폐배터리 습식 제련 공정의 데이터를 정제하고 Ni·Co 회수율을 예측하여, 공정 조건의 분석 결과를 웹과 Unity 가상 공장에 연결하는 것을 목표로 합니다.

- 팀명: 박치기공룡
- 팀대표: 김병진 (콘텐츠IT)
- 팀원: 남기원 (스마트IOT), 김용준 (콘텐츠IT)
- 지도교수: 허종욱 교수님
- 저장소: [kky7949/DTyoungpoong](https://github.com/kky7949/DTyoungpoong)
- 현황 정리 기준: 전처리·웹은 2026년 11월 4일 사전자료, Unity는 2026년 11월 11일 사용자 Play 확인 및 저장소 통합

## 현재 진행상황

**프로젝트에서 수행한 작업과 이 저장소에 포함된 코드는 다릅니다.** 전처리·학습 실험 코드·데이터와 웹·서버 소스는 아직 통합하지 않았습니다. Unity는 사용자 Play 확인을 마친 공정 시연의 C# 두 파일, 세 씬, 패키지·설정을 `unity/`에 통합했습니다. 회사 제공 모델·재질·프리팹·Alembic은 Git에 포함하지 않으며 원본 패키지로 별도 복원해야 합니다.

| 영역 | 프로젝트에서 확인된 진행상황 | 이 저장소의 상태 |
| --- | --- | --- |
| 데이터 전처리 | 원료 성분 211개·공정 조건 80개 결측 대치, CLEAN 420행×24열 생성, 파생변수 8개 계산·검증 | 상위 폴더와 처리 기준 안내. 실제 수행 코드는 미통합 |
| 회수율 예측 Model1 | Random Forest 파생변수·A/B/C/D 비교, 모델 B 후보 선정, 과적합 진단. 개선·최종 확정 미완료 | 상위 폴더와 실험 안내, 기존 회귀 평가 함수 1개 유지 |
| 공정 조건 최적화 | 구현 완료를 확인할 근거 없음. 방법·허용범위 확정 필요 | 상위 폴더와 안내만 유지 |
| 디지털 트윈 웹·서버 | React/TypeScript·FastAPI로 입력→분석→조건 수정→적용 요청 흐름 구현. 모의 데이터와 Unity 대역 스크립트로 확인 | `web/` 안내만 추가. 실제 프런트엔드·서버 소스 미통합 |
| Unity/3D 가상 공장 | 공장·수조·맵 HDRP 배치, Start/Reset, 주입→수면 안정화→부속물 투입→교반 가속·색 변화·조각 소실→배출을 사용자 Play 확인. 실제 웹/API/AI 연결 없음 | `unity/`에 재현용 코드·씬·설정 통합. 제공 에셋은 외부 패키지 4개 임포트 필요 |

웹에서 추천 조건과 실행 상태가 표시된다는 사실은 실제 AI 추론·최적화 또는 Unity 실행이 연결되었다는 뜻이 아닙니다. 자세한 수치, 검증 한계와 사전질문은 [진행상황 보고서](docs/REPORT.md)에 정리했습니다.

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
│   └── README.md                 # 웹·서버의 모의 검증 범위와 연동 과제
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

Python에는 `module2_prediction/evaluate.py`의 `evaluate_regression(y_true, y_pred, prefix="Test")`가 있습니다. 전처리 실행기, 학습 실행기, 최적화 실행기는 제공하지 않습니다. Unity 시연은 [외부 에셋 복원 및 실행 안내](unity/README.md)를 따라 Unity Hub에서 `unity/` 폴더를 엽니다.

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

`requirements.txt`는 전체 프로젝트의 실행 환경을 정의하지 않습니다. 실제 전처리·웹·서버 코드가 통합되면 해당 코드에서 사용하는 의존성과 실행 절차를 함께 추가합니다.

## 다음 작업

1. 기존 전처리 코드와 실험 노트북, 산출물을 정리해 Module 1·2에 통합합니다. 대치 통계는 Train에서만 계산한 원래 절차를 유지합니다.
2. RAW 데이터사전 기준 이상치 처리 검증, 분석일자 21개 결측 처리 방침, 정규화·표준화 필요 여부를 검토합니다.
3. Model1 과적합 개선과 최종 입력·모델 선정을 진행합니다. 후보 비교와 재학습 후 Test 결과는 구분합니다.
4. 웹·서버의 실제 소스를 통합하고 AI·Unity와 연결합니다. 서버 조건 검증, 명령 수신 확인·중복 방지, 시연 인증 범위는 멘토링 후 결정합니다.
5. Unity는 현재 고정된 시연 파라미터로 동작합니다. 다음 단계에서 웹/API 명령·상태와 연결하고, AI 결과를 표현하는 범위를 정합니다. 현재 시연 효과는 검증된 물리·화학 공정 시뮬레이션이나 AI 계산 결과가 아닙니다.

이 목록은 후속 작업이며 완료 목록이 아닙니다. 이번 정리에서 삭제한 초기 예제 코드는 기존 Git 이력에 남아 있습니다.
