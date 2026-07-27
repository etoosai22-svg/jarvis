"""Search MCP 서버 (Part 12 §6) — ddgs(DuckDuckGo metasearch) + httpx/BeautifulSoup 기반.

도구: search_web / search_news / open_result / extract_summary
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import anyio.to_thread
import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

MAX_TEXT_CHARS = 8000
STRIP_TAGS = ("script", "style", "nav", "footer")

mcp = FastMCP("search")


def _ddgs_search(kind: str, query: str, max_results: int) -> list[dict[str, Any]]:
    """DDGS 호출 지점 (동기) — 테스트에서 monkeypatch 한다."""
    with DDGS() as client:
        method = client.text if kind == "text" else client.news
        return method(query, max_results=max_results)


async def _fetch_html(url: str) -> str:
    """외부 HTTP 호출 지점 — 테스트에서 monkeypatch 한다."""
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


def _clamp_results(max_results: int) -> int:
    return max(1, min(max_results, 10))


def _normalize(result: dict[str, Any], *, with_date: bool = False) -> dict[str, Any]:
    item = {
        "title": result.get("title", ""),
        "url": result.get("url") or result.get("href", ""),
        "snippet": result.get("body") or result.get("snippet", ""),
    }
    if with_date:
        item["date"] = result.get("date", "")
    return item


def _validate_url(url: str) -> None:
    scheme = urlparse(url).scheme.lower()
    if scheme not in ("http", "https"):
        raise ToolError(f"http/https URL만 지원합니다: {url}")


def _extract_text(url: str, html: str) -> dict[str, str]:
    """HTML에서 제목과 본문 텍스트를 추출한다."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(STRIP_TAGS):
        tag.decompose()
    title = soup.title.get_text(strip=True) if soup.title else ""
    text = " ".join(soup.get_text(separator=" ").split())
    return {"url": url, "title": title, "text": text}


@mcp.tool()
async def search_web(query: str, max_results: int = 5) -> dict[str, Any]:
    """웹 검색을 수행한다 (DuckDuckGo). max_results는 1~10."""
    max_results = _clamp_results(max_results)
    raw = await anyio.to_thread.run_sync(_ddgs_search, "text", query, max_results)
    return {
        "query": query,
        "results": [_normalize(r) for r in raw],
        "source": "duckduckgo",
    }


@mcp.tool()
async def search_news(query: str, max_results: int = 5) -> dict[str, Any]:
    """뉴스 검색을 수행한다 (DuckDuckGo News). max_results는 1~10."""
    max_results = _clamp_results(max_results)
    raw = await anyio.to_thread.run_sync(_ddgs_search, "news", query, max_results)
    return {
        "query": query,
        "results": [_normalize(r, with_date=True) for r in raw],
        "source": "duckduckgo",
    }


@mcp.tool()
async def open_result(url: str) -> dict[str, Any]:
    """검색 결과 URL을 열어 본문 텍스트를 추출한다 (최대 8000자)."""
    _validate_url(url)
    html = await _fetch_html(url)
    extracted = _extract_text(url, html)
    text = extracted["text"]
    truncated = len(text) > MAX_TEXT_CHARS
    return {
        "url": url,
        "title": extracted["title"],
        "text": text[:MAX_TEXT_CHARS],
        "truncated": truncated,
    }


@mcp.tool()
async def extract_summary(url: str, max_chars: int = 1200) -> dict[str, Any]:
    """URL 본문의 앞부분을 발췌한다 (기본 1200자)."""
    _validate_url(url)
    max_chars = max(1, max_chars)
    html = await _fetch_html(url)
    extracted = _extract_text(url, html)
    return {
        "url": url,
        "title": extracted["title"],
        "summary": extracted["text"][:max_chars],
        "note": "발췌 기반 요약입니다. 의미 요약은 오케스트레이터(LLM)가 수행합니다.",
    }
