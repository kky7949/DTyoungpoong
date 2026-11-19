from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MaterialComposition(BaseModel):
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
    li_content_pct: float | None = Field(
        default=None, ge=0, le=100, description="원료 내 리튬 함량(%)",
    )
    mn_content_pct: float | None = Field(
        default=None, ge=0, le=100, description="원료 내 망간 함량(%)",
    )
    cu_content_pct: float | None = Field(
        default=None, ge=0, le=100, description="원료 내 구리 불순물 함량(%)",
    )
    fe_content_pct: float | None = Field(
        default=None, ge=0, le=100, description="원료 내 철 불순물 함량(%)",
    )
    al_content_pct: float | None = Field(
        default=None, ge=0, le=100, description="원료 내 알루미늄 불순물 함량(%)",
    )


class MaterialInput(MaterialComposition):
    name: str | None = Field(default=None, description="사용자가 입력한 원료 이름")
    grade: str | None = Field(default=None, description="이전 클라이언트 호환용 원료 등급 입력. 새 HMI에서는 사용하지 않음")


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


class RecommendationOptions(BaseModel):
    mode: Literal["joint", "ni", "co"] = "joint"


class AnalyzeRequest(BaseModel):
    material: MaterialInput
    current_process: ProcessConditions
    options: RecommendationOptions | None = None


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
    material_grade: str | None = Field(default=None, description="A가 Ni/Co 함량 등 확정 기준으로 판정한 원료 등급. 미판정이면 null (DRAFT)")
    current_prediction: RecoveryPrediction | None
    recommendation: Recommendation | None
    model_version: str | None = None
    status: str | None = None
    mode: Literal["joint", "ni", "co"] | None = None
    warnings: list[str] = Field(default_factory=list)
    closest_alternative: Recommendation | None = None
