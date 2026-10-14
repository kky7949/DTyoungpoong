from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.health import router as health_router
from app.api.process import router as process_router
from app.api.status import router as status_router
from app.schemas.common import (
    AnalysisAdapterError,
    analysis_adapter_exception_handler,
    validation_exception_handler,
)

app = FastAPI(title="Youngpoong Digital Twin B API")
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(AnalysisAdapterError, analysis_adapter_exception_handler)
app.include_router(health_router)
app.include_router(status_router)
app.include_router(process_router)
