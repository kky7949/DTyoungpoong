from typing import NotRequired, TypedDict

from fastapi import APIRouter, Depends

from app.api.process import get_analysis_provider
from app.integrations.a_base import AnalysisProvider
from app.integrations.a_http import HttpAnalysisProvider

router = APIRouter(prefix="/api/v1", tags=["system"])


class Capabilities(TypedDict):
    prediction: bool
    optimization: bool
    xai: bool
    unity_control: bool


class SystemStatus(TypedDict):
    backend: str
    a_adapter: str
    a_ready: NotRequired[bool]
    c_adapter: str
    capabilities: Capabilities


@router.get("/system/status")
def get_system_status(provider: AnalysisProvider = Depends(get_analysis_provider)) -> SystemStatus:
    live = isinstance(provider, HttpAnalysisProvider)
    result: SystemStatus = {
        "backend": "ok",
        "a_adapter": "live" if live else "mock",
        "c_adapter": "mock",
        "capabilities": {
            "prediction": True,
            "optimization": True,
            "xai": False,
            "unity_control": True,
        },
    }
    if live:
        result["a_ready"] = provider.ready()
    return result
