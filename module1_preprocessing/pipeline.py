"""
Module 1: Preprocessing Pipeline Execution
"""

import sys
from pathlib import Path
import pandas as pd
from .cleaner import DataCleaner
from .features import FeatureEngineer


def run_pipeline(input_path: str, output_path: str):
    print(f"[Module 1] Starting preprocessing on: {input_path}")
    path = Path(input_path)
    if not path.exists():
        print(f"[Module 1] Warning: Input file '{input_path}' not found. Please place raw datasets in data/raw/")
        return

    df = pd.read_csv(input_path) if input_path.endswith('.csv') else pd.read_excel(input_path)
    cleaner = DataCleaner()
    engineer = FeatureEngineer()

    # 1. 표준화 및 정제
    df_clean = cleaner.standardize_column_names(df)
    # 2. 파생 변수 생성
    df_feat = engineer.add_domain_features(df_clean)

    # 3. 저장
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df_feat.to_csv(output_path, index=False)
    print(f"[Module 1] Preprocessing complete. Saved to: {output_path}")


if __name__ == "__main__":
    run_pipeline("data/raw/sample_leaching.csv", "data/processed/clean_leaching.csv")
