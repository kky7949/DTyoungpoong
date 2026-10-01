"""
Module 2: Prediction Models
- Random Forest, XGBoost, LightGBM 앙상블 회귀 모델
"""

from typing import Dict, Any
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor


class RecoveryPredictor:
    def __init__(self, model_type: str = "xgboost", params: Dict[str, Any] = None):
        self.model_type = model_type.lower()
        self.params = params or {}
        self.model = self._init_model()

    def _init_model(self):
        if self.model_type == "random_forest":
            return RandomForestRegressor(
                n_estimators=self.params.get("n_estimators", 100),
                max_depth=self.params.get("max_depth", 10),
                random_state=42
            )
        elif self.model_type == "xgboost":
            return XGBRegressor(
                n_estimators=self.params.get("n_estimators", 150),
                max_depth=self.params.get("max_depth", 6),
                learning_rate=self.params.get("learning_rate", 0.05),
                random_state=42
            )
        elif self.model_type == "lightgbm":
            return LGBMRegressor(
                n_estimators=self.params.get("n_estimators", 150),
                max_depth=self.params.get("max_depth", 6),
                learning_rate=self.params.get("learning_rate", 0.05),
                random_state=42
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict(self, X):
        return self.model.predict(X)
