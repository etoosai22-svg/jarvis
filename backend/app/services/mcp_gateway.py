"""MCP Gateway (docs/12 §3) — 승인 정책·타임아웃·재시도·감사 로그·응답 정규화.

서버는 도구 실행만 하고(§6), 여기가 호출 규칙의 단일 관문이다.
MVP는 서버를 in-process(FastMCP in-memory 세션)로 띄운다 — 별도 프로세스(stdio)
전환 시에도 이 모듈의 공개 인터페이스(invoke)는 유지된다.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from importlib import import_module
from time import perf_counter
from typing import Any

from mcp.shared.memory import create_connected_server_and_client_session
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import utcnow
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

MVP_SERVERS = ("search", "calendar", "notes", "files", "weather")

# §7 승인 정책 — 여기 있는 도구는 approved=True 없이는 실행되지 않는다.
APPROVAL_REQUIRED: dict[str, frozenset[str]] = {
    "calendar": frozenset({"create_event", "update_event", "delete_event"}),
}

# §9 타임아웃(초). 명세에 없는 서버는 10초.
TIMEOUTS: dict[str, float] = {"search": 15.0, "calendar": 10.0, "files": 30.0, "weather": 10.0, "notes": 10.0}
DEFAULT_TIMEOUT = 10.0

# §8 재시도 — 타임아웃은 1회만 더 시도한다. (in-process 구조라 네트워크 오류 재시도는
# stdio 전환 시 transport 계층에 추가한다.)
TIMEOUT_RETRIES = 1


@dataclass
class ToolCallResult:
    """§4 공통 응답 봉투."""

    request_id: str
    status: str  # success | partial_success | failed | approval_required | unauthorized | timeout | rate_limited
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "status": self.status,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }


def _load_server(name: str):
    if name not in MVP_SERVERS:
        raise KeyError(name)
    return import_module(f"jarvis_mcp.{name}.server").mcp


# 테스트에서 가짜 서버를 끼울 수 있는 주입 지점.
_registry_loader = _load_server


def approval_required_for(server: str, tool: str) -> bool:
    return tool in APPROVAL_REQUIRED.get(server, frozenset())


def _safe_target(server: str, tool: str, arguments: dict[str, Any]) -> str:
    """감사 로그 target — 값은 절단해 민감정보 노출을 줄인다(§11)."""
    compact = {k: (v if isinstance(v, (int, float, bool)) else str(v)[:80]) for k, v in arguments.items()}
    return f"{server}.{tool} {json.dumps(compact, ensure_ascii=False)[:200]}"


async def _audit(
    db: AsyncSession, user_id: str, server: str, tool: str, arguments: dict[str, Any], status: str, approved: bool
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=f"mcp.{server}.{tool}",
            target=_safe_target(server, tool, arguments),
            result=json.dumps({"status": status, "approved": approved}, ensure_ascii=False),
        )
    )
    await db.commit()


def _contains_timeout(exc: BaseException) -> bool:
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError)):
        return True
    if isinstance(exc, BaseExceptionGroup):
        return any(_contains_timeout(inner) for inner in exc.exceptions)
    return False


async def _call_once(server_obj, tool: str, arguments: dict[str, Any], timeout: float):
    try:
        async with create_connected_server_and_client_session(server_obj) as session:
            return await asyncio.wait_for(session.call_tool(tool, arguments), timeout=timeout)
    except BaseExceptionGroup as group:
        # in-memory 세션 종료 시 anyio 태스크 그룹이 TimeoutError를 감싸서 던진다.
        if _contains_timeout(group):
            raise TimeoutError from group
        raise


async def invoke(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    server: str,
    tool: str,
    arguments: dict[str, Any] | None = None,
    approved: bool = False,
) -> ToolCallResult:
    """도구 하나를 §4 봉투 규칙으로 호출한다. 모든 경로가 감사 로그를 남긴다."""
    arguments = arguments or {}
    request_id = str(uuid.uuid4())
    started = perf_counter()

    def _meta() -> dict[str, Any]:
        return {
            "latency_ms": round((perf_counter() - started) * 1000, 1),
            "source": f"mcp:{server}",
            "executed_at": utcnow().isoformat(),
            "session_id": session_id,
        }

    async def _finish(status: str, data: Any = None, error: str | None = None) -> ToolCallResult:
        await _audit(db, user_id, server, tool, arguments, status, approved)
        return ToolCallResult(request_id=request_id, status=status, data=data, error=error, metadata=_meta())

    try:
        server_obj = _registry_loader(server)
    except (KeyError, ModuleNotFoundError):
        return await _finish("failed", error=f"알 수 없는 MCP 서버: {server}")

    if approval_required_for(server, tool) and not approved:
        return await _finish("approval_required", error=None, data={"message": f"'{server}.{tool}' 실행에는 사용자 승인이 필요합니다."})

    timeout = TIMEOUTS.get(server, DEFAULT_TIMEOUT)
    for attempt in range(TIMEOUT_RETRIES + 1):
        try:
            result = await _call_once(server_obj, tool, arguments, timeout)
            break
        except (asyncio.TimeoutError, TimeoutError):
            if attempt >= TIMEOUT_RETRIES:
                return await _finish("timeout", error=f"{timeout:.0f}초 안에 응답하지 않았습니다.")
            logger.warning("mcp %s.%s timeout, retrying (%d)", server, tool, attempt + 1)
        except Exception as exc:  # transport/프로토콜 오류
            logger.exception("mcp %s.%s transport failure", server, tool)
            return await _finish("failed", error=str(exc)[:300])

    if result.isError:
        message = result.content[0].text if result.content else "tool error"
        return await _finish("failed", error=message[:500])

    # FastMCP는 dict 반환을 structuredContent로도 전달한다.
    if result.structuredContent is not None:
        data = result.structuredContent
    else:
        try:
            data = json.loads(result.content[0].text) if result.content else None
        except (ValueError, IndexError):
            data = result.content[0].text if result.content else None

    return await _finish("success", data=data)


async def list_tools(server: str) -> list[dict[str, Any]]:
    """§3 도구 스키마 조회 — 오케스트레이터가 도구 선택에 사용한다."""
    server_obj = _registry_loader(server)
    async with create_connected_server_and_client_session(server_obj) as session:
        listed = await session.list_tools()
    return [
        {
            "server": server,
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema,
            "approval_required": approval_required_for(server, tool.name),
        }
        for tool in listed.tools
    ]
