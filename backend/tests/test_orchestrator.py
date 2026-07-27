"""오케스트레이터 + 승인 루프 검증 (docs/09 승인 실행 규칙) — 네트워크·LLM 없음.

키 없는 환경이므로 규칙 라우터 경로가 실행된다. 외부 API를 쓰는 weather/search는
서버 모듈의 호출 지점을 monkeypatch 한다.
"""

import json
from datetime import datetime

import pytest

import jarvis_mcp.search.server as search_server
import jarvis_mcp.weather.server as weather_server
from app.services.orchestrator import _parse_when


@pytest.fixture
def mcp_data(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_MCP_DATA", str(tmp_path))
    monkeypatch.setenv("JARVIS_FILES_ROOT", str(tmp_path / "files"))
    return tmp_path


# ---------------------------------------------------------------- _parse_when 단위

def test_parse_when_relative():
    base = datetime(2026, 7, 27, 9, 0)
    parsed = _parse_when("내일 오후 3시에 회의 잡아줘", now=base)
    assert parsed == datetime(2026, 7, 28, 15, 0)


def test_parse_when_iso_and_invalid():
    assert _parse_when("2026-07-28T10:00 전략 회의") == datetime(2026, 7, 28, 10, 0)
    assert _parse_when("일정 잡아줘") is None
    assert _parse_when("내일 25시 회의 잡아줘") is None


# ---------------------------------------------------------------- 도구 실행 경로

def test_weather_intent_calls_tool_and_replies(client, mcp_data, monkeypatch):
    async def fake_get_json(url, params):
        if "geocoding" in url:
            return {"results": [{"name": "서울", "latitude": 37.5, "longitude": 127.0, "timezone": "Asia/Seoul"}]}
        return {"current": {"temperature_2m": 30.5, "relative_humidity_2m": 62}, "current_units": {}}

    monkeypatch.setattr(weather_server, "_get_json", fake_get_json)

    response = client.post("/api/v1/chat", json={"session_id": "s-weather", "message": "서울 날씨 어때?"})
    assert response.status_code == 200
    payload = response.json()
    assert "30.5" in payload["reply"]
    assert payload["actions"][0]["type"] == "tool.executed"
    assert payload["actions"][0]["server"] == "weather"
    assert payload["actions"][0]["status"] == "success"


def test_search_intent_lists_results(client, mcp_data, monkeypatch):
    def fake_ddgs(kind, query, max_results):
        return [{"title": "결과1", "href": "https://a.example", "body": "본문"}]

    monkeypatch.setattr(search_server, "_ddgs_search", fake_ddgs)

    response = client.post("/api/v1/chat", json={"session_id": "s-search", "message": "MCP 프로토콜 검색해줘"})
    payload = response.json()
    assert payload["actions"][0]["tool"] == "search_web"
    assert "결과1" in payload["reply"]


def test_note_intent_persists_via_notes_server(client, mcp_data):
    response = client.post("/api/v1/chat", json={"session_id": "s-note", "message": "아이스 아메리카노 선호 메모해줘"})
    payload = response.json()
    assert payload["actions"][0]["tool"] == "create_note"
    assert payload["actions"][0]["status"] == "success"


# ---------------------------------------------------------------- 승인 루프 E2E

def test_calendar_intent_creates_approval_task_then_executes_on_approve(client, mcp_data):
    response = client.post(
        "/api/v1/chat",
        json={"session_id": "s-cal", "message": "내일 10시 전략 회의 일정 잡아줘"},
    )
    payload = response.json()
    assert payload["task_status"] == "waiting_for_approval"
    action = payload["actions"][0]
    assert action["type"] == "approval.required"
    assert (action["server"], action["tool"]) == ("calendar", "create_event")

    task_id = action["task_id"]
    tasks = {t["id"]: t for t in client.get("/api/v1/tasks").json()}
    pending = tasks[task_id]
    assert pending["status"] == "waiting_for_approval"
    call = json.loads(pending["payload"])
    assert call["tool"] == "create_event"
    assert "전략 회의" in call["arguments"]["title"]

    # 승인 → 즉시 실행 → completed, 캘린더에 실제로 생성됨
    approved = client.patch(f"/api/v1/tasks/{task_id}", params={"status_value": "running"}).json()
    assert approved["status"] == "completed"
    assert approved["completed_at"] is not None

    import asyncio

    from app.core.database import AsyncSessionLocal
    from app.services import mcp_gateway

    async def check_calendar():
        async with AsyncSessionLocal() as db:
            return await mcp_gateway.invoke(
                db=db, user_id="local-user", session_id="s-verify",
                server="calendar", tool="search_events", arguments={"query": "전략"},
            )

    found = asyncio.run(check_calendar())
    data = found.data.get("result", found.data)
    assert data["count"] == 1


def test_cancel_does_not_execute(client, mcp_data):
    response = client.post(
        "/api/v1/chat",
        json={"session_id": "s-cal2", "message": "모레 9시 면접 일정 등록해줘"},
    )
    task_id = response.json()["actions"][0]["task_id"]

    cancelled = client.patch(f"/api/v1/tasks/{task_id}", params={"status_value": "cancelled"}).json()
    assert cancelled["status"] == "cancelled"

    import asyncio

    from app.core.database import AsyncSessionLocal
    from app.services import mcp_gateway

    async def check_calendar():
        async with AsyncSessionLocal() as db:
            return await mcp_gateway.invoke(
                db=db, user_id="local-user", session_id="s-verify2",
                server="calendar", tool="search_events", arguments={"query": "면접"},
            )

    found = asyncio.run(check_calendar())
    data = found.data.get("result", found.data)
    assert data["count"] == 0


def test_calendar_intent_without_time_asks_for_clarification(client, mcp_data):
    response = client.post("/api/v1/chat", json={"session_id": "s-cal3", "message": "일정 잡아줘"})
    payload = response.json()
    assert payload["task_status"] == "completed"
    assert payload["actions"] == []
    assert "날짜와 시간" in payload["reply"]


def test_plain_task_keyword_still_creates_queued_task(client, mcp_data):
    """도구 의도가 없으면 기존 작업 생성 경로가 유지된다 (회귀 방지)."""
    response = client.post("/api/v1/chat", json={"session_id": "s-old", "message": "회의 준비 작업 만들어줘"})
    payload = response.json()
    assert payload["task_status"] == "queued"
    assert payload["actions"][0]["type"] == "task.created"


def test_approval_request_and_cancellation_are_audited(client, mcp_data):
    """실행되지 않은 결정도 감사 대상이다 (docs/19 S9)."""
    import asyncio

    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.models.audit_log import AuditLog

    async def audit_statuses(title_marker: str) -> list[str]:
        """테스트 DB는 세션 공유이므로 이 테스트가 만든 행만 제목으로 골라낸다."""
        async with AsyncSessionLocal() as db:
            rows = (
                await db.execute(
                    select(AuditLog).where(
                        AuditLog.action == "mcp.calendar.create_event",
                        AuditLog.target.contains(title_marker),
                    )
                )
            ).scalars().all()
        return [json.loads(row.result)["status"] for row in rows]

    approve_id = client.post(
        "/api/v1/chat", json={"session_id": "s-audit-1", "message": "내일 11시 감사대상회의 일정 잡아줘"}
    ).json()["actions"][0]["task_id"]
    cancel_id = client.post(
        "/api/v1/chat", json={"session_id": "s-audit-2", "message": "모레 15시 거절될미팅 일정 잡아줘"}
    ).json()["actions"][0]["task_id"]

    # 실행 전, 승인을 요청했다는 사실만으로 기록이 남아야 한다
    assert asyncio.run(audit_statuses("감사대상회의")) == ["approval_required"]
    assert asyncio.run(audit_statuses("거절될미팅")) == ["approval_required"]

    client.patch(f"/api/v1/tasks/{approve_id}", params={"status_value": "running"})
    client.patch(f"/api/v1/tasks/{cancel_id}", params={"status_value": "cancelled"})

    assert asyncio.run(audit_statuses("감사대상회의")) == ["approval_required", "success"]
    assert asyncio.run(audit_statuses("거절될미팅")) == ["approval_required", "cancelled"]
