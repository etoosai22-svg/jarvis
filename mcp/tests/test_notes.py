"""notes 서버 테스트 — tmp_path + JARVIS_MCP_DATA로 sqlite를 격리한다.

구조는 tests/test_weather.py(본보기)를 따른다.
"""

import json

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

import jarvis_mcp.notes.server as notes


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_MCP_DATA", str(tmp_path))


def _payload(result):
    assert not result.isError, result.content
    return json.loads(result.content[0].text)


async def _create(session, title="회의 메모", content="내용", tags=None):
    return _payload(
        await session.call_tool(
            "create_note", {"title": title, "content": content, "tags": tags or []}
        )
    )


async def test_tools_are_listed():
    async with create_connected_server_and_client_session(notes.mcp) as session:
        tools = {tool.name for tool in (await session.list_tools()).tools}
    assert tools == {"create_note", "search_notes", "update_note", "archive_note"}


async def test_create_and_search_roundtrip():
    async with create_connected_server_and_client_session(notes.mcp) as session:
        created = await _create(session, title="주간 회의", content="안건 정리", tags=["work"])
        assert created["title"] == "주간 회의"
        assert created["tags"] == ["work"]
        assert created["archived"] is False

        payload = _payload(await session.call_tool("search_notes", {"query": "안건"}))
    assert payload["count"] == 1
    assert payload["notes"][0]["id"] == created["id"]


async def test_tags_with_commas_survive_roundtrip():
    async with create_connected_server_and_client_session(notes.mcp) as session:
        created = await _create(session, tags=["회의, 자료", "개인"])
        assert created["tags"] == ["회의, 자료", "개인"]

        payload = _payload(await session.call_tool("search_notes", {"tag": "회의, 자료"}))
        assert payload["count"] == 1
        assert payload["notes"][0]["tags"] == ["회의, 자료", "개인"]

        # 다른 태그로는 걸리지 않는다 (쉼표가 구분자가 아님을 확인)
        miss = _payload(await session.call_tool("search_notes", {"tag": "회의"}))
    assert miss["count"] == 0


async def test_archived_notes_excluded_by_default():
    async with create_connected_server_and_client_session(notes.mcp) as session:
        created = await _create(session)
        archived = _payload(await session.call_tool("archive_note", {"note_id": created["id"]}))
        assert archived == {"archived": created["id"]}

        default = _payload(await session.call_tool("search_notes", {}))
        assert default["count"] == 0

        included = _payload(
            await session.call_tool("search_notes", {"include_archived": True})
        )
        assert included["count"] == 1
        assert included["notes"][0]["archived"] is True

        # 이미 보관된 노트를 다시 보관해도 성공
        again = _payload(await session.call_tool("archive_note", {"note_id": created["id"]}))
    assert again == {"archived": created["id"]}


async def test_update_partial_fields():
    async with create_connected_server_and_client_session(notes.mcp) as session:
        created = await _create(session, title="원래 제목", content="원래 내용", tags=["a"])
        updated = _payload(
            await session.call_tool(
                "update_note", {"note_id": created["id"], "title": "새 제목"}
            )
        )
        assert updated["title"] == "새 제목"
        assert updated["content"] == "원래 내용"
        assert updated["tags"] == ["a"]

        retagged = _payload(
            await session.call_tool("update_note", {"note_id": created["id"], "tags": []})
        )
    assert retagged["tags"] == []
    assert retagged["title"] == "새 제목"


async def test_unknown_id_is_a_tool_error():
    async with create_connected_server_and_client_session(notes.mcp) as session:
        updated = await session.call_tool("update_note", {"note_id": "없는-id", "title": "x"})
        archived = await session.call_tool("archive_note", {"note_id": "없는-id"})
    assert updated.isError
    assert archived.isError
