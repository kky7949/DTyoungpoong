from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MaterialInput(BaseModel):
    grade: str | None = Field(default=None, description="원료 등급")
    ni_content_pct: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="원료 내 니켈 함량(%)",
    )
    co_content_pct: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="원료 내 코발트 함량(%)",
    )


class ProcessConditions(BaseModel):
    feed_amount_kg: float | None = Field(
        default=None,
        ge=0,
        description="원료 투입량(kg)",
    )
    sulfuric_acid_l: float | None = Field(
        default=None,
        ge=0,
        description="황산 투입량(L)",
    )
    leaching_temperature_c: float | None = Field(
        default=None,
        description="침출 온도(°C)",
    )
    leaching_time_hr: float | None = Field(
        default=None,
        ge=0,
        description="침출 시간(시간)",
    )


class AnalyzeRequest(BaseModel):
    material: MaterialInput
    current_process: ProcessConditions


class RecoveryPrediction(BaseModel):
    ni_recovery_pct: float = Field(ge=0, le=100, description="니켈 회수율 예측값(%)")
    co_recovery_pct: float = Field(ge=0, le=100, description="코발트 회수율 예측값(%)")


class RecommendedProcessConditions(BaseModel):
    sulfuric_acid_l: float = Field(ge=0, description="추천 황산 투입량(L)")
    leaching_temperature_c: float = Field(description="추천 침출 온도(°C)")
    leaching_time_hr: float = Field(ge=0, description="추천 침출 시간(시간)")


class Recommendation(BaseModel):
    process_conditions: RecommendedProcessConditions
    expected_recovery: RecoveryPrediction


class AnalyzeResponse(BaseModel):
    schema_version: str
    source: Literal["mock", "live"]
    generated_at: datetime
    request_id: str
    current_prediction: RecoveryPrediction
    recommendation: Recommendation
