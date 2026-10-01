# Data Directory Guide

- `raw/`: 영풍도시광산 제공 랩실 원본 데이터 및 합성 공정 데이터 (`.csv`, `.xlsx`).
  - 보안 및 대용량 파일 관리를 위해 원본 데이터 파일은 `.gitignore`에 의해 Git 추적에서 제외됩니다.
- `processed/`: 결측치 대치 및 축소 코어 모델 기반 특성공학이 완료된 학습용 정제 데이터.
