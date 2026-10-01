"""
Module 2: Explainable AI (SHAP)
- 변수 중요도 및 의사결정 기여도 산출
"""

import shap
import matplotlib.pyplot as plt


class ExplainableAI:
    def __init__(self, model, X_train):
        self.model = model
        self.X_train = X_train
        # 트리 기반 앙상블 모델 전용 TreeExplainer
        self.explainer = shap.TreeExplainer(model)

    def compute_shap_values(self, X):
        return self.explainer.shap_values(X)

    def summary_plot(self, X, save_path: str = None):
        """글로벌 변수 중요도 플롯"""
        shap_values = self.compute_shap_values(X)
        plt.figure(figsize=(10, 6))
        shap.summary_plot(shap_values, X, show=False)
        if save_path:
            plt.savefig(save_path, bbox_inches='tight', dpi=300)
            plt.close()
            print(f"[XAI] Summary plot saved to {save_path}")
        else:
            plt.show()
