"""
Module 1: Data Cleaner
- 결측치(Missing Values) 처리 및 물질 수지(Mass Balance) 왜곡 방지
- 통계적 기법(KNN Imputation) 및 이상치 필터링
"""

import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer


class DataCleaner:
    def __init__(self, n_neighbors: int = 5):
        self.n_neighbors = n_neighbors
        self.imputer = KNNImputer(n_neighbors=n_neighbors)

    def standardize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """컬럼명 공백 제거 및 소문자/표준 표기 변환"""
        clean_df = df.copy()
        clean_df.columns = [c.strip().replace(" ", "_").lower() for c in clean_df.columns]
        return clean_df

    def handle_missing_values(self, df: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
        """
        KNN 기반 결측치 대치:
        단순 평균 대치는 원료 성분 비율의 총합(물질 수지)을 왜곡하므로
        유사한 성분 프로파일을 가진 배치의 수치를 참조하여 대치합니다.
        """
        clean_df = df.copy()
        clean_df[feature_cols] = self.imputer.fit_transform(clean_df[feature_cols])
        return clean_df

    def validate_mass_balance(self, df: pd.DataFrame, composition_cols: list, tolerance: float = 5.0) -> pd.DataFrame:
        """
        원료 성분 총합이 100% 인근(100 +/- tolerance)인지 검증하고 벗어나는 이상치를 플래깅
        """
        clean_df = df.copy()
        total_comp = clean_df[composition_cols].sum(axis=1)
        clean_df['mass_balance_error'] = np.abs(total_comp - 100.0)
        clean_df['is_valid_mass_balance'] = clean_df['mass_balance_error'] <= tolerance
        return clean_df
