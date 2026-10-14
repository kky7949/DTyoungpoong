from typing import TypedDict

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["system"])


class Capabilities(TypedDict):
    prediction: bool
    optimization: bool
    xai: bool
    unity_control: bool


class SystemStatus(TypedDict):
    backend: str
    a_adapter: str
    c_adapter: str
    capabilities: Capabilities


@router.get("/system/status")
def get_system_status() -> SystemStatus:
    """B와 아직 연결되지 않은 A/C 기능 상태를 반환한다."""
    return {
        "backend": "ok",
        "a_adapter": "mock",
        "c_adapter": "mock",
        "capabilities": {
            "prediction": True,
            "optimization": True,
            "xai": False,
            "unity_control": True,
        },
    }
