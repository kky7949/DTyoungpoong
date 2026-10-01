"""
Module 3: Process Constraints
- 화학적, 물리적 한계 조건 (온도, 산 투입량, 반응 시간 등)
"""

class ProcessConstraints:
    def __init__(self):
        # 도메인 지식 기반 물리적 제약 조건
        self.bounds = {
            "temperature": (60.0, 90.0),       # ℃ (60도 미만 반응성 저하, 90도 초과 증발/비등 위험)
            "acid_volume": (100.0, 1000.0),    # L 또는 mL 단위 제약
            "leaching_time": (1.0, 6.0),       # 시간(h)
            "stirring_speed": (200.0, 500.0)   # RPM
        }

    def is_valid(self, recipe: dict) -> bool:
        """레시피 파라미터가 공정 허용 범위 내에 있는지 확인"""
        for param, (low, high) in self.bounds.items():
            if param in recipe:
                val = recipe[param]
                if val < low or val > high:
                    return False
        return True
