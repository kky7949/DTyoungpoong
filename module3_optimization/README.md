# Module 3 — 최적 공정 레시피 추천

`optimizer.py`는 고정된 원료 입력8개(조성7개·원료량)를 유지하고 황산량·온도·시간만 탐색합니다. 모든 목적은 Module2의 같은 예측값과 같은 지원범위 검사를 사용합니다.

| 목적 | 후보 조건 | 선택 기준 |
|---|---|---|
| 목표 달성형 | Ni≥설정 최소치, Co≥설정 최소치 | 기본은 `(100-Ni)^2+(100-Co)^2` 최소, 선택적으로 `maximin` |
| Ni 우선 | 두 출력의0~100범위와 지원범위 검사 | Ni 최대, 동률이면 Co, 그 다음 후보 순번 |
| Co 우선 | 두 출력의0~100범위와 지원범위 검사 | Co 최대, 동률이면 Ni, 그 다음 후보 순번 |

Ni 우선에는 Co 최소치를, Co 우선에는 Ni 최소치를 적용하지 않습니다. 산·자원 비용 최소화 항은 없습니다. 공통 최적 후보라면 세 목적이 같아도 그대로 반환합니다. 100% 초과 출력은100으로 자르지 않고 후보에서 제외합니다.

## 실행

Python 3.12로 모델 환경을 준비한 뒤 저장소 루트에서 실행합니다. [의존성 설치](../module2_prediction/README.md#의존성-설치)

```bash
python -m module3_optimization.recommend --input data/examples/example_input.json
python -m module3_optimization.recommend --input data/examples/example_no_joint_target.json --output module3_optimization/results/no_joint_target.json
python -m module3_optimization.recommend --acid-step 25 --temperature-step 2.5 --time-step 0.25
```

기본은 황산400~1500L/50L,온도40~95℃/5℃,시간1~8h/0.5h의4,140개입니다. 마지막 명령은30,015개입니다. 소수점 간격을 지원하지만 메모리·응답시간을 위해50,000개를 넘으면 명확한 오류를 냅니다. 격자를 세분화하는 것은 고정 모델의 탐색 정밀도 변경이며 모델의 검증 MAE 개선이 아닙니다.

`recommendations.json`은 현재조건 예측,목적별 대표/상위3개,최소치 여유분,거리,제외수와 상태를 저장합니다. CSV와 입력별1변수 반응 그래프도 함께 생성합니다.

## 결과 상태

- `RECOMMENDED_ON_PREDICTION`: 주어진 모델·탐색격자의 예측상 추천.
- `TARGET_NOT_FOUND_IN_GRID`: 지원되는 후보에서 두 목표를 함께 충족하지 못함. `closest_alternative`는 미달 대안이며 추천 성공이 아닙니다.
- `TARGET_FOUND_BUT_UNSUPPORTED`: 목표는 예측상 넘지만 지원범위 검사를 통과하지 못함.
- `NO_SUPPORTED_CANDIDATE`: 물리적 출력범위는 맞지만 지원되는 후보가 없음.
- `NO_VALID_MODEL_OUTPUT`: 유한한0~100% 출력 후보가 없음.

거리 기준은 완전 관측 개발151행으로 계산한 표준화 최근접거리의 경험적 기준입니다. 신뢰구간·실제 달성확률·공정 안전 인증이 아닙니다. 원료별 반응기작과 현장 최적조건을 새 실험으로 검증한 결과도 아닙니다.

Jupyter에서는 `from module3_optimization.ui import launch; app=launch()`로 입력 패널을 사용할 수 있습니다. 입력이 바뀌면 이전 결과가 무효화됩니다.
