from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.factory import get_factory_store
from app.main import app
from app.services.factory_store import FactoryStore


MATERIAL_COMPOSITION = {
    "ni_content_pct": 12.17,
    "co_content_pct": 2.41,
    "li_content_pct": 0,
    "mn_content_pct": 10.49,
    "cu_content_pct": 1.9,
    "fe_content_pct": None,
    "al_content_pct": 3.43,
}

APPLY_REQUEST: dict[str, Any] = {
    "analysis_request_id": "analysis-123",
    "material": {"name": "혼합 원료 A", "feed_amount_kg": 1000, **MATERIAL_COMPOSITION},
    "expected_recovery": {"ni_recovery_pct": 89.2, "co_recovery_pct": 82.1},
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
        "material": APPLY_REQUEST["material"],
        "expected_recovery": APPLY_REQUEST["expected_recovery"],
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


async def report(client, command_id, state="running", progress=35):
    return await client.post("/api/v1/factory/status", json={
        "command_id": command_id, "state": state,
        "progress_pct": progress, "message": "테스트 상태",
    })


@pytest.mark.anyio
async def test_custom_final_conditions_are_delivered_unchanged(factory_client):
    conditions = {"sulfuric_acid_l": 900.5, "leaching_temperature_c": 60.0, "leaching_time_hr": 4.5}
    response = await factory_client.post("/api/v1/factory/apply", json={
        **APPLY_REQUEST, "analysis_request_id": "original-analysis", "process_conditions": conditions,
    })
    assert response.status_code == 202
    command = await factory_client.get("/api/v1/factory/commands/next")
    assert command.json()["process_conditions"] == conditions


@pytest.mark.anyio
@pytest.mark.parametrize("running", [False, True])
async def test_rejects_apply_while_busy(factory_client, running):
    first = (await factory_client.post("/api/v1/factory/apply", json=APPLY_REQUEST)).json()
    if running:
        await report(factory_client, first["command_id"])
    response = await factory_client.post("/api/v1/factory/apply", json=APPLY_REQUEST)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "FACTORY_BUSY"
    assert (await factory_client.get("/api/v1/factory/state")).json()["command_id"] == first["command_id"]


@pytest.mark.anyio
@pytest.mark.parametrize("terminal,progress", [("completed", 100), ("error", 35)])
async def test_terminal_state_cannot_regress(factory_client, terminal, progress):
    command = (await factory_client.post("/api/v1/factory/apply", json=APPLY_REQUEST)).json()
    await report(factory_client, command["command_id"], terminal, progress)
    assert (await report(factory_client, command["command_id"], terminal, progress)).status_code == 200
    assert (await report(factory_client, command["command_id"])).status_code == 409
    assert (await factory_client.get("/api/v1/factory/state")).json()["state"] == terminal


@pytest.mark.anyio
async def test_old_command_cannot_overwrite_new_command(factory_client):
    old = (await factory_client.post("/api/v1/factory/apply", json=APPLY_REQUEST)).json()
    await factory_client.get("/api/v1/factory/commands/next")
    await report(factory_client, old["command_id"], "completed", 100)
    new = await factory_client.post("/api/v1/factory/apply", json=APPLY_REQUEST)
    assert new.status_code == 202
    assert (await report(factory_client, old["command_id"])).status_code == 409
    assert (await factory_client.get("/api/v1/factory/state")).json()["command_id"] == new.json()["command_id"]


@pytest.mark.anyio
async def test_rejects_progress_regression_and_incomplete_completion(factory_client):
    command = (await factory_client.post("/api/v1/factory/apply", json=APPLY_REQUEST)).json()
    await report(factory_client, command["command_id"], "running", 60)
    assert (await report(factory_client, command["command_id"], "running", 30)).status_code == 409
    assert (await report(factory_client, command["command_id"], "completed", 60)).status_code == 409


@pytest.mark.anyio
async def test_unity_connection_expires_without_losing_process_state(factory_client, monkeypatch):
    from datetime import datetime, timedelta, timezone

    current = datetime(2026, 11, 3, tzinfo=timezone.utc)

    class Clock:
        @staticmethod
        def now():
            return current

    monkeypatch.setattr("app.services.factory_store.datetime", Clock)
    assert (await factory_client.get("/api/v1/factory/state")).json().get("connection_status") == "disconnected"
    assert (await factory_client.get("/api/v1/factory/commands/next")).status_code == 204
    idle = (await factory_client.get("/api/v1/factory/state")).json()
    assert idle["state"] == "idle"
    assert idle["connection_status"] == "connected"
    command = (await factory_client.post("/api/v1/factory/apply", json=APPLY_REQUEST)).json()
    await report(factory_client, command["command_id"])
    connected = (await factory_client.get("/api/v1/factory/state")).json()
    assert connected["connection_status"] == "connected"
    current += timedelta(seconds=60)
    stale = (await factory_client.get("/api/v1/factory/state")).json()
    assert stale["connection_status"] == "disconnected"
    assert stale["state"] == "running"
    assert stale["last_seen_at"] == connected["last_seen_at"]
    await factory_client.get("/api/v1/factory/commands/next")
    assert (await factory_client.get("/api/v1/factory/state")).json()["connection_status"] == "connected"


@pytest.mark.anyio
@pytest.mark.parametrize("feed_amount", [None, 0])
async def test_display_metadata_preserves_missing_values_and_zero(factory_client, feed_amount):
    payload = {**APPLY_REQUEST, "material": {"name": None, "feed_amount_kg": feed_amount},
               "expected_recovery": {"ni_recovery_pct": 0, "co_recovery_pct": 100}}
    response = await factory_client.post("/api/v1/factory/apply", json=payload)
    assert response.status_code == 202
    command = (await factory_client.get("/api/v1/factory/commands/next")).json()
    assert command["material"] == {**payload["material"], **dict.fromkeys(MATERIAL_COMPOSITION)}
    assert command["expected_recovery"] == payload["expected_recovery"]


@pytest.mark.anyio
@pytest.mark.parametrize("section,key,value", [
    ("material", "feed_amount_kg", -1),
    ("material", "ni_content_pct", -0.1),
    ("material", "al_content_pct", 100.1),
    ("expected_recovery", "ni_recovery_pct", -0.1),
    ("expected_recovery", "ni_recovery_pct", 100.1),
    ("expected_recovery", "co_recovery_pct", None),
])
async def test_invalid_display_values_are_not_queued(factory_client, section, key, value):
    from copy import deepcopy
    payload = deepcopy(APPLY_REQUEST)
    payload[section][key] = value
    response = await factory_client.post("/api/v1/factory/apply", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert (await factory_client.get("/api/v1/factory/commands/next")).status_code == 204


@pytest.mark.anyio
@pytest.mark.parametrize("missing", ["material", "expected_recovery"])
async def test_new_apply_requests_require_display_sections(factory_client, missing):
    response = await factory_client.post("/api/v1/factory/apply", json={key: value for key, value in APPLY_REQUEST.items() if key != missing})
    assert response.status_code == 422
    assert (await factory_client.get("/api/v1/factory/commands/next")).status_code == 204


def test_queued_display_values_are_an_immutable_snapshot():
    from app.schemas.factory import ApplyFactoryRequest
    request = ApplyFactoryRequest.model_validate(APPLY_REQUEST)
    store = FactoryStore()
    store.queue_command(request)
    request.material.name = "변경된 원료"
    request.process_conditions.sulfuric_acid_l = 9999
    request.expected_recovery.ni_recovery_pct = 1
    command = store.next_command()
    assert command is not None
    assert command.material.name == "혼합 원료 A"
    assert command.process_conditions.sulfuric_acid_l == 1050
    assert command.expected_recovery.ni_recovery_pct == 89.2
