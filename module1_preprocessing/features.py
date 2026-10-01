"""
Module 1: Feature Engineering
- 축소 코어 모델(Shrinking Core Model) 기반 파생 변수
- 산-원료 투입비, 불순물 페널티 지수 등 도메인 변수 생성
"""

import pandas as pd
import numpy as np


class FeatureEngineer:
    def __init__(self):
        pass

    def add_domain_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """화학공학 도메인 지식 기반 파생 변수 생성"""
        feat_df = df.copy()

        # 1. 산-원료 투입비 (Acid-to-Solid Ratio)
        if 'acid_volume' in feat_df.columns and 'solid_mass' in feat_df.columns:
            feat_df['acid_to_solid_ratio'] = feat_df['acid_volume'] / (feat_df['solid_mass'] + 1e-6)

        # 2. 유효 니켈 대비 산 비율
        if 'acid_volume' in feat_df.columns and 'ni_content' in feat_df.columns and 'solid_mass' in feat_df.columns:
            theoretical_ni_mass = feat_df['solid_mass'] * (feat_df['ni_content'] / 100.0)
            feat_df['acid_to_ni_ratio'] = feat_df['acid_volume'] / (theoretical_ni_mass + 1e-6)

        # 3. 불순물 페널티 스코어 (부반응 유발 인자: Fe, Al 등)
        impurity_cols = [c for c in ['fe_content', 'al_content', 'cu_content'] if c in feat_df.columns]
        if impurity_cols:
            feat_df['impurity_penalty_score'] = feat_df[impurity_cols].sum(axis=1)

        # 4. 아레니우스 지수 근사 (온도 기반 반응 속도 인자)
        # k ~ exp(-Ea / (R * T))
        if 'temperature' in feat_df.columns:
            temp_kelvin = feat_df['temperature'] + 273.15
            # 가상 활성화 에너지 인자 기준
            feat_df['arrhenius_term'] = np.exp(-4000.0 / temp_kelvin)

        return feat_df
