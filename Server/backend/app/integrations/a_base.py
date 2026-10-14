from typing import Protocol

from app.schemas.process import AnalyzeRequest, AnalyzeResponse


class AnalysisProvider(Protocol):
    def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        """현재 조건의 예측과 추천 결과를 반환한다."""
        ...
