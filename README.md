# DTyoungpoong: 폐배터리 습식 제련 공정 최적화를 위한 AI 기반 디지털 트윈 시스템

한림대학교 SW중심대학사업 2026학년도 2학기 소프트웨어캡스톤디자인 프로젝트

- **팀명:** 박치기공룡
- **팀대표:** 김병진 (콘텐츠IT)
- **팀원:** 남기원 (스마트IOT), 김용준 (콘텐츠IT)
- **지도교수:** 허종욱 교수님
- **프로젝트 원격 저장소:** [https://github.com/kky7949/DTyoungpoong](https://github.com/kky7949/DTyoungpoong)

---

## 1. 프로젝트 개요

폐배터리 리튬이온 배터리 재활용 공정 중 황산을 활용한 습식 제련(Hydrometallurgy)은 95% 이상의 높은 핵심 금속(니켈, 코발트 등) 회수율을 달성할 수 있는 친환경 공정입니다. 그러나 투입되는 원료(블랙파우더)의 성분이 매번 달라져 기존 숙련공의 경험적 제어만으로는 품질과 수율을 일정하게 유지하기 어렵습니다.

본 프로젝트는 다음과 같은 솔루션을 제공합니다:
1. **도메인 지식 기반 데이터 전처리:** 화학 반응 속도론(축소 코어 모델)과 물질 수지를 보존하는 통계적 대치 기법 적용
2. **XAI 기반 고정밀 회수율 예측:** 앙상블 회귀 모델(XGBoost, LightGBM, Random Forest) 및 SHAP 기반 공정 인자 해석
3. **다목적 공정 레시피 최적화:** 니켈/코발트 회수율 극대화 및 약품/에너지 절감을 동시에 달성하는 파레토 최적해 도출
4. **3D 디지털 트윈 가상 공장:** ISO 23247 표준을 고려한 3D Unity 시뮬레이션 및 실시간 제어 대시보드 연동

---

## 2. 디렉토리 구조

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
│   ├── objectives.py           # 다목적 최적화 함수 정의
│   ├── constraints.py          # 화학/물리적 공정 제약조건
│   └── optimizer.py            # Grid Search & 메타휴리스틱 최적화 알고리즘
├── notebooks/                  # EDA 및 단계별 검증 Jupyter Notebooks
├── docs/                       # 프로젝트 보고서 및 아키텍처 문서
│   └── REPORT.md               # 캡스톤 최종/통합 기술 보고서
├── requirements.txt            # 의존성 패키지 목록
└── README.md                   # 프로젝트 안내 문서
```

---

## 3. 시작하기

### 3.1 환경 설정
```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # macOS / Linux

# 패키지 설치
pip install -r requirements.txt
```

### 3.2 실행 예시
```bash
# 1. 데이터 전처리 파이프라인 실행
python -m module1_preprocessing.pipeline

# 2. 회수율 예측 모델 학습 및 평가
python -m module2_prediction.models

# 3. 최적 공정 레시피 도출
python -m module3_optimization.optimizer
```
