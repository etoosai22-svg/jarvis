"""게이트웨이 계약 검증 (docs/12 §3·§4·§7·§8) — 네트워크 없음."""

import asyncio
import json

import pytest
from mcp.server.fastmcp import FastMCP
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.audit_log import AuditLog
from app.services import mcp_gateway

VALID_STATUSES = {"success", "partial_success", "failed", "approval_required", "unauthorized", "timeout", "rate_limited"}


@pytest.fixture
def mcp_data(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_MCP_DATA", str(tmp_path))
    monkeypatch.setenv("JARVIS_FILES_ROOT", str(tmp_path / "files"))
    return tmp_path


async def _invoke(**kwargs):
    async with AsyncSessionLocal() as db:
        return await mcp_gateway.invoke(db=db, user_id="local-user", session_id="s-mcp", **kwargs)


async def _audit_rows(action: str) -> list[AuditLog]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(AuditLog).where(AuditLog.action == action))
        return list(result.scalars().all())


def test_all_mvp_servers_load_and_list_tools(mcp_data):
    async def check():
        total = 0
        for server in mcp_gateway.MVP_SERVERS:
            tools = await mcp_gateway.list_tools(server)
            assert tools, f"{server}: 도구가 없다"
            total += len(tools)
        return total

    assert asyncio.run(check()) >= 22  # 4+5+4+5+4


def test_notes_roundtrip_through_gateway(client, mcp_data):
    async def flow():
        created = await _invoke(server="notes", tool="create_note", arguments={"title": "회의", "content": "정리"})
        assert created.status == "success"
        found = await _invoke(server="notes", tool="search_notes", arguments={"query": "회의"})
        return created, found

    created, found = asyncio.run(flow())
    payload = found.data["result"] if "result" in (found.data or {}) else found.data
    assert payload["count"] == 1
    assert created.request_id != found.request_id


def test_calendar_mutation_blocked_without_approval(client, mcp_data):
    args = {"title": "전략 회의", "starts_at": "2026-07-28T10:00:00", "ends_at": "2026-07-28T11:00:00"}

    async def flow():
        blocked = await _invoke(server="calendar", tool="create_event", arguments=args)
        assert blocked.status == "approval_required"
        # 승인 전에는 실행되지 않아야 한다 — 검색으로 확인
        empty = await _invoke(server="calendar", tool="search_events", arguments={"query": "전략"})
        approved = await _invoke(server="calendar", tool="create_event", arguments=args, approved=True)
        return blocked, empty, approved

    blocked, empty, approved = asyncio.run(flow())
    empty_payload = empty.data["result"] if "result" in (empty.data or {}) else empty.data
    assert empty_payload["count"] == 0
    assert approved.status == "success"

    audits = asyncio.run(_audit_rows("mcp.calendar.create_event"))
    assert len(audits) == 2
    statuses = {json.loads(a.result)["status"] for a in audits}
    assert statuses == {"approval_required", "success"}


def test_files_sandbox_escape_maps_to_failed(client, mcp_data):
    result = asyncio.run(_invoke(server="files", tool="read_file", arguments={"path": "../escape.txt"}))
    assert result.status == "failed"
    assert "샌드박스" in (result.error or "")


def test_unknown_server_fails_and_is_audited(client, mcp_data):
    result = asyncio.run(_invoke(server="ghost", tool="anything"))
    assert result.status == "failed"
    assert asyncio.run(_audit_rows("mcp.ghost.anything"))


def test_timeout_maps_to_timeout_status_after_retry(client, mcp_data, monkeypatch):
    slow = FastMCP("slow")
    calls = {"n": 0}

    @slow.tool()
    async def sleepy() -> dict:
        calls["n"] += 1
        await asyncio.sleep(1.0)
        return {"ok": True}

    monkeypatch.setattr(mcp_gateway, "_registry_loader", lambda name: slow)
    monkeypatch.setitem(mcp_gateway.TIMEOUTS, "slow", 0.05)

    result = asyncio.run(_invoke(server="slow", tool="sleepy"))
    assert result.status == "timeout"
    assert calls["n"] == 2  # 최초 1회 + 재시도 1회 (§8)


def test_envelope_shape_matches_contract(client, mcp_data):
    result = asyncio.run(_invoke(server="notes", tool="search_notes", arguments={}))
    envelope = result.as_dict()
    assert set(envelope) == {"request_id", "status", "data", "error", "metadata"}
    assert envelope["status"] in VALID_STATUSES
    assert {"latency_ms", "source", "executed_at", "session_id"} <= set(envelope["metadata"])
