# Module 2 — Ni/Co 예측, 학습 재현 및 변수 중요도

이 모듈은 기존 `curve17`의 학습 완료 수치를 사용한 예측과, 그 수치가 만들어진 개발 데이터 학습·검증 절차를 제공합니다. Ni와 Co는 별도의 Ridge 모델입니다. 기본 추론은 `artifacts/frozen_model.json`을 읽으며, 학습 함수는 비교용 `results/refit_model.json`을 생성합니다. 재학습 결과가 기존 추론 모델을 덮어쓰지 않습니다.

학습·평가 결과는 이미 사용했던 개발 데이터의 재현입니다. 신규 독립 검증이나 실제 설비 운전 승인에 해당하지 않습니다. 배치 ID의 숫자 순서를 사용하며, 실제 달력상의 시간 순서인지는 별도 검증되지 않았습니다.

## 의존성 설치

모델 재현 기준은 **Python 3.12**입니다. 저장소 루트에서 Python 3.12로 가상환경을 만들고 활성화합니다.

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell에서는 .\.venv\Scripts\Activate.ps1
python -m pip install -r module2_prediction/requirements.txt
```

## 실행

먼저 고정 모델로 예제의 Ni·Co 회수율을 예측할 수 있습니다.

```bash
python -m module2_prediction.inference --input data/examples/example_input.json
```

저장소 루트에서 실행합니다. 전처리된 CSV를 먼저 만들 필요 없이 동봉 RAW 파일부터 모듈 1의 동일한 정제 규칙으로 시작합니다.

```bash
python -m module2_prediction.evaluate
python -m module2_prediction.train
python -m module2_prediction.importance
```

세 명령은 모두 `--data PATH`와 `--output-dir PATH`를 받습니다. 기본 결과 폴더는 `module2_prediction/results`입니다. `--data`는 같은 RAW 자료의 다른 경로나 동일한 구조의 원본 CSV를 지정하는 옵션입니다. 재현 프로토콜은 정제 후 420행을 요구합니다. `development_imputed.csv`는 교차검증 입력으로 사용하지 않습니다.

평가·학습·중요도는 Python에서도 호출할 수 있습니다.

```python
from pathlib import Path
import pandas as pd
from module2_prediction.evaluate import evaluate_models
from module2_prediction.train import train_final
from module2_prediction.importance import run_importance

result = evaluate_models(data_path=None, output_dir=None)
metrics = pd.read_csv(Path(result["output_dir"]) / result["files"]["metrics"])

