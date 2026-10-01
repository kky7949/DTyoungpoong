# DTyoungpoong: 폐배터리 습식 제련 공정 최적화를 위한 AI 기반 디지털 트윈 시스템 🏭♻️

한림대학교 SW중심대학사업 2026학년도 2학기 소프트웨어캡스톤디자인 프로젝트

- **팀명:** 박치기공룡
- **팀대표:** 김병진 (콘텐츠IT)
- **팀원:** 남기원 (스마트IOT), 김용준 (콘텐츠IT)
- **지도교수:** 허종욱 교수님
- **프로젝트 원격 저장소:** [https://github.com/kky7949/DTyoungpoong](https://github.com/kky7949/DTyoungpoong)

---

## 1. 프로젝트 개요

전기차 폐배터리 블랙파우더(Black Powder)의 습식 제련 공정에서 핵심 금속(니켈, 코발트 등)의 회수율을 극대화하기 위한 **'AI 최적 공정 레시피 추천 및 3D 가상 공장(Digital Twin) 시각화 시스템'**입니다.

본 프로젝트는 불균일한 원료 성분 데이터를 기반으로 머신러닝 예측 모델을 구축하고, 다목적 최적화 알고리즘을 통해 도출된 최적의 산(Acid) 투입량 및 반응 온도 레시피를 Unity 3D 기반 가상 공장 및 대시보드에 실시간으로 연동합니다.

### 🏗 시스템 아키텍처 및 핵심 기술
1. **[Module 1] 데이터 전처리 (Data Preprocessing):** 화학 반응 속도론(축소 코어 모델) 기반 파생 변수 생성 및 물질 수지를 보존하는 KNN 결측치 정제
2. **[Module 2] 회수율 예측 모델링 (AI Prediction & XAI):** XGBoost/LightGBM/Random Forest 기반 회수율 예측 및 SHAP(SHapley Additive exPlanations)을 이용한 변수 중요도 시각화
3. **[Module 3] 공정 최적화 및 시스템 연동 (Optimization & Digital Twin):** 다목적 최적화 알고리즘(NSGA-II, Grid Search)을 활용한 파레토 최적해 탐색, WebSocket API를 통한 Unity 3D 실시간 제어(ISO 23247 표준 지향)

---

## 2. 레포지토리 구조

```text
DTyoungpoong/
├── data/                       # 데이터 디렉토리 (원본 및 전처리 데이터)
│   ├── raw/                    # 원본 랩실 데이터 (보안/용량상 git 제외)
│   └── processed/              # 정제 및 특성공학 완료 데이터
├── module1_preprocessing/      # [Module 1] 데이터 정제 및 특성공학 파이프라인
│   ├── cleaner.py              # 결측치/이상치 처리 및 물질수지 검증
│   ├── features.py             # 축소 코어 모델 기반 파생변수 생성
│   └── pipeline.py             # 엔드투엔드 전처리 실행기
├── module2_prediction/         # [Module 2] 회수율 예측 모델링 및 XAI
│   ├── models.py               # 회귀 모델 정의 및 학습 래퍼
│   ├── evaluate.py             # 정량적 평가 (RMSE, MAE, R²) 및 과적합 진단
│   └── xai.py                  # SHAP 기반 변수 기여도 시각화
├── module3_optimization/       # [Module 3] 최적 공정 레시피 추천 시스템
│   ├── objectives.py           # 다목적 최적화 목적 함수
│   ├── constraints.py          # 화학/물리적 공정 제약조건
│   └── optimizer.py            # Grid Search & 메타휴리스틱 최적화 알고리즘
├── notebooks/                  # 데이터 분석(EDA) 및 모델링 실험용 Jupyter Notebook
├── docs/                       # 기획서 및 통합 분석 보고서
│   └── REPORT.md               # 캡스톤 최종/통합 기술 보고서
├── requirements.txt            # 의존성 패키지 목록
└── README.md                   # 프로젝트 개요 및 가이드 (본 문서)
```

---

## 3. 데이터셋 설명 및 보안 유의사항

- **데이터 소스:** 폐배터리 블랙파우더 성분 분석 랩실 데이터 (니켈, 코발트 함량, 불순물 수치, 공정 온도, 시간, 산 투입량 등)
- **보안 유의사항:**
  - 본 레포지토리의 `data/` 폴더에 포함되는 원본 데이터는 기업 보안 및 개인정보 보호를 위해 비식별화/익명화 처리된 샘플 데이터셋을 사용합니다.
  - 대용량 원본 파일(`.csv`, `.xlsx`, `.zip`)은 `.gitignore`에 의해 원격 저장소 커밋에서 제외됩니다.

---

## 4. 환경 설정 및 설치

### 4.1 Python 백엔드 환경 (AI 연산)
- **권장 환경:** Python 3.9+
```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # macOS / Linux

# 필수 라이브러리 설치
pip install -r requirements.txt
```

### 4.2 프론트엔드 환경 (3D 시각화)
- **엔진:** Unity Editor 2022.3 LTS 이상
- **에셋 및 플러그인:** glTFUtility (3D 에셋 임포트용), WebGL 빌드 모듈, Youngpoong 에셋 패키지

---

## 5. 모듈별 실행 방법

```bash
# 1. 데이터 전처리 파이프라인 실행
python -m module1_preprocessing.pipeline

# 2. 회수율 예측 모델 학습 및 평가
python -m module2_prediction.models

# 3. 최적 공정 레시피 도출
python -m module3_optimization.optimizer
```

---

## 6. 통합 분석 보고서
상세한 데이터 탐색(EDA) 과정, 모델별 하이퍼파라미터 튜닝 근거, 시스템 기대효과 등의 심층적인 내용은 [docs/REPORT.md](docs/REPORT.md)에서 확인할 수 있습니다.
