"""
Module 3: Recipe Optimizer
- Grid Search 및 다목적 최적화 탐색
"""

import numpy as np
import pandas as pd
from typing import List, Dict
from .objectives import OptimizationObjective
from .constraints import ProcessConstraints


class RecipeOptimizer:
    def __init__(self, objective: OptimizationObjective, constraints: ProcessConstraints = None):
        self.objective = objective
        self.constraints = constraints or ProcessConstraints()

    def grid_search_best_recipe(
        self,
        base_raw_material: dict,
        temp_range: np.ndarray = np.linspace(60, 90, 7),
        acid_range: np.ndarray = np.linspace(300, 800, 11),
        time_range: np.ndarray = np.linspace(2, 5, 4)
    ) -> List[Dict]:
        """
        주어진 원료 성분 하에서 최적의 온도, 산 투입량, 침출 시간 조합 탐색
        """
        valid_candidates = []

        for temp in temp_range:
            for acid in acid_range:
                for t in time_range:
                    candidate = base_raw_material.copy()
                    candidate["temperature"] = float(temp)
                    candidate["acid_volume"] = float(acid)
                    candidate["leaching_time"] = float(t)

                    if not self.constraints.is_valid(candidate):
                        continue

                    eval_res = self.objective.evaluate_recipe(candidate)
                    if eval_res["meets_ni_target"] and eval_res["meets_co_target"]:
                        res_entry = {**candidate, **eval_res}
                        valid_candidates.append(res_entry)

        # 산 투입량(비용)이 적고 회수율이 높은 순으로 정렬
        sorted_candidates = sorted(
            valid_candidates,
            key=lambda x: (-x["predicted_ni_recovery"], x["acid_volume"])
        )
        return sorted_candidates
