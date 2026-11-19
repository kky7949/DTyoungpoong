from collections import deque
import os
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


class FactoryConflict(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class FactoryStore:
    """MVP용 메모리 저장소. FastAPI 재시작 시 명령과 상태가 초기화된다."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._queue: deque[FactoryCommand] = deque()
        self._known_command_ids: set[str] = set()
        self._last_seen_at: datetime | None = None
        # DRAFT: Unity 폴링 주기 확정 후 조정한다.
        self._connection_timeout = float(os.getenv("UNITY_CONNECTION_TIMEOUT_SECONDS", "10"))
        if not 0 < self._connection_timeout < float("inf"):
            raise ValueError("UNITY_CONNECTION_TIMEOUT_SECONDS must be finite and positive")
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
            material=request.material.model_copy(deep=True),
            process_conditions=request.process_conditions.model_copy(deep=True),
            expected_recovery=request.expected_recovery.model_copy(deep=True),
        )
        with self._lock:
            if self._state.state in {"queued", "running"}:
                raise FactoryConflict("FACTORY_BUSY", "대기 또는 실행 중인 공정이 있습니다. 완료 후 다시 적용해 주세요.")
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
            self._last_seen_at = datetime.now().astimezone()
            if self._state.command_id is None:
                self._state = self._state.model_copy(update={
                    "state": "idle", "message": "가상 공장이 명령을 기다리고 있습니다.",
                    "updated_at": self._last_seen_at,
                })
            if not self._queue:
                return None
            return self._queue.popleft().model_copy(deep=True)

    def update_state(self, update: FactoryStatusUpdate) -> FactoryStateResponse:
        with self._lock:
            if update.command_id not in self._known_command_ids:
                raise UnknownFactoryCommand(update.command_id)
            if update.command_id != self._state.command_id:
                raise FactoryConflict("STALE_COMMAND", "현재 공정의 명령이 아닙니다.")
            previous = self._state
            if previous.state in {"completed", "error"}:
                if update.state != previous.state or update.progress_pct != previous.progress_pct:
                    raise FactoryConflict("INVALID_STATE_TRANSITION", "종료된 공정의 상태를 변경할 수 없습니다.")
            elif update.state == "idle" or update.progress_pct < previous.progress_pct:
                raise FactoryConflict("INVALID_STATE_TRANSITION", "공정 상태 또는 진행률을 이전 단계로 변경할 수 없습니다.")
            if update.state == "completed" and update.progress_pct != 100:
                raise FactoryConflict("INVALID_STATE_TRANSITION", "완료 상태의 진행률은 100%여야 합니다.")
            self._last_seen_at = datetime.now().astimezone()
            # 보고가 명령 조회보다 먼저 도착해도 종료된 명령이 나중에 실행되지 않게 한다.
            self._queue.clear()
            self._state = FactoryStateResponse(
                source="mock",
                state=update.state,
                command_id=update.command_id,
                progress_pct=update.progress_pct,
                message=update.message,
                updated_at=datetime.now().astimezone(),
            )
            return self._snapshot()

    def get_state(self) -> FactoryStateResponse:
        with self._lock:
            return self._snapshot()

    def _snapshot(self) -> FactoryStateResponse:
        connected = self._last_seen_at is not None and (
            datetime.now().astimezone() - self._last_seen_at
        ).total_seconds() < self._connection_timeout
        return self._state.model_copy(deep=True, update={
            "connection_status": "connected" if connected else "disconnected",
            "last_seen_at": self._last_seen_at,
        })
