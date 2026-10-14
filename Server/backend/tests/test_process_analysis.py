from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.process import get_analysis_provider
from app.main import app
from app.schemas.process import AnalyzeRequest


VALID_REQUEST: dict[str, Any] = {
    "material": {
        "grade": "B",
        "ni_content_pct": 12.17,
        "co_content_pct": 6.98,
    },
    "current_process": {
        "feed_amount_kg": 159.1,
        "sulfuric_acid_l": 1118.0,
        "leaching_temperature_c": 55.6,
        "leaching_time_hr": 6.32,
    },
}


async def post_analysis(payload: dict[str, Any]):
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as client:
        return await client.post("/api/v1/process/analyze", json=payload)


def analysis_response_payload() -> dict[str, Any]:
    return {
        "schema_version": "draft-1",
        "source": "mock",
        "generated_at": "2026-10-14T21:00:00+09:00",
        "request_id": "test-request-id",
        "current_prediction": {
            "ni_recovery_pct": 85.65,
            "co_recovery_pct": 78.45,
        },
        "recommendation": {
            "process_conditions": {
                "sulfuric_acid_l": 1050.0,
                "leaching_temperature_c": 62.0,
                "leaching_time_hr": 5.5,
            },
            "expected_recovery": {
                "ni_recovery_pct": 89.2,
                "co_recovery_pct": 82.1,
            },
        },
    }


@pytest.mark.anyio
async def test_analysis_returns_labeled_mock_result_without_xai() -> None:
    """모의 결과가 실제 AI 또는 XAI 결과처럼 표시되면 실패한다."""
    response = await post_analysis(VALID_REQUEST)

    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "draft-1"
    assert body["source"] == "mock"
    assert body["current_prediction"] == {
        "ni_recovery_pct": 85.65,
        "co_recovery_pct": 78.45,
    }
    assert body["recommendation"]["expected_recovery"] == {
        "ni_recovery_pct": 89.2,
        "co_recovery_pct": 82.1,
    }
    assert "xai" not in body


class CapturingProvider:
    def __init__(self) -> None:
        self.request: AnalyzeRequest | None = None

    def analyze(self, request: AnalyzeRequest) -> dict[str, Any]:
        self.request = request
        return analysis_response_payload()


@pytest.mark.anyio
async def test_analysis_passes_null_content_to_provider_without_imputation() -> None:
    """B가 결측값을 0이나 평균값으로 바꾸면 실패한다."""
    provider = CapturingProvider()
    app.dependency_overrides[get_analysis_provider] = lambda: provider
    payload = {
        **VALID_REQUEST,
        "material": {**VALID_REQUEST["material"], "ni_content_pct": None},
    }

    try:
        response = await post_analysis(payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert provider.request is not None
    assert provider.request.material.ni_content_pct is None


@pytest.mark.anyio
async def test_analysis_rejects_content_above_one_hundred_in_korean() -> None:
    """백분율 상한 검증이 사라지거나 영어 오류만 노출되면 실패한다."""
    payload = {
        **VALID_REQUEST,
        "material": {**VALID_REQUEST["material"], "ni_content_pct": 101},
    }

    response = await post_analysis(payload)

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "입력값을 확인해 주세요."
    assert body["error"]["details"] == [
        {
            "field": "material.ni_content_pct",
            "message": "원료 내 니켈 함량(%)은 0~100 범위여야 합니다.",
        }
    ]
    assert body["request_id"]


class FailingProvider:
    def analyze(self, request: AnalyzeRequest) -> dict[str, Any]:
        raise RuntimeError("A service unavailable")


@pytest.mark.anyio
async def test_analysis_converts_provider_failure_to_structured_502() -> None:
    """A 내부 예외가 그대로 노출되거나 B의 500으로 뭉개지면 실패한다."""
    app.dependency_overrides[get_analysis_provider] = lambda: FailingProvider()

    try:
        response = await post_analysis(VALID_REQUEST)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    body = response.json()
    assert body["error"] == {
        "code": "A_ADAPTER_ERROR",
        "message": "예측 및 최적화 처리에 실패했습니다.",
        "details": [],
    }
    assert body["request_id"]
    assert "A service unavailable" not in response.text
