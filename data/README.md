# 데이터 출처와 파일 안내

## 원본과 범위

출처는 과제에서 제공한 **`영풍그룹_금속회수율최적화_RawMaterialData_학생배포용.xlsx`** 한 개입니다. 외부 공정 자료, 인터넷에서 수집한 관측값, 별도 기업 데이터를 추가하지 않았습니다.

`raw/youngpoong_raw.xlsx`는 수업 제공 원본의 두 시트와 데이터를 보존하고, 문서 속성에서 개인을 식별할 수 있는 마지막 수정자 항목을 제거한 배포용 파일입니다. 배포본의 SHA-256은 다음과 같습니다.

```text
2af3f5da454838269c3afbb51767deb3c4f83b50199c2de5ad9e1ea8726cdd64
```

원본에는 `원료분석_원본데이터` 424행 × 16열과 `데이터사전` 16행 × 4열이 있습니다. 원본 필드는 배치 ID, 분석일자, 원료등급, 숫자 입력 11개, Ni·Co 회수율 타깃 2개입니다. 이름·연락처·보안 관련 필드는 관찰되지 않았습니다. 이는 관찰한 필드 목록에 대한 설명입니다.

## 단위와 사전 범위

`pct` 값은 백분율 숫자 자체입니다. 예를 들어 Ni 함량 `20`은 20 wt%, Ni 회수율 `90`은 90%이며 `0.20`, `0.90`으로 변환하지 않습니다.

| 입력 컬럼 | 단위 | 허용 범위(경계 포함) |
|---|---|---:|
| `Ni_함량_pct` | wt% | 8–30 |
| `Co_함량_pct` | wt% | 2–15 |
| `Li_함량_pct` | wt% | 2–6 |
| `Mn_함량_pct` | wt% | 5–16 |
| `Cu_불순물_pct` | wt% | 0.3–6 |
| `Fe_불순물_pct` | wt% | 0.2–6 |
| `Al_불순물_pct` | wt% | 0.5–7 |
| `원료투입량_kg` | kg | 80–200 |
| `황산투입량_L` | L | 400–1500 |
| `침출온도_C` | °C | 40–95 |
| `침출시간_hr` | hr | 1–8 |

`Ni_회수율_pct`, `Co_회수율_pct`의 단위는 %입니다. 타깃이 결측이거나 0–100% 밖이면 파이프라인은 오류를 냅니다. 타깃을 대치하지 않습니다. 원본 데이터사전에는 타깃 범위가 `-`로 적혀 있으며, 0–100% 검사는 회수율 타깃에 별도로 적용한 검증 규칙입니다.

## 정제와 분리

배치 ID 공백과 원료등급 표기를 정규화하고, 중복 ID의 첫 번째 원본 행을 유지합니다. 중복 4행을 제거한 420행을 **배치 ID 끝 숫자**로 안정 정렬합니다. `분석일자`의 혼합 표기는 원본 메타데이터로 보존합니다. 배치 순서가 실제 시간 순서라는 검증은 수행하지 않았습니다.

| 구간 | 행수 | 배치 범위 | 입력 결측 셀 | 용도 |
|---|---:|---|---:|---|
| 정제 전체 | 420 | 0001–0420 | 345 | 원본 정제 기록 |
| 개발 | 357 | 0001–0357 | 303 | 모델 선택, fold별 전처리, 최종 개발 학습 |
| 보류 | 63 | 0358–0420 | 42 | 현재 전처리·학습 fit에서 제외 |

개발 357행 중 151행은 입력 11개가 모두 관측되어 있습니다. 사전 범위 밖 입력은 결측 처리하며, IQR 경계 밖의 **검토 후보 16개 셀은 삭제하지 않습니다**. IQR은 개발 구간에서 변수별 관측값으로 계산했습니다.

보류 구간은 프로젝트 중 이미 열람된 자료이므로 **독립적인 신규 블라인드 테스트라고 주장할 수 없습니다.** 이 구간의 타깃이 파일에 포함된 것은 데이터 보존을 위한 것이며, 이번 전처리 통계 계산에 사용하지 않습니다.

## 파일별 용도

모든 CSV는 UTF-8 BOM으로 저장했습니다. 결측은 빈 셀입니다.

