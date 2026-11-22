# Module 1 — 원본 정제와 전처리

제공된 원본을 읽어 **424행 → 중복 제거 후 420행 → 개발 357행 / 보류 63행**으로 분리합니다. 개발 구간의 입력 11개가 모두 관측된 행은 **151행**입니다. 표준화·대치 통계는 개발 357행에서만 계산합니다.

## 실행

Python 3.12로 모델 환경을 준비한 뒤 저장소 최상위 폴더에서 실행합니다. 입력·출력 경로의 기본값은 `__file__`을 기준으로 찾습니다. [의존성 설치](../module2_prediction/README.md#의존성-설치)

```bash
python -m module1_preprocessing.pipeline
python -m module1_preprocessing.pipeline --data-path data/raw/youngpoong_raw.csv --output-dir .venv/youngpoong-preprocessing
python -m pytest module1_preprocessing/tests -q
```

추가 업로드, 대화형 입력, 자동 패키지 설치가 없습니다. 원본 XLSX는 다시 작성하지 않고 그대로 보존합니다. 선택한 대체 데이터의 행수가 달라도 정식 배포 파일명인 `cleaned420.csv` 등은 유지되며 실제 행수는 `audit.json`에 기록됩니다.

## 공개 API

| 위치 | API | 역할 |
|---|---|---|
| `schema.py` | `BASE`, `CHEM`, `PROCESS`, `TARGETS`, `LIMITS`, `ROOT` | 원본 입력 순서, 타깃, 사전 범위, 저장소 경로 |
| `pipeline.py` | `load_raw_data(path=None)` | 원본 XLSX 또는 CSV를 읽어 DataFrame 반환 |
| `pipeline.py` | `load_clean_data(path=None)` | 결측을 유지한 정제 DataFrame 반환 |
| `pipeline.py` | `FoldPreprocessor(feature_mode='A17')` | 학습 행에서 중앙값을 추정하고 지정한 특징 행렬 반환 |
| `pipeline.py` | `run_preprocessing(data_path=None, output_dir=None)` | CSV·통계 JSON·품질표·그림 생성 |
| `features.py` | `feature_matrix(x, mode='A17')` | 채워진 입력 11개를 지정 특징으로 변환 |
| `features.py` | `feature_names(mode='A17')` | 출력 행렬과 동일한 순서의 컬럼명 목록 |

`run_preprocessing()`의 반환값은 `{'output_dir': str, 'files': {key: path}, 'audit': dict}`입니다. 주요 집계는 `result['audit']['rows']`, 컬럼별 처리 내역은 `result['audit']['input_quality']`에 있습니다.

## 정제 규칙

1. 배치 ID의 앞뒤 공백을 제거합니다. 원료등급은 공백 제거, 대문자 변환, `급` 제거 후 A/B/C인지 확인합니다.
2. 정규화한 배치 ID가 중복되면 원본에서 처음 등장한 행을 유지합니다. 중복 4행을 제외한 뒤 ID 끝의 숫자로 안정 정렬합니다.
3. `분석일자`는 원본 메타데이터 그대로 보존하며 날짜 변환·모델 입력·정렬에 사용하지 않습니다. **배치 순서를 실제 날짜 순서로 검증했다는 의미가 아닙니다.**
4. 입력 11개를 숫자로 변환합니다. 숫자 변환 실패나 데이터사전 범위 밖 값은 결측으로 바꿉니다. 범위 경계값은 허용합니다.
5. Ni·Co 회수율은 숫자이고 관측되어 있으며 0–100%여야 합니다. 위반하면 중단합니다. 타깃은 대치하지 않습니다.
6. IQR 후보는 검토용으로 기록하고 유지합니다. 사전 범위 마스킹과 통계적 이상치 후보 선정을 구분합니다.

원본 정제에서 입력 결측은 345개입니다. 개발 구간은 303개, 보류 구간은 42개입니다. 자세한 원인·변수별 수치는 [품질표](../data/processed/quality/missing_counts.csv)를 참조합니다.

## 학습 fold 안에서 대치

화학 성분 7개는 해당 학습 fold에서 원료등급별 관측값이 **변수별로 5개 이상**이면 등급별 중앙값을 사용합니다. 관측값이 적거나 해당 등급이 없으면 학습 fold 전체 중앙값을 사용합니다. 원료투입량·황산투입량·온도·시간 4개는 학습 fold 전체 중앙값을 사용합니다. 학습 구간 전체에 관측값이 없는 입력은 오류로 처리합니다.

`global_median_`은 Series이고 `grade_median_`, `grade_count_`는 DataFrame입니다. 타깃 `y`는 사용하지 않으며 transform은 입력 DataFrame을 수정하지 않습니다. sklearn `clone`과 `Pipeline`에서 사용할 수 있습니다.

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from module1_preprocessing.pipeline import load_clean_data, FoldPreprocessor
from module1_preprocessing.schema import BASE, TARGETS

clean = load_clean_data()
development = clean.iloc[:int(len(clean) * 0.85)]
X = development[list(BASE) + ['원료등급']]
y = development[TARGETS['Ni']]
pipeline = Pipeline([
    ('preprocess', FoldPreprocessor('A17')),
    ('scale', StandardScaler()),
    ('model', Ridge(alpha=1.0)),
])
# 각 교차검증 반복에서 pipeline.fit(X.iloc[train_idx], y.iloc[train_idx])
# 그 반복의 검증 행에는 pipeline.predict(X.iloc[valid_idx])를 적용합니다.
```

`development_imputed.csv`, `development_features17.csv`, `development_standardized17.csv`는 **개발 전체에서 한 번 fit한 결과를 설명하는 출력**입니다. 이 파일들을 교차검증 입력으로 쓰면 검증 행의 정보가 전처리 통계에 들어갑니다. 교차검증은 `development357.csv` 또는 `load_clean_data()`에서 시작해야 합니다.

## 특징 순서

기본 11개는 Ni, Co, Li, Mn, Cu, Fe, Al, 원료투입량, 황산투입량, 침출온도, 침출시간 순서입니다. 아래 A는 황산투입량(L), T는 온도(°C), h는 시간(hr)입니다.

| 모드 | 특징 수 | 기본 11개 뒤에 추가하는 항목 |
|---|---:|---|
| `A`, `A11` | 11 | 없음 |
| `B` | 12 | 황산/원료 비(L/kg) |
| `B_Impurity` | 13 | 황산/원료 비, Cu+Fe+Al 불순물 합(wt%) |
| `B_TempTime` | 13 | 황산/원료 비, T×h |
| `A17` | 17 | A², T², h², A×T, A×h, T×h |
| `A20` | 20 | A17 다음에 불순물 합×A, 불순물 합×T, 불순물 합×h |

A17의 추가 컬럼명은 `acid2_L2`, `temp2_C2`, `time2_hr2`, `acid_temp_L_C`, `acid_time_L_hr`, `temp_time_C_hr`입니다. 특징 확장은 대치 후, 표준화 전에 적용합니다. StandardScaler는 개발 학습 데이터의 평균과 모집단 표준편차(ddof=0)를 사용합니다.

## 근거와 한계

정제·대치 규칙은 제공된 `youngpoong_nested_model_selection(1).py`의 원본 구현을 따릅니다. A17/A20은 제공된 기존 모델의 수치 변환 순서를 따릅니다. 원본은 [데이터사전 CSV](../data/raw/data_dictionary.csv)와 [정제 감사 기록](../data/processed/audit.json)으로 추적할 수 있습니다. 외부 공정 데이터는 사용하지 않았습니다.

보류 63행은 이번 모듈의 fit에서 제외하지만, 프로젝트 중 이미 열람된 구간이므로 새 블라인드 테스트로 주장하지 않습니다. 분포·상관계수·IQR 경계는 개발 구간의 관측값으로 계산했습니다. 상관계수는 각 변수쌍의 관측 행만 사용하므로 비교마다 표본수가 다를 수 있습니다. [쌍별 표본수](../data/processed/quality/correlation_pair_counts.csv)를 함께 제공합니다.
