"""search 서버 테스트 — 네트워크 없이 _ddgs_search/_fetch_html을 patch해 in-memory MCP 세션으로 검증.

tests/test_weather.py와 같은 구조를 따른다.
"""

import json

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

import jarvis_mcp.search.server as search

WEB_RESULTS = [
    {"title": "파이썬 공식", "href": "https://python.org", "body": "Python programming language"},
    {"title": "위키", "url": "https://ko.wikipedia.org/wiki/Python", "body": "프로그래밍 언어"},
]

NEWS_RESULTS = [
    {"title": "AI 뉴스", "url": "https://news.example.com/1", "body": "요약", "date": "2026-07-27T00:00:00"},
]

SAMPLE_HTML = """
<html>
  <head><title>테스트 페이지</title><style>body { color: red; }</style></head>
  <body>
    <nav>메뉴 홈 소개</nav>
    <script>console.log("추적 스크립트");</script>
    <main>본문 첫 문장입니다. 본문 둘째 문장입니다.</main>
    <footer>저작권 안내</footer>
  </body>
</html>
"""


@pytest.fixture(autouse=True)
def fake_external(monkeypatch):
    def _fake_ddgs(kind, query, max_results):
        return (WEB_RESULTS if kind == "text" else NEWS_RESULTS)[:max_results]

    async def _fake_fetch(url):
        return SAMPLE_HTML

    monkeypatch.setattr(search, "_ddgs_search", _fake_ddgs)
    monkeypatch.setattr(search, "_fetch_html", _fake_fetch)


def _payload(result):
    assert not result.isError, result.content
    return json.loads(result.content[0].text)


async def test_tools_are_listed():
    async with create_connected_server_and_client_session(search.mcp) as session:
        tools = {tool.name for tool in (await session.list_tools()).tools}
    assert tools == {"search_web", "search_news", "open_result", "extract_summary"}


async def test_search_web_returns_normalized_results():
    async with create_connected_server_and_client_session(search.mcp) as session:
        payload = _payload(await session.call_tool("search_web", {"query": "python"}))
    assert payload["query"] == "python"
    assert payload["source"] == "duckduckgo"
    assert payload["results"][0] == {
        "title": "파이썬 공식",
        "url": "https://python.org",
        "snippet": "Python programming language",
    }
    assert payload["results"][1]["url"] == "https://ko.wikipedia.org/wiki/Python"


async def test_search_web_clamps_max_results():
    async with create_connected_server_and_client_session(search.mcp) as session:
        payload = _payload(await session.call_tool("search_web", {"query": "python", "max_results": 0}))
    assert len(payload["results"]) == 1


async def test_search_news_includes_date():
    async with create_connected_server_and_client_session(search.mcp) as session:
        payload = _payload(await session.call_tool("search_news", {"query": "ai"}))
    assert payload["results"][0]["date"] == "2026-07-27T00:00:00"
    assert payload["results"][0]["title"] == "AI 뉴스"


async def test_open_result_extracts_and_strips_html():
    async with create_connected_server_and_client_session(search.mcp) as session:
        payload = _payload(await session.call_tool("open_result", {"url": "https://example.com/page"}))
    assert payload["title"] == "테스트 페이지"
    assert "본문 첫 문장입니다" in payload["text"]
    assert "추적 스크립트" not in payload["text"]
    assert "메뉴 홈 소개" not in payload["text"]
    assert "저작권 안내" not in payload["text"]
    assert "color: red" not in payload["text"]
    assert payload["truncated"] is False


async def test_open_result_truncates_long_text(monkeypatch):
    async def _fake_fetch(url):
        return "<html><head><title>긴 글</title></head><body>" + ("가 " * 10000) + "</body></html>"

    monkeypatch.setattr(search, "_fetch_html", _fake_fetch)
    async with create_connected_server_and_client_session(search.mcp) as session:
        payload = _payload(await session.call_tool("open_result", {"url": "https://example.com/long"}))
    assert len(payload["text"]) == 8000
    assert payload["truncated"] is True


async def test_open_result_rejects_bad_scheme():
    async with create_connected_server_and_client_session(search.mcp) as session:
        result = await session.call_tool("open_result", {"url": "file:///etc/passwd"})
    assert result.isError


async def test_extract_summary_respects_max_chars():
    async with create_connected_server_and_client_session(search.mcp) as session:
        payload = _payload(
            await session.call_tool("extract_summary", {"url": "https://example.com/page", "max_chars": 10})
        )
    assert len(payload["summary"]) == 10
    assert payload["url"] == "https://example.com/page"
    assert payload["note"] == "발췌 기반 요약입니다. 의미 요약은 오케스트레이터(LLM)가 수행합니다."
