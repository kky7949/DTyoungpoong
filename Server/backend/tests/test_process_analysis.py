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


ADDITIONAL_CONTENT_FIELDS = {
    "li_content_pct": ("리튬 함량", 4.25),
    "mn_content_pct": ("망간 함량", 10.49),
    "cu_content_pct": ("구리 불순물 함량", 1.9),
    "fe_content_pct": ("철 불순물 함량", 2.04),
    "al_content_pct": ("알루미늄 불순물 함량", 3.43),
}


@pytest.mark.anyio
async def test_recommendation_accepts_material_without_process_settings() -> None:
    provider = CapturingProvider()
    app.dependency_overrides[get_analysis_provider] = lambda: provider
    try:
        response = await post_analysis({
            "material": {"name": "원료 1", "ni_content_pct": 12.17, "co_content_pct": 6.98},
            "current_process": {
                "feed_amount_kg": 159.1,
                "sulfuric_acid_l": None,
                "leaching_temperature_c": None,
                "leaching_time_hr": None,
            },
        })
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["recommendation"]["process_conditions"]["sulfuric_acid_l"] == 1050
    assert provider.request is not None
    assert provider.request.current_process.feed_amount_kg == 159.1
    assert provider.request.current_process.sulfuric_acid_l is None
    assert provider.request.current_process.leaching_temperature_c is None
    assert provider.request.current_process.leaching_time_hr is None


@pytest.mark.anyio
async def test_analysis_passes_all_additional_contents_without_imputation() -> None:
    provider = CapturingProvider()
    app.dependency_overrides[get_analysis_provider] = lambda: provider
    contents = {field: value for field, (_, value) in ADDITIONAL_CONTENT_FIELDS.items()}
    try:
        for values in (
            contents,
            dict.fromkeys(contents),
            dict.fromkeys(contents, 0),
            dict.fromkeys(contents, 100),
            {},
        ):
            response = await post_analysis({
                **VALID_REQUEST,
                "material": {**VALID_REQUEST["material"], **values},
            })
            assert response.status_code == 200
            assert provider.request is not None
            for field in contents:
                assert getattr(provider.request.material, field) == values.get(field)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
@pytest.mark.parametrize("field", ADDITIONAL_CONTENT_FIELDS)
@pytest.mark.parametrize("value", [-0.01, 100.01])
async def test_analysis_rejects_invalid_additional_content_in_korean(field, value) -> None:
    response = await post_analysis({
        **VALID_REQUEST,
        "material": {**VALID_REQUEST["material"], field: value},
    })
    assert response.status_code == 422
    label = ADDITIONAL_CONTENT_FIELDS[field][0]
    assert response.json()["error"]["details"] == [{
        "field": f"material.{field}",
        "message": f"원료 내 {label}(%)은 0~100 범위여야 합니다.",
    }]


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
async def test_material_name_is_passed_without_treating_it_as_a_grade():
    provider = CapturingProvider()
    app.dependency_overrides[get_analysis_provider] = lambda: provider
    payload = {**VALID_REQUEST, "material": {
        "name": "원료 1", "ni_content_pct": 12.17, "co_content_pct": 6.98,
    }}
    try:
        response = await post_analysis(payload)
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert provider.request is not None
    assert provider.request.material.name == "원료 1"
    assert provider.request.material.grade is None
    assert response.json()["material_grade"] is None


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
