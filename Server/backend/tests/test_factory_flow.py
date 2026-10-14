from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.factory import get_factory_store
from app.main import app
from app.services.factory_store import FactoryStore


APPLY_REQUEST: dict[str, Any] = {
    "analysis_request_id": "analysis-123",
    "process_conditions": {
        "sulfuric_acid_l": 1050.0,
        "leaching_temperature_c": 62.0,
        "leaching_time_hr": 5.5,
    },
}


@pytest.fixture
def factory_store() -> FactoryStore:
    return FactoryStore()


@pytest.fixture
async def factory_client(factory_store: FactoryStore):
    app.dependency_overrides[get_factory_store] = lambda: factory_store
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://testserver",
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_apply_queues_command_and_next_returns_it_once(factory_client) -> None:
    """적용 명령이 누락되거나 Unity에 중복 전달되면 실패한다."""
    apply_response = await factory_client.post(
        "/api/v1/factory/apply",
        json=APPLY_REQUEST,
    )

    assert apply_response.status_code == 202
    applied = apply_response.json()
    assert applied["status"] == "queued"
    assert applied["source"] == "mock"
    assert applied["command_id"]

    first = await factory_client.get("/api/v1/factory/commands/next")
    assert first.status_code == 200
    assert first.json() == {
        "command_id": applied["command_id"],
        "command": "apply_and_start",
        "process_conditions": APPLY_REQUEST["process_conditions"],
    }

    second = await factory_client.get("/api/v1/factory/commands/next")
    assert second.status_code == 204
    assert second.content == b""


@pytest.mark.anyio
async def test_status_reports_running_then_completed(factory_client) -> None:
    """Unity가 보고한 진행 상태가 HMI 조회 상태에 반영되지 않으면 실패한다."""
    applied = (
        await factory_client.post("/api/v1/factory/apply", json=APPLY_REQUEST)
    ).json()
    command_id = applied["command_id"]

    running = await factory_client.post(
        "/api/v1/factory/status",
        json={
            "command_id": command_id,
            "state": "running",
            "progress_pct": 35,
            "message": "침출 공정 실행 중",
        },
    )
    assert running.status_code == 200

    running_state = await factory_client.get("/api/v1/factory/state")
    assert running_state.json()["state"] == "running"
    assert running_state.json()["progress_pct"] == 35

    completed = await factory_client.post(
        "/api/v1/factory/status",
        json={
            "command_id": command_id,
            "state": "completed",
            "progress_pct": 100,
            "message": "공정 완료",
        },
    )
    assert completed.status_code == 200

    completed_state = await factory_client.get("/api/v1/factory/state")
    assert completed_state.json()["state"] == "completed"
    assert completed_state.json()["progress_pct"] == 100


@pytest.mark.anyio
async def test_status_rejects_unknown_command_id(factory_client) -> None:
    """Unity의 오래되거나 잘못된 명령 상태가 현재 상태를 덮어쓰면 실패한다."""
    response = await factory_client.post(
        "/api/v1/factory/status",
        json={
            "command_id": "unknown-command",
            "state": "running",
            "progress_pct": 10,
            "message": "잘못된 상태",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"] == {
        "code": "UNKNOWN_COMMAND",
        "message": "알 수 없는 가상 공장 명령입니다.",
        "details": [],
    }
