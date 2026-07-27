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
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall, Function

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.llm import build_client, pick_model
from app.models.task import Task
from app.services import mcp_gateway

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 6

#: 문장이 끝났다고 볼 지점. 한국어 종결(…다. …요.)도 마침표로 잡힌다.
_SENTENCE_END = re.compile(r"[.!?…](?=\s|$)|\n")
#: 너무 잘게 쪼개면 TTS 호출만 늘어난다 — 이보다 짧은 조각은 다음 문장과 합친다.
_MIN_SENTENCE_CHARS = 12

#: 완성된 문장 하나를 받는 콜백. 음성 경로가 즉시 TTS로 넘긴다.
SentenceSink = Callable[[str], Awaitable[None]]
#: 액션(도구 실행·승인 요청)이 생긴 즉시 받는 콜백.
#: 스트리밍에서는 반환값을 기다릴 수 없으므로 발생 시점에 알려야 한다.
ActionSink = Callable[[dict[str, Any]], Awaitable[None]]


def _split_ready_sentences(buffer: str) -> tuple[list[str], str]:
    """버퍼에서 완성된 문장들을 떼어내고 남은 꼬리를 돌려준다."""
    sentences: list[str] = []
    while True:
        match = _SENTENCE_END.search(buffer)
        if match is None:
            break
        cut = match.end()
        candidate = buffer[:cut].strip()
        if len(candidate) < _MIN_SENTENCE_CHARS and len(buffer) > cut:
            # 너무 짧다 — 다음 종결 지점까지 더 모은다.
            nxt = _SENTENCE_END.search(buffer, cut)
            if nxt is None:
                break
            cut = nxt.end()
            candidate = buffer[:cut].strip()
        buffer = buffer[cut:]
        if candidate:
            sentences.append(candidate)
    return sentences, buffer


async def _complete(
    client: Any,
    settings: Settings,
    messages: list[Any],
    tools: list[dict[str, Any]] | None,
    extra: dict[str, Any],
    on_sentence: SentenceSink | None,
    model: str | None = None,
) -> ChatCompletionMessage:
    """한 번의 LLM 호출. on_sentence가 있으면 스트리밍으로 받아 문장 단위로 흘린다.

    도구 호출 라운드는 사용자에게 보이는 텍스트가 없으므로 스트리밍해도 조용하고,
    최종 응답 라운드만 문장이 흘러나간다 — 그래서 첫 소리가 훨씬 빨라진다.
    """
    request: dict[str, Any] = {
        "model": model or settings.llm_chat_model,
        "messages": messages,
        "max_tokens": settings.llm_max_tokens,
        **extra,
    }
    if tools is not None:
        request["tools"] = tools

    if on_sentence is None:
        completion = await client.chat.completions.create(**request)
        return completion.choices[0].message

    stream = await client.chat.completions.create(**request, stream=True)
    content = ""
    buffer = ""
    slots: dict[int, dict[str, str]] = {}

    async for chunk in stream:
        choices = getattr(chunk, "choices", None)
        if not choices:
            continue
        delta = choices[0].delta
        if getattr(delta, "content", None):
            content += delta.content
            buffer += delta.content
            ready, buffer = _split_ready_sentences(buffer)
            for sentence in ready:
                await on_sentence(sentence)
        for call in getattr(delta, "tool_calls", None) or []:
            slot = slots.setdefault(call.index, {"id": "", "name": "", "arguments": ""})
            if call.id:
                slot["id"] = call.id
            function = getattr(call, "function", None)
            if function is not None:
                slot["name"] += function.name or ""
                slot["arguments"] += function.arguments or ""

    tail = buffer.strip()
    if tail:
        await on_sentence(tail)

    tool_calls = [
        ChatCompletionMessageToolCall(
            id=slot["id"] or f"call_{index}",
            type="function",
            function=Function(name=slot["name"], arguments=slot["arguments"] or "{}"),
        )
        for index, slot in sorted(slots.items())
    ] or None
    return ChatCompletionMessage(role="assistant", content=content or None, tool_calls=tool_calls)