| 파일 | 내용과 사용 목적 |
|---|---|
| `raw/youngpoong_raw.xlsx` | 두 원본 시트가 포함된 배포용 XLSX |
| `raw/youngpoong_raw.csv` | 원본 데이터 시트 424행의 CSV 추출본 |
| `raw/data_dictionary.csv` | 제공 데이터사전 그대로 추출 |
| `processed/cleaned420.csv` | 중복 제거·숫자 변환·사전 범위 마스킹, 결측 유지 |
| `processed/development357.csv` | 개발 구간, 결측 유지. 교차검증의 입력 |
| `processed/holdout63.csv` | 보류 구간, 결측 유지 |
| `processed/development_imputed.csv` | 개발 357행만으로 대치한 원래 16개 컬럼. 메타데이터·타깃 포함 |
| `processed/development_features17.csv` | 개발 행의 17개 입력 특징만 저장. 타깃·메타데이터 없음 |
| `processed/development_standardized17.csv` | 같은 17개 입력의 개발 표준화 결과 |
| `processed/imputer_state.json` | 개발 전체 중앙값, 등급별 중앙값·관측수, 변수별 대치 셀수 |
| `processed/scaler_state.json` | 17개 특징의 순서, 평균, 표준편차, 분산(ddof=0) |
| `processed/audit.json` | 배포 XLSX 해시, 행수, split, 중복 ID, 범위·결측·대치·IQR 처리 기록 |
| `processed/quality/missing_counts.csv` | 원본 결측·중복 제거 후 결측·범위 마스킹·개발/보류 결측 집계 |
| `processed/quality/missing_counts.png` | 대치 전 개발/보류 입력 결측수 |
| `processed/quality/development_summary.csv` | 개발 관측값의 기초통계 |
| `processed/quality/development_distributions.png` | 개발 관측값의 분포, 관측 표본수 표시 |
| `processed/quality/development_correlation.csv` | 개발 관측값의 pairwise Pearson 상관계수 |
| `processed/quality/correlation_pair_counts.csv` | 상관계수마다 사용한 관측 행수 |
| `processed/quality/development_correlation.png` | 상관계수 그림 |
| `processed/quality/outlier_rules.csv` | 개발 관측값으로 계산한 Q1/Q3/IQR/1.5×IQR 경계 |
| `processed/quality/outlier_candidates.csv` | IQR 검토 후보와 `retain_for_review` 처리 |

특징·표준화 CSV의 행 순서는 `development357.csv`와 같으며 행을 추가·삭제하지 않습니다. 기본 입력 11개 순서와 특징 확장 수식은 [Module 1 설명](../module1_preprocessing/README.md)에 있습니다.

## 누수 없이 사용하는 법

개발 전체로 대치한 파일과 표준화 파일은 최종 개발 학습 결과를 설명하기 위한 출력입니다. **이 출력을 다시 교차검증에 넣지 마세요.** 각 학습 fold의 결측 유지 데이터에서 `FoldPreprocessor`와 `StandardScaler`를 새로 fit하고, 그 상태를 해당 검증 fold에 적용해야 합니다.

화학 성분 7개는 등급별 관측값이 변수별로 5개 이상이면 학습 등급 중앙값을 사용하고, 그 외에는 학습 전체 중앙값을 사용합니다. 공정 입력 4개는 학습 전체 중앙값을 사용합니다. 보류 63행을 포함한 420행 전체에서 중앙값을 fit하지 않습니다.

## 재생성

저장소 루트에서 [설치 안내](../notebooks/README.md)에 따라 의존성을 설치한 뒤 다음 명령으로 정제 파일을 재생성합니다.

```bash
python -m module1_preprocessing.pipeline
```

원본 정제·대치 기준은 제공된 `youngpoong_nested_model_selection(1).py`, A17 특징 순서는 기존 curve17 모델을 기준으로 맞췄습니다. 기존 curve17 대비 개발 표준화 평균의 최대 절대 차이는 약 4.55×10⁻¹², 표준편차는 약 2.33×10⁻¹⁰으로 부동소수점 수준입니다. 결과는 [audit.json](processed/audit.json)과 [scaler_state.json](processed/scaler_state.json)에서 확인할 수 있습니다.
