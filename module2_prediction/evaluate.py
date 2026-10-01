"""
Module 2: Model Evaluation
- RMSE, MAE, R-squared 계산
- 일반화 성능 및 과적합 평가
"""

import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


def evaluate_regression(y_true, y_pred, prefix: str = "Test") -> dict:
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)

    metrics = {
        f"{prefix}_RMSE": float(rmse),
        f"{prefix}_MAE": float(mae),
        f"{prefix}_R2": float(r2)
    }

    print(f"[{prefix} Evaluation]")
    print(f"  - RMSE: {rmse:.4f}")
    print(f"  - MAE : {mae:.4f}")
    print(f"  - R²  : {r2:.4f}")

    return metrics