@dataclass
class OrchestrationResult:
    reply: str | None = None  # None이면 도구 의도 없음 — 호출자가 일반 대화로 처리
    actions: list[dict[str, Any]] = field(default_factory=list)
    task_status: str = "completed"
    #: 응답을 on_sentence로 이미 흘려보냈는지. True면 호출자가 다시 보낼 필요 없다.
    streamed: bool = False


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
    # 실행되지 않았더라도 "승인을 요청했다"는 사실을 감사 로그에 남긴다 (docs/19 S9).
    await mcp_gateway.record_decision(db, user_id, server, tool, arguments, "approval_required", approved=False)
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
    on_sentence: SentenceSink | None = None,
    on_action: ActionSink | None = None,
    for_voice: bool = False,
) -> OrchestrationResult:
    out = OrchestrationResult()
    client = build_client(settings)

    async def record(action: dict[str, Any]) -> None:
        out.actions.append(action)
        if on_action is not None:
            await on_action(action)
    assert client is not None  # orchestrate()가 키 유무를 먼저 확인한다
    tools = await _openai_tools_schema()
    messages = list(llm_messages)
    extra = {} if settings.llm_temperature is None else {"temperature": settings.llm_temperature}
    model = pick_model(settings, for_voice)

    for _ in range(MAX_TOOL_ROUNDS):
        choice = await _complete(client, settings, messages, tools, extra, on_sentence, model)
        if not choice.tool_calls:
            out.reply = choice.content
            out.streamed = on_sentence is not None and bool(choice.content)
            return out

        messages.append(choice)
        for call in choice.tool_calls:
            server, _, tool = call.function.name.partition("__")
            arguments = json.loads(call.function.arguments or "{}")

            if mcp_gateway.approval_required_for(server, tool):
                task = await _pend_approval(
                    db, user_id, server, tool, arguments, f"{server}.{tool} 실행 승인 요청"
                )
                await record(
                    {"type": "approval.required", "task_id": task.id, "server": server, "tool": tool}
                )
                out.task_status = "waiting_for_approval"
                tool_payload = {"status": "approval_required", "note": "사용자 승인 대기 작업으로 등록됨"}
            else:
                result, action = await _run_tool(db, user_id, session_id, server, tool, arguments)
                await record(action)
                tool_payload = result.as_dict()

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(tool_payload, ensure_ascii=False)[:8000],
                }
            )

    # 한도에 걸렸다면 도구 없이 한 번 더 불러 지금까지의 결과를 말이 되는 문장으로 정리한다.
    # (사용자에게 "한도 도달"이라고 말하는 건 답이 아니다 — 특히 음성에서는.)
    try:
        messages.append({
            "role": "user",
            "content": "지금까지 확인한 내용만으로 실장님께 결과를 간결히 보고하세요. 추가 도구는 쓰지 마세요.",
        })
        # tools를 빼면 Bedrock이 502를 낸다 — 히스토리에 tool_calls가 남아 있기 때문이다.
        # 대신 "도구를 더 쓰지 말라"고 말로 지시한다 (위 user 메시지).
        final = await _complete(client, settings, messages, tools, extra, on_sentence, model)
        out.reply = final.content or None
        out.streamed = on_sentence is not None and bool(out.reply)
    except Exception:
        logger.exception("summarization after tool-round limit failed")

    if not out.reply:
        out.reply = (
            "네, 실장님. 요청하신 내용을 처리했습니다. 자세한 결과는 작업 목록에서 확인해 주세요."
            if out.actions
            else "죄송합니다, 실장님. 요청을 완료하지 못했습니다. 다시 말씀해 주시겠습니까?"
        )
    return out


async def orchestrate(
    db: AsyncSession,
    settings: Settings,
    user_id: str,
    session_id: str,
    user_message: str,
    llm_messages: list[dict[str, Any]],
    on_sentence: SentenceSink | None = None,
    on_action: ActionSink | None = None,
    for_voice: bool = False,
) -> OrchestrationResult:
    """도구 라우팅 진입점. reply=None이면 호출자가 일반 대화 경로를 탄다.

    on_sentence를 주면 최종 응답이 문장 단위로 흘러나오고,
    on_action은 도구 실행·승인 요청이 생긴 즉시 호출된다 (음성 경로가 쓴다).
    """
    if settings.llm_api_key:
        try:
            return await _route_by_llm(
                db, settings, user_id, session_id, llm_messages, on_sentence, on_action, for_voice
            )
        except Exception:
            logger.exception("LLM orchestration failed; falling back to rule router")
    return await _route_by_rules(db, settings, user_id, session_id, user_message)
