# 영풍그룹 금속 회수율 최적화 디지털 트윈

한림대학교 2026학년도 2학기 소프트웨어캡스톤디자인 프로젝트입니다. 폐배터리 습식 제련 공정의 원료 데이터를 정제하고 Ni·Co 회수율을 예측합니다. 웹 대시보드에서 선택한 공정 조건을 Unity 가상 공장에 전달해 공정 단계를 시연합니다.

- **팀명** 박치기공룡
- **팀대표** 김병진 (콘텐츠IT)
- **팀원** 남기원 (스마트IOT), 김용준 (콘텐츠IT)
- **지도교수** 허종욱 교수님
- **저장소** [kky7949/DTyoungpoong](https://github.com/kky7949/DTyoungpoong)

[모델 실행](#모델-실행) · [노트북 실행](notebooks/README.md) · [웹 대시보드 실행](web/README.md) · [Unity 실행](unity/README.md)

## 최종 모델과 제출 자료

고정 모델 `YP-curve17-dev357-v2`는 원료 조성·투입량과 공정조건 11개에 제곱항과 교호항 6개를 더한 17개 특성으로 Ni·Co 회수율을 각각 예측합니다. 수업 제공 원본의 424행에서 중복을 제거한 420개 배치 중 357개를 모델 개발에 사용했습니다. 보류한 63개 배치는 이번 학습·튜닝·평가에서 제외했습니다.

| 경로 | 내용 |
|---|---|
| [`data/`](data/README.md) | 배포용 XLSX·CSV, 데이터사전, 정제·대치·표준화 데이터와 입력 예제 |
| [`module1_preprocessing/`](module1_preprocessing/README.md) | 원본 검증, 중복·결측 처리, 특성 생성과 전처리 테스트 |
| [`module2_prediction/`](module2_prediction/README.md) | 고정 모델 상태, 회수율 예측, 비교 평가, 재학습과 변수 중요도 |
| [`module3_optimization/`](module3_optimization/README.md) | 황산 투입량·침출 온도·침출 시간 탐색과 목적별 추천 |
| [`notebooks/`](notebooks/README.md) | 전처리·예측·조건 탐색 분석과 단일 셀 데모 |

## 모델 실행

저장소 루트에서 Python 3.12 가상환경을 만들고 모델 의존성을 설치합니다.

```powershell
# Windows PowerShell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r module2_prediction/requirements.txt
```

```bash
# macOS / Linux
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r module2_prediction/requirements.txt
```

아래 명령은 예제 입력으로 현재 조건의 회수율을 예측하고, 고정 모델로 공정 조건을 탐색합니다. 추천 결과는 가상환경 폴더에 JSON·CSV·그래프로 저장됩니다.

```bash
python -m module2_prediction.inference --input data/examples/example_input.json
python -m module3_optimization.recommend --input data/examples/example_input.json --output .venv/recommendations.json
```

기본 공동 목표는 Ni 95% 이상과 Co 90% 이상입니다. 두 목표를 충족하고 지원 범위 검사를 통과한 후보에서 `(100-Ni)^2 + (100-Co)^2`가 최소인 조건을 선택합니다. Ni 우선과 Co 우선은 각각 해당 금속의 예측 회수율을 최대화합니다. [추천 기준과 결과 상태](module3_optimization/README.md)

원본 정제, 모델 비교, 재학습과 중요도를 재현하려면 아래 명령을 실행합니다. 각 명령의 기본 출력 폴더에 있는 배포 결과는 다시 생성될 수 있습니다.

```bash
python -m module1_preprocessing.pipeline
python -m module2_prediction.evaluate
python -m module2_prediction.train
python -m module2_prediction.importance
```

루트의 `requirements.txt`는 기존 회귀 평가 함수 `evaluate_regression`의 의존성 파일입니다. 모델과 노트북은 위 설치 절차를 따릅니다.

## 웹 대시보드와 Unity 시연

`web/`에는 React 대시보드와 FastAPI 서버가 있습니다. 실제 분석 모드 `A_ADAPTER=live`는 `A_API_BASE_URL`로 지정한 팀의 별도 HTTP 분석 서비스를 호출합니다. 위 모델 명령은 Python에서 독립적으로 실행합니다. [대시보드 실행과 모의·실제 연동](web/README.md) · [Unity 연동 예제](web/integration/unity/README.md)

웹·서버와 Unity는 2026년 11월 19일 통합·시연 체크포인트를 포함합니다. 11월 18일 팀 환경에서 웹·서버와 Unity Editor 사이의 명령 수신과 완료 보고를 확인했고, 이후 카메라·코드 변경은 Unity Editor와 로컬 시험 서버에서 검증했습니다. Unity Hub에서 `unity/` 폴더를 열고 회사 제공 에셋을 원본 패키지에서 복원한 뒤 기본 씬 `FactoryDemoExhibitionApi`를 실행합니다. [Unity 실행 및 에셋 복원](unity/README.md) · [Unity 진행 이력](unity/CHANGELOG.md)

전처리와 모델의 초기 실험 및 팀 진행 기록은 기존 보고서에서 확인할 수 있습니다. [프로젝트 진행상황 보고서](docs/REPORT.md)
