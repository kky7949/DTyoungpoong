from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.process import MaterialComposition, RecommendedProcessConditions, RecoveryPrediction

FactoryState = Literal[
    "disconnected",
    "idle",
    "queued",
    "running",
    "completed",
    "error",
]


class FactoryMaterial(MaterialComposition):
    name: str | None = Field(default=None, description="Unity 표시용 원료 이름, 미입력은 null")
    feed_amount_kg: float | None = Field(default=None, ge=0, allow_inf_nan=False, description="Unity 표시용 원료 투입량(kg), 미입력은 null")


class ApplyFactoryRequest(BaseModel):
    analysis_request_id: str = Field(description="분석 요청 식별자")
    material: FactoryMaterial
    process_conditions: RecommendedProcessConditions
    expected_recovery: RecoveryPrediction


class ApplyFactoryResponse(BaseModel):
    command_id: str
    status: Literal["queued"]
    source: Literal["mock", "live"]


class FactoryCommand(BaseModel):
    command_id: str
    command: Literal["apply_and_start"]
    material: FactoryMaterial
    process_conditions: RecommendedProcessConditions
    expected_recovery: RecoveryPrediction


class FactoryStatusUpdate(BaseModel):
    command_id: str
    state: Literal["idle", "running", "completed", "error"]
    progress_pct: float = Field(ge=0, le=100, description="공정 진행률(%)")
    message: str = Field(description="Unity가 보고한 한글 상태 메시지")


class FactoryStateResponse(BaseModel):
    source: Literal["mock", "live"]
    state: FactoryState
    command_id: str | None = None
    progress_pct: float = Field(ge=0, le=100)
    message: str
    updated_at: datetime
    connection_status: Literal["connected", "disconnected"] = "disconnected"
    last_seen_at: datetime | None = None
