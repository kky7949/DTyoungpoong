from typing import Any
from uuid import uuid4

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    field: str
    message: str


class ErrorContent(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail]


class ErrorResponse(BaseModel):
    error: ErrorContent
    request_id: str


class AnalysisAdapterError(RuntimeError):
    """A 분석 어댑터 호출에 실패했음을 나타낸다."""


FIELD_LABELS = {
    "material.grade": "원료 등급",
    "material.ni_content_pct": "원료 내 니켈 함량(%)",
    "material.co_content_pct": "원료 내 코발트 함량(%)",
    "current_process.feed_amount_kg": "원료 투입량(kg)",
    "current_process.sulfuric_acid_l": "황산 투입량(L)",
    "current_process.leaching_temperature_c": "침출 온도(°C)",
    "current_process.leaching_time_hr": "침출 시간(시간)",
}


def _request_id(request: Request) -> str:
    return request.headers.get("X-Request-ID") or str(uuid4())


def _validation_detail(error: dict[str, Any]) -> ErrorDetail:
    field = ".".join(str(part) for part in error["loc"] if part != "body")
    label = FIELD_LABELS.get(field, field or "입력값")
    if error["type"] in {"greater_than_equal", "less_than_equal"} and field in {
        "material.ni_content_pct",
        "material.co_content_pct",
    }:
        message = f"{label}은 0~100 범위여야 합니다."
    else:
        message = f"{label} 값을 확인해 주세요."
    return ErrorDetail(field=field, message=message)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    response = ErrorResponse(
        error=ErrorContent(
            code="VALIDATION_ERROR",
            message="입력값을 확인해 주세요.",
            details=[_validation_detail(error) for error in exc.errors()],
        ),
        request_id=_request_id(request),
    )
    return JSONResponse(status_code=422, content=response.model_dump(mode="json"))


async def analysis_adapter_exception_handler(
    request: Request,
    exc: AnalysisAdapterError,
) -> JSONResponse:
    response = ErrorResponse(
        error=ErrorContent(
            code="A_ADAPTER_ERROR",
            message="예측 및 최적화 처리에 실패했습니다.",
            details=[],
        ),
        request_id=_request_id(request),
    )
    return JSONResponse(status_code=502, content=response.model_dump(mode="json"))
