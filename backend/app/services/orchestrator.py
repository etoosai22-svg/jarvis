"""오케스트레이터 (Part 15 흐름의 MVP) — 발화에서 도구를 선택해 게이트웨이로 호출한다.

- LLM 사용 가능: OpenAI function-calling으로 도구 선택 (최대 3라운드)
- LLM 없음: 규칙 기반 한국어 라우터 (날씨 / 검색 / 메모 / 일정 등록)
- 승인 필수 도구는 실행하지 않고 waiting_for_approval 작업을 만든다 (docs/09 승인 실행 규칙)

승인 정책·타임아웃·감사 로그는 게이트웨이 책임이다 — 여기서는 다시 검사하지 않는다.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.task import Task
from app.services import mcp_gateway

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 3


@dataclass
class OrchestrationResult:
    reply: str | None = None  # None이면 도구 의도 없음 — 호출자가 일반 대화로 처리
    actions: list[dict[str, Any]] = field(default_factory=list)
    task_status: str = "completed"


async def _run_tool(
    db: AsyncSession, user_id: str, session_id: str, server: str, tool: str, arguments: dict[str, Any]
) -> tuple[mcp_gateway.ToolCallResult, dict[str, Any]]:
    result = await mcp_gateway.invoke(
        db=db, user_id=user_id, session_id=session_id, server=server, tool=tool, arguments=arguments
    )
    action = {"type": "tool.executed", "server": server, "tool": tool, "status": result.status, "request_id": result.request_id}
    return result, action


async def _pend_approval(
    db: AsyncSession, user_id: str, server: str, tool: str, arguments: dict[str, Any], title: str
) -> Task:
    task = Task(
        user_id=user_id,
        title=title[:200],
        description=f"승인 시 {server}.{tool} 을(를) 실행합니다.",
        status="waiting_for_approval",
        payload=json.dumps({"server": server, "tool": tool, "arguments": arguments}, ensure_ascii=False),
    )
    db.add(task)
    await db.flush()
    return task


def _tool_data(result: mcp_gateway.ToolCallResult) -> dict[str, Any]:
    data = result.data or {}
    return data.get("result", data) if isinstance(data, dict) else {}


# ---------------------------------------------------------------- 규칙 기반 라우터

_ISO_RE = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")
_REL_RE = re.compile(r"(오늘|내일|모레)\s*(?:오전|오후)?\s*(\d{1,2})시(?:\s*(\d{1,2})분)?")


def _parse_when(message: str, now: datetime | None = None) -> datetime | None:
    """'내일 10시' / '2026-07-28T10:00' 류만 지원하는 최소 파서. 못 읽으면 None."""
    if match := _ISO_RE.search(message):
        try:
            return datetime.fromisoformat(match.group().replace(" ", "T"))
        except ValueError:
            return None
    if match := _REL_RE.search(message):
        now = now or datetime.now()
        offset = {"오늘": 0, "내일": 1, "모레": 2}[match.group(1)]
        hour = int(match.group(2))
        if "오후" in match.group() and hour < 12:
            hour += 12
        minute = int(match.group(3) or 0)
        if hour > 23 or minute > 59:
            return None
        return (now + timedelta(days=offset)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    return None


def _extract_location(message: str) -> str:
    match = re.search(r"([가-힣A-Za-z]+)\s*(?:의)?\s*날씨", message)
    candidate = match.group(1) if match else ""
    return "서울" if not candidate or candidate in {"오늘", "내일", "지금", "현재"} else candidate


def _clean_query(message: str, *stopwords: str) -> str:
    query = message
    for word in stopwords:
        query = query.replace(word, " ")
    return " ".join(query.split()).strip()


async def _route_by_rules(
    db: AsyncSession, settings: Settings, user_id: str, session_id: str, message: str
) -> OrchestrationResult:
    out = OrchestrationResult()

    if "날씨" in message:
        location = _extract_location(message)
        result, action = await _run_tool(
            db, user_id, session_id, "weather", "get_current_weather", {"location": location}
        )
        out.actions.append(action)
        if result.status == "success":
            current = _tool_data(result).get("current", {})
            temp, humid = current.get("temperature_2m"), current.get("relative_humidity_2m")
            out.reply = f"네, 실장님. 현재 {location} 기온은 {temp}°C, 습도는 {humid}%입니다."
        else:
            out.reply = f"죄송합니다, 실장님. 날씨 조회에 실패했습니다: {result.error}"
        return out

    if "검색" in message:
        query = _clean_query(message, "검색해줘", "검색해 줘", "검색", "해줘")
        result, action = await _run_tool(db, user_id, session_id, "search", "search_web", {"query": query or message})
        out.actions.append(action)
        if result.status == "success":
            rows = _tool_data(result).get("results", [])[:3]
            listing = "\n".join(f"- {row['title']} ({row['url']})" for row in rows) or "- 결과가 없습니다."
            out.reply = f"네, 실장님. '{query or message}' 검색 결과입니다:\n{listing}"
        else:
            out.reply = f"죄송합니다, 실장님. 검색에 실패했습니다: {result.error}"
        return out

    if "메모" in message:
        content = _clean_query(message, "메모해줘", "메모해 줘", "메모로", "메모")
        result, action = await _run_tool(
            db, user_id, session_id, "notes", "create_note", {"title": content[:40] or "메모", "content": content or message}
        )
        out.actions.append(action)
        out.reply = (
            "네, 실장님. 메모로 저장했습니다."
            if result.status == "success"
            else f"죄송합니다, 실장님. 메모 저장에 실패했습니다: {result.error}"
        )
        return out

    if "일정" in message and any(word in message for word in ("잡아", "등록", "추가")):
        when = _parse_when(message)
        if when is None:
            out.reply = "네, 실장님. 일정을 등록하려면 날짜와 시간을 알려주세요. 예: '내일 10시 전략 회의 일정 잡아줘'"
            return out
        title = _clean_query(message, "일정", "잡아줘", "잡아 줘", "등록해줘", "등록", "추가해줘", "추가") or "새 일정"
        title = _REL_RE.sub("", _ISO_RE.sub("", title)).strip() or "새 일정"
        arguments = {"title": title, "starts_at": when.isoformat(), "ends_at": (when + timedelta(hours=1)).isoformat()}
        task = await _pend_approval(db, user_id, "calendar", "create_event", arguments, f"일정 생성: {title}")
        out.actions.append({"type": "approval.required", "task_id": task.id, "server": "calendar", "tool": "create_event"})
        out.task_status = "waiting_for_approval"
        out.reply = (
            f"네, 실장님. {when.strftime('%m월 %d일 %H:%M')}에 '{title}' 일정을 등록할 준비를 마쳤습니다. "
            "작업 카드에서 승인해 주시면 바로 등록하겠습니다."
        )
        return out

    return out  # reply=None → 도구 의도 없음


# ---------------------------------------------------------------- LLM function-calling

async def _openai_tools_schema() -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = []
    for server in mcp_gateway.MVP_SERVERS:
        for tool in await mcp_gateway.list_tools(server):
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": f"{server}__{tool['name']}",
                        "description": f"[{server}] {tool['description'] or ''}"[:1024],
                        "parameters": tool["input_schema"],
                    },
                }
            )
    return tools


async def _route_by_llm(
    db: AsyncSession,
    settings: Settings,
    user_id: str,
    session_id: str,
    llm_messages: list[dict[str, Any]],
) -> OrchestrationResult:  # pragma: no cover - 외부 API 의존 (키 없는 테스트 환경에서는 규칙 라우터 사용)
    from openai import AsyncOpenAI

    out = OrchestrationResult()
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    tools = await _openai_tools_schema()
    messages = list(llm_messages)

    for _ in range(MAX_TOOL_ROUNDS):
        completion = await client.chat.completions.create(
            model=settings.openai_chat_model, messages=messages, tools=tools, temperature=0.4
        )
        choice = completion.choices[0].message
        if not choice.tool_calls:
            out.reply = choice.content
            return out

        messages.append(choice)
        for call in choice.tool_calls:
            server, _, tool = call.function.name.partition("__")
            arguments = json.loads(call.function.arguments or "{}")

            if mcp_gateway.approval_required_for(server, tool):
                task = await _pend_approval(
                    db, user_id, server, tool, arguments, f"{server}.{tool} 실행 승인 요청"
                )
                out.actions.append(
                    {"type": "approval.required", "task_id": task.id, "server": server, "tool": tool}
                )
                out.task_status = "waiting_for_approval"
                tool_payload = {"status": "approval_required", "note": "사용자 승인 대기 작업으로 등록됨"}
            else:
                result, action = await _run_tool(db, user_id, session_id, server, tool, arguments)
                out.actions.append(action)
                tool_payload = result.as_dict()

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(tool_payload, ensure_ascii=False)[:8000],
                }
            )

    out.reply = "도구 호출 한도에 도달했습니다. 지금까지의 결과를 정리해 다시 말씀드리겠습니다."
    return out


async def orchestrate(
    db: AsyncSession,
    settings: Settings,
    user_id: str,
    session_id: str,
    user_message: str,
    llm_messages: list[dict[str, Any]],
) -> OrchestrationResult:
    """도구 라우팅 진입점. reply=None이면 호출자가 일반 대화 경로를 탄다."""
    if settings.openai_api_key:
        try:  # pragma: no cover - 외부 API 의존
            return await _route_by_llm(db, settings, user_id, session_id, llm_messages)
        except Exception:
            logger.exception("LLM orchestration failed; falling back to rule router")
    return await _route_by_rules(db, settings, user_id, session_id, user_message)
