from datetime import datetime, timezone
from math import isfinite
from typing import Literal
from uuid import uuid4

import httpx
from pydantic import BaseModel, ValidationError

from app.schemas.common import FIELD_LABELS, AnalysisAdapterError, ErrorDetail
from app.schemas.process import AnalyzeRequest, AnalyzeResponse, Recommendation, RecoveryPrediction


COMPOSITION_RANGES = {
    "ni_content_pct": (8, 30), "co_content_pct": (2, 15), "li_content_pct": (2, 6),
    "mn_content_pct": (5, 16), "cu_content_pct": (0.3, 6), "fe_content_pct": (0.2, 6),
    "al_content_pct": (0.5, 7),
}
PROCESS_RANGES = {
    "sulfuric_acid_l": (400, 1500), "leaching_temperature_c": (40, 95),
    "leaching_time_hr": (1, 8),
}


class AResult(BaseModel):
    source: Literal["live"]
    model_version: str


class APrediction(AResult):
    status: Literal["PREDICTED", "PREDICTION_UNUSABLE"]
    prediction: RecoveryPrediction | None
    warnings: list[str]


class ARecommendation(AResult):
    status: Literal["RECOMMENDED_ON_PREDICTION", "NO_VALID_MODEL_OUTPUT", "NO_SUPPORTED_CANDIDATE",
                    "TARGET_FOUND_BUT_UNSUPPORTED", "TARGET_NOT_FOUND_IN_GRID"]
    mode: Literal["joint", "ni", "co"]
    current_prediction: None
    recommendation: Recommendation | None
    closest_alternative: Recommendation | None


def checked_input(request: AnalyzeRequest) -> tuple[bool, dict]:
    payload = request.model_dump(mode="json", exclude_none=True)
    process = request.current_process
    recommend = all(getattr(process, field) is None for field in PROCESS_RANGES)
    details = []
    rules = [
        ("material", request.material, COMPOSITION_RANGES),
        ("current_process", process, {"feed_amount_kg": (80, 200), **({} if recommend else PROCESS_RANGES)}),
    ]
    for section, values, ranges in rules:
        for field, (minimum, maximum) in ranges.items():
            value = getattr(values, field)
            path = f"{section}.{field}"
            label = FIELD_LABELS[path]
            if value is None:
                details.append(ErrorDetail(field=path, message=f"{label} 값을 입력해 주세요."))
            elif not isfinite(value) or not minimum <= value <= maximum:
                details.append(ErrorDetail(field=path, message=f"{label}은 {minimum:g}~{maximum:g} 범위여야 합니다."))
    if not details and sum(getattr(request.material, field) for field in COMPOSITION_RANGES) > 100:
        details.append(ErrorDetail(field="material", message="원료 성분의 합계는 100% 이하여야 합니다."))
    if not recommend and request.options is not None:
        details.append(ErrorDetail(field="options", message="추천 목표는 원료 기준 추천에서만 선택할 수 있습니다."))
    if details:
        raise AnalysisAdapterError(422, "A_INVALID_INPUT", "A 모델의 필수값과 지원 범위를 확인해 주세요.", details)
    return recommend, payload


class HttpAnalysisProvider:
    def __init__(self, base_url: str, transport: httpx.BaseTransport | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.transport = transport

    def _client(self, timeout: float) -> httpx.Client:
        return httpx.Client(base_url=self.base_url, transport=self.transport, timeout=timeout, trust_env=False)

    def ready(self) -> bool:
        try:
            with self._client(1.0) as client:
                response = client.get("/health")
                payload = response.json()
                return response.status_code == 200 and isinstance(payload, dict) and payload.get("model_ready") is True
        except (httpx.HTTPError, ValueError):
            return False

    def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        recommend, payload = checked_input(request)
        path = "/api/v1/recommend" if recommend else "/api/v1/predict"
        try:
            with self._client(3.0) as client:
                response = client.post(path, json=payload)
        except httpx.TimeoutException as exc:
            raise AnalysisAdapterError(504, "A_TIMEOUT", "A 서버의 응답 시간이 초과됐습니다.") from exc
        except (httpx.RequestError, ValueError) as exc:
            raise AnalysisAdapterError(502, "A_UNREACHABLE", "A 서버에 연결할 수 없습니다.") from exc

        if response.status_code == 503:
            raise AnalysisAdapterError(503, "A_NOT_READY", "A 서버의 모델을 사용할 수 없습니다.")
        if response.status_code == 422:
            try:
                raw_details = response.json()["error"]["details"]
                details = [ErrorDetail(field=item["field"],
                           message=f"{FIELD_LABELS.get(item['field'], '입력값')}의 형식 또는 범위를 확인해 주세요.")
                           for item in raw_details]
            except (ValueError, KeyError, TypeError):
                details = []
            raise AnalysisAdapterError(422, "A_INVALID_INPUT", "A 모델이 입력값을 처리할 수 없습니다.", details)
        if response.status_code != 200:
            message = "A 서버에서 공정 추천에 실패했습니다." if recommend else "A 서버에서 회수율 예측에 실패했습니다."
            raise AnalysisAdapterError(502, "A_CALCULATION_FAILED", message)

        # A의 두 응답을 HMI의 통합 분석 응답으로 옮긴다.
        try:
            result = (ARecommendation if recommend else APrediction).model_validate_json(response.content)
        except ValidationError as exc:
            raise AnalysisAdapterError(502, "A_INVALID_RESPONSE", "A 서버 응답 형식이 올바르지 않습니다.") from exc

        return AnalyzeResponse(
            schema_version="draft-1", source=result.source, model_version=result.model_version,
            request_id=str(uuid4()), generated_at=datetime.now(timezone.utc), status=result.status,
            current_prediction=result.prediction if isinstance(result, APrediction) and result.status == "PREDICTED" else None,
            recommendation=result.recommendation if isinstance(result, ARecommendation) and result.status == "RECOMMENDED_ON_PREDICTION" else None,
            mode=result.mode if isinstance(result, ARecommendation) else None,
            closest_alternative=result.closest_alternative if isinstance(result, ARecommendation) else None,
            warnings=result.warnings if isinstance(result, APrediction) else [],
        )
