"""
Module 3: Objective Functions
- 니켈/코발트 회수율 최대화 및 약품/에너지 비용 최소화
"""

class OptimizationObjective:
    def __init__(self, ni_model, co_model=None, target_ni_recovery: float = 95.0, target_co_recovery: float = 90.0):
        self.ni_model = ni_model
        self.co_model = co_model
        self.target_ni = target_ni_recovery
        self.target_co = target_co_recovery

    def evaluate_recipe(self, features_dict: dict) -> dict:
        """
        단일 레시피에 대한 예상 회수율 및 목표 달성 여부 산출
        """
        import pandas as pd
        input_df = pd.DataFrame([features_dict])
        pred_ni = float(self.ni_model.predict(input_df)[0])
        pred_co = float(self.co_model.predict(input_df)[0]) if self.co_model else None

        return {
            "predicted_ni_recovery": pred_ni,
            "predicted_co_recovery": pred_co,
            "meets_ni_target": pred_ni >= self.target_ni,
            "meets_co_target": (pred_co >= self.target_co) if pred_co is not None else True
        }
