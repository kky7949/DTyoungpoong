import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_system_status_reports_mock_adapters() -> None:
    """실제 연동 전인데 A/C 또는 XAI를 활성 상태로 오인하면 실패한다."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/v1/system/status")

    assert response.status_code == 200
    assert response.json() == {
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
