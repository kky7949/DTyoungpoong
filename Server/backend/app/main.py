from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.factory import router as factory_router
from app.api.factory import unknown_factory_command_handler
from app.api.health import router as health_router
from app.api.process import router as process_router
from app.api.status import router as status_router
from app.config import get_frontend_origins
from app.schemas.common import (
    AnalysisAdapterError,
    analysis_adapter_exception_handler,
    validation_exception_handler,
)
from app.services.factory_store import UnknownFactoryCommand

app = FastAPI(title="Youngpoong Digital Twin B API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_frontend_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(AnalysisAdapterError, analysis_adapter_exception_handler)
app.add_exception_handler(UnknownFactoryCommand, unknown_factory_command_handler)
app.include_router(health_router)
app.include_router(status_router)
app.include_router(process_router)
app.include_router(factory_router)

# 프로덕션 빌드가 있을 때만 HMI를 같은 8000번 주소에서 제공한다.
# API 라우터를 먼저 등록해 정적 파일 mount가 /health와 /api 경로를 가리지 않게 한다.
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
