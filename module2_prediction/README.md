# Module 2 회수율 예측 Model1

Ni·Co 회수율을 예측하는 Model1의 선행 실험을 정리합니다. 학습 코드·학습 데이터·저장 모델은 아직 이 저장소에 통합하지 않았습니다.

## 확인된 실험

- Random Forest 기본 변수 11개와 파생변수 포함 19개 비교.
- A 기본 11개, B 황산/원료비 추가, C 불순물합계 추가, D 불순물/목표금속비 추가 조합 비교.
- 총 12개 입력의 모델 B를 유력 후보로 선택했으며 최종 확정은 아님.
- Train+Validation 재학습 후 Test R²는 Ni 0.7866, Co 0.8062.
- 별도 동일 학습 모델 기준 과적합 진단의 Test R²는 Ni 0.7680, Co 0.8004. 위 재학습 결과와 구분.
- 과적합 개선과 최종 모델 확정은 미완료. XGBoost·LightGBM·SHAP 수행 완료는 확인되지 않음.

## 현재 포함된 코드

`evaluate.py`의 `evaluate_regression(y_true, y_pred, prefix="Test")`는 기존 RMSE·MAE·R² 계산 함수입니다. 이 함수는 변경하지 않고 유지했습니다. 모델을 학습하거나 공정 데이터를 자동으로 읽는 실행기는 아닙니다.

저장소 루트의 `requirements.txt`는 이 함수가 사용하는 numpy·scikit-learn만 정의합니다. `__init__.py` 없이도 저장소 루트에서는 Python 3의 namespace package로 가져올 수 있습니다.

학습·SHAP 예제 래퍼는 정리했습니다. 실제 실험 코드를 통합할 때 분할 기준, 입력 목록, 설정, 학습된 통계와 모델, 결과 재현 절차를 함께 추가합니다.

[진행상황 보고서](../docs/REPORT.md)
