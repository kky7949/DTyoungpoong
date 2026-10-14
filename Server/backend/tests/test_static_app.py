from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@pytest.mark.anyio
@pytest.mark.skipif(not FRONTEND_DIST.exists(), reason="프런트 빌드가 없으면 API 전용으로 실행")
async def test_built_frontend_and_api_are_served_together() -> None:
    """프로덕션 빌드와 API가 같은 FastAPI 주소에서 함께 제공된다."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        page_response = await client.get("/")
        health_response = await client.get("/health")
        status_response = await client.get("/api/v1/system/status")

    assert page_response.status_code == 200
    assert "text/html" in page_response.headers["content-type"]
    assert '<div id="root"></div>' in page_response.text
    assert health_response.status_code == 200
    assert status_response.status_code == 200
