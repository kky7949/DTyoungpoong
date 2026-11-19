from typing import Protocol

from app.schemas.process import AnalyzeRequest, AnalyzeResponse


class AnalysisProvider(Protocol):
    def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        """요청에 해당하는 예측 또는 추천 결과를 반환한다."""
        ...
