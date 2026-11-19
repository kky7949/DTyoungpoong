import json

import httpx
import pytest

from app.api.process import get_analysis_provider
from app.integrations.a_http import HttpAnalysisProvider
from app.main import app


MATERIAL = dict(ni_content_pct=12.17, co_content_pct=6.98, li_content_pct=4.25,
                mn_content_pct=10.49, cu_content_pct=1.9, fe_content_pct=2.04,
                al_content_pct=3.43)
CONDITIONS = dict(sulfuric_acid_l=1118, leaching_temperature_c=55.6, leaching_time_hr=6.32)
RECOVERY = dict(ni_recovery_pct=84.924, co_recovery_pct=76.754)


@pytest.fixture
def a_response():
    return {"source": "live", "model_version": "test-model"}


@pytest.fixture
def client_for():
    def factory(handler):
        provider = HttpAnalysisProvider("http://a.test:8001", transport=httpx.MockTransport(handler))
        app.dependency_overrides[get_analysis_provider] = lambda: provider
        return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://b.test")
    yield factory
    app.dependency_overrides.pop(get_analysis_provider, None)


@pytest.mark.anyio
async def test_live_prediction_calls_a_and_returns_only_prediction(client_for, a_response):
    def handler(request):
        assert request.url.path == "/api/v1/predict"
        assert json.loads(request.content)["current_process"] == {"feed_amount_kg": 159.1, **CONDITIONS}
        return httpx.Response(200, json={**a_response, "status": "PREDICTED", "prediction": RECOVERY, "warnings": []})

    async with client_for(handler) as client:
        result = await client.post("/api/v1/process/analyze", json={
            "material": MATERIAL, "current_process": {"feed_amount_kg": 159.1, **CONDITIONS}})
    assert result.status_code == 200
    assert result.json()["current_prediction"] == RECOVERY
    assert result.json()["recommendation"] is None
    assert result.json()["source"] == "live"


@pytest.mark.anyio
async def test_live_recommendation_preserves_target_miss_and_alternative(client_for, a_response):
    candidate = {"process_conditions": CONDITIONS, "expected_recovery": RECOVERY}

    def handler(request):
        assert request.url.path == "/api/v1/recommend"
        sent = json.loads(request.content)
        assert sent["options"] == {"mode": "joint"}
        assert sent["current_process"] == {"feed_amount_kg": 159.1}
        return httpx.Response(200, json={**a_response, "status": "TARGET_NOT_FOUND_IN_GRID", "mode": "joint",
                                         "current_prediction": None, "recommendation": None,
                                         "closest_alternative": candidate})

    async with client_for(handler) as client:
        result = await client.post("/api/v1/process/analyze", json={
            "material": MATERIAL, "current_process": {"feed_amount_kg": 159.1},
            "options": {"mode": "joint"}})
    assert result.status_code == 200
    body = result.json()
    assert body["recommendation"] is body["current_prediction"] is None
    assert body["closest_alternative"] == candidate
    assert body["status"] == "TARGET_NOT_FOUND_IN_GRID"


@pytest.mark.anyio
async def test_live_missing_material_and_out_of_range_feed_return_field_errors(client_for):
    def handler(request):
        pytest.fail("invalid inputs must be rejected before calling A")

    async with client_for(handler) as client:
        result = await client.post("/api/v1/process/analyze", json={
            "material": {**MATERIAL, "ni_content_pct": None}, "current_process": {"feed_amount_kg": 1000}})
    assert result.status_code == 422
    assert {detail["field"] for detail in result.json()["error"]["details"]} == {
        "material.ni_content_pct", "current_process.feed_amount_kg"}


@pytest.mark.anyio
async def test_a_timeout_preserves_failure_instead_of_using_mock(client_for):
    def handler(request):
        raise httpx.ReadTimeout("timeout", request=request)

    async with client_for(handler) as client:
        result = await client.post("/api/v1/process/analyze", json={
            "material": MATERIAL, "current_process": {"feed_amount_kg": 159.1}})
    assert result.status_code == 504
    assert result.json()["error"]["code"] == "A_TIMEOUT"
