from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

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
