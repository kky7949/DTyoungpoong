from app.integrations.a_base import AnalysisProvider
from app.schemas.common import AnalysisAdapterError
from app.schemas.process import AnalyzeRequest, AnalyzeResponse


class ProcessCoordinator:
    def __init__(self, provider: AnalysisProvider) -> None:
        self.provider = provider

    def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        try:
            return self.provider.analyze(request)
        except Exception as exc:
            raise AnalysisAdapterError from exc
