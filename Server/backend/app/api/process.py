import os

from fastapi import APIRouter, Depends

from app.integrations.a_base import AnalysisProvider
from app.integrations.a_http import HttpAnalysisProvider
from app.integrations.a_mock import MockAnalysisProvider
from app.schemas.process import AnalyzeRequest, AnalyzeResponse
from app.services.process_coordinator import ProcessCoordinator

router = APIRouter(prefix="/api/v1/process", tags=["process"])
_mock_provider = MockAnalysisProvider()


def get_analysis_provider() -> AnalysisProvider:
    if os.environ.get("A_ADAPTER", "mock").lower() == "live":
        return HttpAnalysisProvider(os.environ.get("A_API_BASE_URL", ""))
    return _mock_provider


def get_process_coordinator(
    provider: AnalysisProvider = Depends(get_analysis_provider),
) -> ProcessCoordinator:
    return ProcessCoordinator(provider)


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_process(
    request: AnalyzeRequest,
    coordinator: ProcessCoordinator = Depends(get_process_coordinator),
) -> AnalyzeResponse:
    return coordinator.analyze(request)
