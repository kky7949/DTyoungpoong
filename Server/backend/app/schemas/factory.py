from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.process import RecommendedProcessConditions

FactoryState = Literal[
    "disconnected",
    "idle",
    "queued",
    "running",
    "completed",
    "error",
]


class ApplyFactoryRequest(BaseModel):
    analysis_request_id: str = Field(description="분석 요청 식별자")
    process_conditions: RecommendedProcessConditions


class ApplyFactoryResponse(BaseModel):
    command_id: str
    status: Literal["queued"]
    source: Literal["mock", "live"]


class FactoryCommand(BaseModel):
    command_id: str
    command: Literal["apply_and_start"]
    process_conditions: RecommendedProcessConditions


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
