from uuid import uuid4

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse

from app.schemas.common import ErrorContent, ErrorResponse
from app.schemas.factory import (
    ApplyFactoryRequest,
    ApplyFactoryResponse,
    FactoryCommand,
    FactoryStateResponse,
    FactoryStatusUpdate,
)
from app.services.factory_store import FactoryStore, UnknownFactoryCommand

router = APIRouter(prefix="/api/v1/factory", tags=["factory"])
_factory_store = FactoryStore()


def get_factory_store() -> FactoryStore:
    return _factory_store


@router.post("/apply", response_model=ApplyFactoryResponse, status_code=status.HTTP_202_ACCEPTED)
def apply_factory_conditions(
    request: ApplyFactoryRequest,
    store: FactoryStore = Depends(get_factory_store),
) -> ApplyFactoryResponse:
    command = store.queue_command(request)
    return ApplyFactoryResponse(command_id=command.command_id, status="queued", source="mock")


@router.get("/commands/next", response_model=FactoryCommand)
def get_next_factory_command(
    store: FactoryStore = Depends(get_factory_store),
) -> FactoryCommand | Response:
    command = store.next_command()
    if command is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return command


@router.post("/status", response_model=FactoryStateResponse)
def update_factory_status(
    update: FactoryStatusUpdate,
    store: FactoryStore = Depends(get_factory_store),
) -> FactoryStateResponse:
    return store.update_state(update)


@router.get("/state", response_model=FactoryStateResponse)
def get_factory_state(
    store: FactoryStore = Depends(get_factory_store),
) -> FactoryStateResponse:
    return store.get_state()


async def unknown_factory_command_handler(
    request: Request,
    exc: UnknownFactoryCommand,
) -> JSONResponse:
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    response = ErrorResponse(
        error=ErrorContent(
            code="UNKNOWN_COMMAND",
            message="알 수 없는 가상 공장 명령입니다.",
            details=[],
        ),
        request_id=request_id,
    )
    return JSONResponse(status_code=400, content=response.model_dump(mode="json"))
