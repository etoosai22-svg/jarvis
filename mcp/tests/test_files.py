"""files 서버 테스트 — tmp_path 샌드박스(JARVIS_FILES_ROOT)로 격리해 in-memory MCP 세션으로 검증."""

import json

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

import jarvis_mcp.files.server as files


@pytest.fixture(autouse=True)
def sandbox(tmp_path, monkeypatch):
    root = tmp_path / "sandbox"
    root.mkdir()
    monkeypatch.setenv("JARVIS_FILES_ROOT", str(root))
    return root


def _payload(result):
    assert not result.isError, result.content
    return json.loads(result.content[0].text)


async def _call(tool, arguments):
    async with create_connected_server_and_client_session(files.mcp) as session:
        return await session.call_tool(tool, arguments)


async def test_tools_are_listed():
    async with create_connected_server_and_client_session(files.mcp) as session:
        tools = {tool.name for tool in (await session.list_tools()).tools}
    assert tools == {"search_files", "read_file", "summarize_file", "create_file", "update_file"}


async def test_create_then_read_roundtrip():
    created = _payload(await _call("create_file", {"path": "notes/hello.txt", "content": "안녕 JARVIS"}))
    assert created["path"] == "notes/hello.txt"
    payload = _payload(await _call("read_file", {"path": "notes/hello.txt"}))
    assert payload["content"] == "안녕 JARVIS"
    assert payload["truncated"] is False


async def test_dotdot_escape_is_blocked():
    for tool in ("read_file", "summarize_file"):
        result = await _call(tool, {"path": "../outside.txt"})
        assert result.isError
        assert "샌드박스" in result.content[0].text
    result = await _call("create_file", {"path": "../evil.txt", "content": "x"})
    assert result.isError


async def test_absolute_path_is_blocked():
    result = await _call("read_file", {"path": "/etc/passwd"})
    assert result.isError
    assert "샌드박스" in result.content[0].text


async def test_symlink_escape_is_blocked(tmp_path, sandbox):
    secret = tmp_path / "secret.txt"
    secret.write_text("비밀", encoding="utf-8")
    (sandbox / "link.txt").symlink_to(secret)
    result = await _call("read_file", {"path": "link.txt"})
    assert result.isError
    assert "샌드박스" in result.content[0].text
    # 검색 결과에서도 탈출 링크는 제외된다
    payload = _payload(await _call("search_files", {"pattern": "*.txt"}))
    assert payload["files"] == []


async def test_create_duplicate_is_a_tool_error():
    _payload(await _call("create_file", {"path": "a.txt", "content": "1"}))
    result = await _call("create_file", {"path": "a.txt", "content": "2"})
    assert result.isError
    assert "update_file" in result.content[0].text


async def test_update_missing_is_a_tool_error():
    result = await _call("update_file", {"path": "ghost.txt", "content": "x"})
    assert result.isError


async def test_search_files_by_content():
    _payload(await _call("create_file", {"path": "docs/plan.md", "content": "오늘의 계획: 커피"}))
    _payload(await _call("create_file", {"path": "docs/log.md", "content": "어제의 기록"}))
    payload = _payload(await _call("search_files", {"pattern": "*.md", "content_query": "커피"}))
    assert payload["count"] == 1
    assert payload["files"][0]["path"] == "docs/plan.md"
    assert payload["files"][0]["size"] > 0
    assert "modified_at" in payload["files"][0]


async def test_summarize_respects_max_chars():
    _payload(await _call("create_file", {"path": "long.txt", "content": "가나다라\n" * 500}))
    payload = _payload(await _call("summarize_file", {"path": "long.txt", "max_chars": 100}))
    assert len(payload["excerpt"]) <= 100
    assert payload["line_count"] == 500
    assert "발췌" in payload["note"]
