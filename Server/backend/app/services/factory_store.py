from collections import deque
from datetime import datetime
from threading import Lock
from uuid import uuid4

from app.schemas.factory import (
    ApplyFactoryRequest,
    FactoryCommand,
    FactoryStateResponse,
    FactoryStatusUpdate,
)


class UnknownFactoryCommand(ValueError):
    """등록되지 않은 Unity 명령의 상태가 보고됐다."""


class FactoryStore:
    """MVP용 메모리 저장소. FastAPI 재시작 시 명령과 상태가 초기화된다."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._queue: deque[FactoryCommand] = deque()
        self._known_command_ids: set[str] = set()
        self._state = FactoryStateResponse(
            source="mock",
            state="disconnected",
            progress_pct=0,
            message="가상 공장이 연결되지 않았습니다.",
            updated_at=datetime.now().astimezone(),
        )

    def queue_command(self, request: ApplyFactoryRequest) -> FactoryCommand:
        command = FactoryCommand(
            command_id=str(uuid4()),
            command="apply_and_start",
            process_conditions=request.process_conditions,
        )
        with self._lock:
            self._queue.append(command)
            self._known_command_ids.add(command.command_id)
            self._state = FactoryStateResponse(
                source="mock",
                state="queued",
                command_id=command.command_id,
                progress_pct=0,
                message="가상 공장 적용 명령이 대기 중입니다.",
                updated_at=datetime.now().astimezone(),
            )
        return command.model_copy(deep=True)

    def next_command(self) -> FactoryCommand | None:
        with self._lock:
            if not self._queue:
                return None
            return self._queue.popleft().model_copy(deep=True)

    def update_state(self, update: FactoryStatusUpdate) -> FactoryStateResponse:
        with self._lock:
            if update.command_id not in self._known_command_ids:
                raise UnknownFactoryCommand(update.command_id)
            self._state = FactoryStateResponse(
                source="mock",
                state=update.state,
                command_id=update.command_id,
                progress_pct=update.progress_pct,
                message=update.message,
                updated_at=datetime.now().astimezone(),
            )
            return self._state.model_copy(deep=True)

    def get_state(self) -> FactoryStateResponse:
        with self._lock:
            return self._state.model_copy(deep=True)
