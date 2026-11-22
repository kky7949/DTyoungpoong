# 분석 노트북

01–03은 저장소의 데이터와 Python 모듈을 사용합니다. 노트북과 `data/`, `module1_preprocessing/`, `module2_prediction/`, `module3_optimization/`를 같은 저장소 루트에 둡니다.

| 노트북 | 내용 |
| --- | --- |
| [01 전처리](01_preprocessing.ipynb) | 원본, 결측·이상값 처리, 파생 특성, 표준화와 EDA |
| [02 회수율 예측](02_prediction.ipynb) | 교차검증, 모델 비교, MAE·RMSE, 중요도 |
| [03 공정조건 탐색](03_optimization.ipynb) | 세 가지 추천 목적, 목표 여유, 후보 순위, 반응곡선 |
| [04 단일 셀 데모](04_standalone_demo.ipynb) | 제출본에 보존된 최종 모델 데모 |

## 로컬 Jupyter

Python 3.12로 모델 환경을 준비합니다. 같은 가상환경에서 JupyterLab을 설치하고 저장소 루트에서 실행합니다. [의존성 설치](../module2_prediction/README.md#의존성-설치)

```bash
python -m pip install jupyterlab
jupyter lab
```

`notebooks/`에서 01 → 02 → 03 순으로 열고 각 노트북의 Python 커널에서 모든 셀을 실행합니다. 04는 `NumPy`와 `ipywidgets`를 사용하는 단일 셀 데모입니다.

## Colab

저장소 전체를 가져오거나 ZIP을 업로드한 뒤 압축을 풉니다. Colab의 작업 폴더를 압축을 푼 저장소 루트로 이동하고 Python 3.12 런타임에서 아래를 실행합니다.

```python
%pip install -r module2_prediction/requirements.txt
```

같은 런타임에서 01–03의 셀을 실행합니다. 04는 노트북 파일만 열어 단일 셀을 실행할 수 있습니다.
