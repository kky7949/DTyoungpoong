폐배터리 습식 제련 공정 최적화를 위한 AI 기반 디지털 트윈 시스템 🏭♻️

전기차 폐배터리 블랙파우더(Black Powder)의 습식 제련 공정에서 핵심 금속(니켈, 코발트 등)의 회수율을 극대화하기 위한 'AI 최적 공정 레시피 추천 및 3D 가상 공장(Digital Twin) 시각화 시스템'입니다.

본 프로젝트는 불균일한 원료 성분 데이터를 기반으로 머신러닝 예측 모델을 구축하고, 다목적 최적화 알고리즘을 통해 도출된 최적의 산(Acid) 투입량 및 반응 온도 레시피를 Unity 3D 기반의 웹 대시보드에 실시간으로 연동합니다.

🏗 시스템 아키텍처 및 핵심 기술

1. [Module 1] 데이터 전처리 (Data Preprocessing): 화학 반응 속도론(축소 코어 모델 등) 기반 파생 변수 생성 및 결측치 정제
2. [Module 2] 회수율 예측 모델링 (AI Prediction & XAI): XGBoost/Random Forest 기반 회수율 예측 및 SHAP(SHapley Additive exPlanations)을 이용한 변수 중요도 시각화
3. [Module 3] 공정 최적화 및 시스템 연동 (Optimization & Digital Twin): 다목적 메타 휴리스틱 알고리즘(NSGA-II)을 활용한 파레토 최적해 탐색, WebSocket API를 통한 Unity 3D 실시간 제어(ISO 23247 표준 지향)

📁 레포지토리 구조

DTyoungpoong/
├── data/                       # 원본 데이터 및 전처리된 데이터 (※ 보안 유의사항 참조)
├── module1_preprocessing/      # 결측치 처리, 이상치 탐지, 파생 변수 생성 파이프라인
│   └── preprocess.py
├── module2_prediction/         # 예측 모델 학습, 교차 검증 및 SHAP 해석 코드
│   └── train_predict.py
├── module3_optimization/       # 다목적 최적화 알고리즘 구현 및 WebSocket 서버 연동 코드
│   ├── optimize.py
│   └── server.py
├── notebooks/                  # 데이터 분석(EDA) 및 모델링 실험용 Jupyter Notebook
├── docs/                       # 기획서, 통합 분석 보고서(REPORT.md) 및 실행 가이드
└── README.md                   # 프로젝트 개요 및 가이드 (본 문서)


📊 데이터셋 설명 및 사용 시 유의사항

⚬ 데이터 소스: 폐배터리 블랙파우더 성분 분석 랩실 데이터 (니켈, 코발트 함량, 불순물 수치, 공정 온도, 시간, 산 투입량 등)
⚬ 사용 시 유의사항 (보안):
  ⚬ 본 레포지토리의 data/ 폴더에 포함된 원본 데이터는 기업 보안 및 개인정보 보호를 위해 비식별화/익명화 처리된 샘플(Dummy) 데이터셋입니다.
  ⚬ 실제 공장 데이터를 적용할 경우, 데이터 형식(Column 구조 등)이 본 샘플 데이터셋과 일치하는지 확인 후 파이프라인에 입력해야 합니다.

⚙️ 환경 설정 및 필수 라이브러리

본 프로젝트를 로컬 환경에서 실행하기 위해 다음의 소프트웨어 및 라이브러리가 필요합니다.

1. Python 백엔드 환경 (AI 연산)

⚬ Python 3.9+
⚬ 필수 라이브러리 설치:
  pip install pandas numpy scikit-learn xgboost shap websockets jupyter
  

2. 프론트엔드 환경 (3D 시각화)

⚬ Unity Editor 2022.3 LTS 이상
⚬ glTFUtility (3D 에셋 임포트용) 및 WebGL 빌드 모듈

🚀 모듈별 실행 방법 및 예시

[Module 1] 데이터 전처리

원본 엑셀/CSV 데이터를 로드하여 결측치를 대치하고 화학적 특성을 반영한 파생 변수를 생성합니다.

# module1 디렉토리에서 실행
python module1_preprocessing/preprocess.py --input ../data/raw_data.csv --output ../data/processed_data.csv


⚬ 결과: data/ 폴더에 정규화 및 특성 공학이 완료된 processed_data.csv가 생성됩니다.

[Module 2] 회수율 예측 모델 학습 및 XAI 분석

전처리된 데이터를 바탕으로 XGBoost 모델을 학습시키고, 성능 지표(RMSE, MAE) 및 SHAP 분석 결과를 출력합니다.

# module2 디렉토리에서 실행
python module2_prediction/train_predict.py --data ../data/processed_data.csv


⚬ 결과: 학습된 모델 가중치 파일(.pkl)이 저장되며, 변수 중요도를 나타내는 shap_summary_plot.png가 생성됩니다.

[Module 3] 다목적 공정 최적화 및 Unity API 서버 구동

목표 회수율 달성을 위한 최적 공정 조건을 탐색하고, 시각화 대시보드(Unity)와 통신할 WebSocket 서버를 엽니다.

# module3 디렉토리에서 실행
python module3_optimization/server.py --port 8000


⚬ 결과: 터미널에 WebSocket Server Started on ws://localhost:8000이 출력됩니다.
⚬ 통신 연동: 이후 Unity 프로젝트를 실행하면 Python 서버로 목표 수율을 요청(Request)하고, 서버는 최적 공정 레시피(황산 투입량, 반응 온도 등)를 JSON 형태로 반환(Response)하여 3D 가상 공장의 교반기 애니메이션 및 패널 UI를 업데이트합니다.

📝 통합 분석 보고서

상세한 데이터 탐색(EDA) 과정, 각 모델별 하이퍼파라미터 튜닝 근거, 시스템 기대효과 등의 심층적인 내용은 docs/REPORT.md (통합 분석 보고서)에서 확인할 수 있습니다.