refit = train_final(data_path=None, output_dir=None)
importance = run_importance(data_path=None, output_dir=None)
```

반환 딕셔너리에는 `output_dir`와 상대 파일명 매핑 `files`가 있습니다. 평가 함수는 `metrics`, `reproduction`을, 학습 함수는 `selected_alphas`, `fit_rows`, `comparison`을, 중요도 함수는 `permutation_importance`, `coefficient_rows`, `comparison`을 추가로 반환합니다. 저장되는 JSON의 파일 참조는 상대 파일명이며, NaN/Infinity를 기록하지 않고 사용할 수 없는 값은 `null`로 저장합니다.

## 누수 방지와 후보 정의

모듈 1의 RAW 정제 결과 420행 중 첫 357행만 사용합니다. 마지막 63행은 이 모듈에서 학습, 튜닝, 예측, 점수 계산에 사용하지 않습니다. 바깥쪽 `TimeSeriesSplit(n_splits=3)`은 다음과 같습니다.

| Fold | 학습 행 | 검증 행 | 검증 배치 순서 |
|---|---:|---:|---|
| 1 | 90 | 89 | 91–179 |
| 2 | 179 | 89 | 180–268 |
| 3 | 268 | 89 | 269–357 |

각 바깥 학습 구간 안에서 다시 3개 시간순 분할을 만들어 Ridge alpha를 `0.1, 1, 10, 100` 중 원래 회수율 단위의 pooled MAE가 가장 낮은 값으로 선택합니다. 모든 개별 fit은 새 `FoldPreprocessor`와 `StandardScaler`를 가집니다. 대치값, 등급별 유효 관측 수, 스케일 평균·표준편차를 해당 학습 구간에서만 계산합니다. 타깃은 대치하지 않습니다.

| Candidate | 입력 및 모델 | 선택 방법 |
|---|---|---|
| `baseline` | Ni: ElasticNet(A) + Ridge(B_Impurity) + RBF SVR(B_Impurity) 고정 가중 앙상블. Co: Ridge(A, alpha=0.1) | 이전 설정·가중치를 고정하고 각 바깥 학습 구간에서 다시 적합 |
| `ridge11` | 원본 11개 입력 + Ridge | 내부 CV로 alpha 선택 |
| `curve17` | 원본 11개 + 공정 제곱 3개 + 공정 곱 3개 + Ridge | 내부 CV로 alpha 선택 |
| `bounded17` | curve17 입력 + 회수율 logit 변환 + Ridge | 역변환 후 원래 단위 MAE로 alpha 선택 |
| `interaction20` | curve17 + 불순물합계 × 산·온도·시간 3개 + Ridge | 내부 CV로 alpha 선택 |

Ni baseline의 정확한 설정은 ElasticNet `alpha=0.1, l1_ratio=0.8, max_iter=20000, random_state=42`, Ridge `alpha=1`, SVR `C=10, epsilon=0.1, gamma="scale", kernel="rbf"`입니다. 순서대로 가중치는 `0.3366978614608818`, `0.3365960332725443`, `0.3267061052665740`입니다. 모든 구성 모델은 표준화합니다. `B_Impurity`는 원본 11개에 황산/원료 비율과 Cu+Fe+Al 합계를 추가한 13개입니다.

curve17의 파생 항은 황산투입량을 $a$, 침출온도를 $t$, 침출시간을 $h$라 할 때 $a^2,t^2,h^2,at,ah,th$입니다. 입력의 실제 단위에서 항을 생성한 후 17개 항을 표준화합니다. `bounded17`은 $q=y/100$과 $\log(q/(1-q))$를 사용하고, 정확한 0 또는 100 라벨에만 `eps=1e-5`를 적용합니다. 예측은 $100\operatorname{sigmoid}(z)$로 역변환합니다.

추천 모드의 결과가 서로 다른지, 예측 목표를 달성하는 후보가 몇 개인지는 모델 선택 기준에 포함하지 않습니다.

## 재현된 검증 결과

아래 값은 267개 바깥 검증 배치의 pooled 오차입니다. MAE/RMSE 단위는 회수율 퍼센트포인트(pp)입니다. 상세 값은 [metrics.csv](results/metrics.csv), fold별 결과는 [fold_metrics.csv](results/fold_metrics.csv)에 있습니다.

| Candidate | Ni MAE | Ni RMSE | Co MAE | Co RMSE |
|---|---:|---:|---:|---:|
| baseline | 1.872871 | 2.328829 | 2.079797 | 2.685718 |
| ridge11 | 1.955064 | 2.405085 | 2.079797 | 2.685718 |
| curve17 | **1.741881** | **2.196502** | **1.905236** | **2.519481** |
| bounded17 | 2.199302 | 2.742255 | 2.001817 | 2.620013 |
| interaction20 | 1.756510 | 2.206910 | 1.951368 | 2.560056 |

curve17은 baseline 대비 pooled MAE가 Ni 약 6.994%, Co 약 8.393% 낮았고, 두 금속 모두 바깥 3개 fold의 MAE가 낮았습니다. 이 결과는 개발 데이터 재사용 조건의 비교입니다. `bounded17`은 Ni에서 오차가 커졌고, `interaction20`도 curve17보다 두 금속의 pooled MAE/RMSE가 커서 기본 모델을 교체하지 않습니다. 사전 정의된 후보의 결과를 모두 남깁니다.

보관된 증거 파일 [model_comparison_reference.json](reference/model_comparison_reference.json)과 현재 실행 결과를 비교하면, 300개 pooled/fold 수치 비교의 최대 절대 차이는 `2.842170943040401e-14`였고 alpha 선택 및 9개 집단별 목표 분류의 정수 개수 차이는 없었습니다. 결과는 [evaluation_reproduction.json](results/evaluation_reproduction.json)에 기록됩니다. 보관된 재현 기록은 Python 3.12.14, 원 기록은 Python 3.13.5 환경에서 작성했습니다. NumPy 2.3.5, SciPy 1.17.0, scikit-learn 1.8.0은 동일합니다. 마지막 비트까지 모든 플랫폼에서 일치한다고 주장하지 않습니다.

### Ni≥95%, Co≥90% 목표 분류

이는 실제 관측 조건에서의 curve17 OOF 예측을 분류한 결과이며, 최적화된 새 공정 조건의 성공률 검증이 아닙니다.

| 목표 | 실제 달성 | 예측 달성 | TP | FP | FN | TN | Precision | Recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Ni≥95 | 14 | 6 | 3 | 3 | 11 | 250 | 0.500 | 0.214 |
| Co≥90 | 5 | 3 | 3 | 0 | 2 | 262 | 1.000 | 0.600 |
| 동시 달성 | 2 | 2 | 1 | 1 | 1 | 264 | 0.500 | 0.500 |

특히 Co의 precision 1.0은 예측 달성 사례 3개에 대한 기술통계입니다. 실제 고회수율 사례와 동시 달성 사례가 적으므로 보장이나 보정된 확률로 해석하지 않습니다. [target_classification.csv](results/target_classification.csv)는 전체 267행 외에 원본 11개 입력이 모두 관측된 113행, 공정 4개 입력이 모두 관측된 213행도 따로 기록합니다.

## 최종 개발구간 재학습과 수치 비교

`train_final`은 첫 357행의 내부 3-fold CV로 각 금속의 alpha를 새로 선택한 후, 357행 전체에 각각 적합합니다. 두 금속 모두 `alpha=0.1`이 선택됩니다. 모델 상태는 다음 구조입니다.

| JSON 필드 | 내용 |
|---|---|
| `model_version` | `YP-curve17-dev357-v2` |
| `fit_rows` | 357 |
| `features` | 원본 11개 입력의 순서 |
| `parameters` | Ni, Co 순서의 2×52: mean17 + scale17 + coef17 + intercept1 |
| `distance_mean`, `distance_scale` | 완전 관측 개발 151행으로 적합한 원본 11개 입력 표준화 통계 |
| `distance_points` | 대치 전 완전 관측 개발 자료 151×11 |
| `distance_threshold` | 각 참조행에서 자기 자신을 제외한 최근접 거리들의 95% 분위수 |
| `selected_alphas` | 금속별 선택 alpha |

거리 기준은 개발 151개 참조행의 표준화된 11차원 Euclidean 거리에서 계산합니다. 예측 신뢰구간이나 타깃 성공 확률이 아닙니다.

[refit_comparison.json](results/refit_comparison.json)은 frozen 상태와 재학습 결과를 비교합니다. 이번 재현의 계수 최대 절대 차이는 Ni `9.237055564881302e-14`, Co `1.936228954946273e-13`입니다. 전체 상태 최대 차이 `2.3283064365386963e-10`은 값이 큰 황산 제곱항의 스케일 통계에서 발생하며, 상대적으로는 부동소수점 정밀도 수준입니다. 151개 거리 참조값과 거리 임계값은 정확히 일치합니다.

357개 개발 대치 입력, 151개 완전 관측 입력, seed 42로 만든 범위 내 1,000개 합성 입력에서 frozen 대비 예측 최대 차이는 `1.2789769243681803e-13` pp였습니다. 합성 입력은 직렬화·수치 계산 검사용이며 새 라벨 검증 데이터가 아닙니다. 원본 frozen 모델은 유지됩니다.

## 변수 중요도

[permutation_importance.csv](results/permutation_importance.csv)는 **원본 11개 입력**을 하나씩 섞은 후의 검증 MAE 증가량을 기록합니다. 각 outer validation에서 10번, seed 42로 수행합니다. 각 예측은 해당 outer train에서 이미 적합한 대치기·표준화기를 사용하며, 제곱항과 곱항을 다시 계산합니다. 검증 라벨로 재학습하지 않습니다. 금속별 11행, 총 22행의 평균·표준편차와 660개 개별 결과를 저장합니다.

가장 큰 평균 ΔMAE는 온도(Ni 1.597 pp / Co 2.040 pp), 시간(Ni 1.431 / Co 1.250), 황산(Ni 1.409 / Co 1.241)이었습니다. 이는 현재 모델이 해당 입력 정보에 의존하는 정도입니다. 입력을 조작했을 때 실제 회수율이 그만큼 변한다는 뜻은 아닙니다.

표준편차는 3개 fold × 10번, 30개 ΔMAE의 표본 표준편차(`ddof=1`)이며 신뢰구간이 아닙니다. 바깥 학습 구간들이 겹치고 반복 순열도 독립 관측이 아닙니다. 상관된 입력은 서로의 정보를 대신할 수 있으므로 작은 중요도나 음의 중요도가 변수 불필요성을 입증하지 않습니다. 순열은 원래 입력의 주변분포를 유지해도 상관관계를 깨뜨려 관측 지지가 약한 조합을 만들 수 있습니다. 이 진단에는 거리 또는 운영 가능성 필터를 적용하지 않습니다.

[standardized_coefficients.csv](results/standardized_coefficients.csv)는 최종 curve17의 17개 모델 항 × 2개 금속, 총 34행입니다. `StandardizedCoefficient`는 표준화한 모델 항의 Ridge 계수입니다. 원본 입력과 제곱항·곱항은 상관되어 있으며, 곱항이 있으므로 계수 한 개를 독립 공정 효과로 해석할 수 없습니다. `RawBasisCoefficient`는 그 항의 계수/스케일이며 전체 모델의 원본 입력에 대한 도함수가 아닙니다. 원인·결과나 개별 변수의 필요성을 주장하지 않습니다.

## 결과 파일 안내

| 파일 | 내용 |
|---|---|
| `metrics.csv` | 10행의 후보·금속별 pooled MAE/RMSE/R²/P90/최대오차/편향 |
| `fold_metrics.csv` | 30행의 fold별 alpha, 학습·검증 오차와 MAE gap |
| `oof_predictions.csv` | 267 × 2 × 5 = 2,670행의 실제값·예측값·잔차 |
| `tuning_results.csv` | 288행의 내부 alpha/fold MAE, pooled MAE 및 선택 여부 |
| `target_classification.csv` | 전체/완전관측/공정완전관측별 9행의 목표 분류 |
| `evaluation_fit_audit.json` | 324개 개별 pipeline fit의 대치·표준화 상태 및 학습 행 범위 |
| `evaluation_reproduction.json`, `evaluation_summary.json` | 원기록 수치 차이, 프로토콜·버전·결과 요약 |
| `refit_model.json`, `final_tuning_results.csv` | 전체 개발구간 curve17 수치 및 24개 내부 튜닝 결과 |
| `training_fit_audit.json`, `training_summary.json`, `refit_comparison.json` | 최종 재학습 26개 fit의 증거와 frozen 비교 |
| `permutation_importance.csv`, `permutation_importance_details.csv`, `permutation_importance_by_fold.csv` | 원본 입력 순열 중요도 22/660/66행 |
| `standardized_coefficients.csv` | 최종 curve17의 표준화 계수 34행 |
| `importance_fit_audit.json`, `importance_tuning_results.csv`, `importance_refit_comparison.json`, `importance_summary.json` | 중요도 실행의 104개 fit, 튜닝·frozen 비교·해석 한계 |
| `predicted_vs_actual.png`, `residuals.png`, `model_mae_comparison.png` | OOF 예측 및 후보 비교 그림 |
| `permutation_importance.png`, `standardized_coefficients.png` | 순열 중요도 및 계수 그림 |

모든 수치는 실행으로 생성합니다. 원본 증거, 보류 구간, frozen 추론 상태를 수정하지 않습니다.
