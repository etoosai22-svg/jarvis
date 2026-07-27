"""calendar 서버 테스트 — tmp_path sqlite로 격리해 in-memory MCP 세션으로 검증."""

import json

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

import jarvis_mcp.calendar.server as calendar


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_MCP_DATA", str(tmp_path))


def _payload(result):
    assert not result.isError, result.content
    return json.loads(result.content[0].text)


async def _create(session, title="회의", starts_at="2026-07-28T10:00:00", ends_at="2026-07-28T11:00:00", **kwargs):
    return _payload(
        await session.call_tool(
            "create_event",
            {"title": title, "starts_at": starts_at, "ends_at": ends_at, **kwargs},
        )
    )


async def test_tools_are_listed():
    async with create_connected_server_and_client_session(calendar.mcp) as session:
        tools = {tool.name for tool in (await session.list_tools()).tools}
    assert tools == {"search_events", "create_event", "update_event", "delete_event", "check_availability"}


async def test_create_and_search_roundtrip():
    async with create_connected_server_and_client_session(calendar.mcp) as session:
        created = await _create(session, title="치과 예약", description="정기 검진", location="강남")
        assert created["id"]
        assert created["title"] == "치과 예약"
        assert created["created_at"]

        found = _payload(await session.call_tool("search_events", {"query": "치과"}))
        assert found["count"] == 1
        assert found["events"][0]["id"] == created["id"]

        by_description = _payload(await session.call_tool("search_events", {"query": "검진"}))
        assert by_description["count"] == 1

        out_of_range = _payload(
            await session.call_tool(
                "search_events", {"date_from": "2026-08-01T00:00:00", "date_to": "2026-08-31T00:00:00"}
            )
        )
        assert out_of_range["count"] == 0


async def test_update_partial_fields():
    async with create_connected_server_and_client_session(calendar.mcp) as session:
        created = await _create(session, title="회의", location="본사")
        updated = _payload(
            await session.call_tool("update_event", {"event_id": created["id"], "title": "전체 회의"})
        )
    assert updated["title"] == "전체 회의"
    assert updated["location"] == "본사"
    assert updated["starts_at"] == created["starts_at"]


async def test_update_unknown_id_is_tool_error():
    async with create_connected_server_and_client_session(calendar.mcp) as session:
        result = await session.call_tool("update_event", {"event_id": "no-such-id", "title": "x"})
    assert result.isError


async def test_delete_removes_event():
    async with create_connected_server_and_client_session(calendar.mcp) as session:
        created = await _create(session, title="지울 일정")
        deleted = _payload(await session.call_tool("delete_event", {"event_id": created["id"]}))
        assert deleted["deleted"] == created["id"]

        found = _payload(await session.call_tool("search_events", {"query": "지울"}))
        assert found["count"] == 0

        again = await session.call_tool("delete_event", {"event_id": created["id"]})
    assert again.isError


async def test_check_availability_detects_overlap():
    async with create_connected_server_and_client_session(calendar.mcp) as session:
        created = await _create(session, starts_at="2026-07-28T10:00:00", ends_at="2026-07-28T11:00:00")

        overlapping = _payload(
            await session.call_tool(
                "check_availability", {"starts_at": "2026-07-28T10:30:00", "ends_at": "2026-07-28T12:00:00"}
            )
        )
        assert overlapping["available"] is False
        assert [c["id"] for c in overlapping["conflicts"]] == [created["id"]]

        adjacent = _payload(
            await session.call_tool(
                "check_availability", {"starts_at": "2026-07-28T11:00:00", "ends_at": "2026-07-28T12:00:00"}
            )
        )
        assert adjacent["available"] is True
        assert adjacent["conflicts"] == []


async def test_invalid_iso_string_is_tool_error():
    async with create_connected_server_and_client_session(calendar.mcp) as session:
        bad_create = await session.call_tool(
            "create_event", {"title": "x", "starts_at": "내일 오후", "ends_at": "2026-07-28T11:00:00"}
        )
        assert bad_create.isError

        inverted = await session.call_tool(
            "create_event",
            {"title": "x", "starts_at": "2026-07-28T11:00:00", "ends_at": "2026-07-28T10:00:00"},
        )
        assert inverted.isError

        bad_check = await session.call_tool(
            "check_availability", {"starts_at": "not-a-date", "ends_at": "2026-07-28T11:00:00"}
        )
    assert bad_check.isError
