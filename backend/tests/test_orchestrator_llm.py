"""LLM function-calling 경로 검증 — OpenAI SDK 타입을 그대로 쓰되 네트워크는 없다.

실키 검증 전에 코드 쪽 결함(도구명 분해, 승인 분기, 메시지 직렬화, 라운드 한도)을
여기서 걸러낸다. 실제 모델의 판단 품질은 이 테스트의 범위가 아니다.
"""

import asyncio
import json

import pytest
from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall, Function

import jarvis_mcp.weather.server as weather_server
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.services import mcp_gateway, orchestrator


@pytest.fixture
def mcp_data(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_MCP_DATA", str(tmp_path))
    monkeypatch.setenv("JARVIS_FILES_ROOT", str(tmp_path / "files"))
    return tmp_path


@pytest.fixture
def settings_with_key():
    base = get_settings()
    from app.core.config import Settings

    return Settings(**{**base.model_dump(), "llm_api_key": "sk-test-not-a-real-key", "llm_base_url": None})


def _assistant_tool_call(name: str, arguments: dict) -> ChatCompletionMessage:
    return ChatCompletionMessage(
        role="assistant",
        content=None,
        tool_calls=[
            ChatCompletionMessageToolCall(
                id=f"call_{name}",
                type="function",
                function=Function(name=name, arguments=json.dumps(arguments)),
            )
        ],
    )


def _assistant_text(text: str) -> ChatCompletionMessage:
    return ChatCompletionMessage(role="assistant", content=text)


class FakeOpenAI:
    """스크립트대로 응답하고, 받은 messages가 SDK로 보낼 수 있는 형태인지 검사한다."""

    def __init__(self, script, recorder):
        self._script = list(script)
        self._recorder = recorder
        self.chat = self  # client.chat.completions.create 체인을 자기 자신으로 잇는다
        self.completions = self

    async def create(self, *, model, messages, tools=None, temperature=None, **kwargs):
        self._recorder["model"] = model
        self._recorder["messages"].append(list(messages))
        self._recorder["tools"] = tools
        for message in messages:
            # 실제 SDK는 pydantic 모델 또는 dict만 받는다. 그 외 타입이면 여기서 잡는다.
            if not isinstance(message, dict):
                assert hasattr(message, "model_dump"), f"직렬화 불가 메시지: {type(message)}"
                json.dumps(message.model_dump(exclude_none=True))
            else:
                json.dumps(message)
        reply = self._script.pop(0)
        return type("Completion", (), {"choices": [type("Choice", (), {"message": reply})()]})()


def _install_fake(monkeypatch, script):
    """build_client()가 부르는 이름을 바꾼다 (llm.py가 import 시점에 바인딩하므로)."""
    recorder = {"messages": [], "tools": None}
    import app.core.llm as llm_module

    monkeypatch.setattr(llm_module, "AsyncOpenAI", lambda **kw: FakeOpenAI(script, recorder))
    return recorder


async def _orchestrate(settings, message="테스트"):
    async with AsyncSessionLocal() as db:
        result = await orchestrator.orchestrate(
            db=db,
            settings=settings,
            user_id="local-user",
            session_id="s-llm",
            user_message=message,
            llm_messages=[{"role": "system", "content": "sys"}, {"role": "user", "content": message}],
        )
        await db.commit()
        return result


def test_tool_call_then_text_executes_and_replies(client, mcp_data, settings_with_key, monkeypatch):
    async def fake_get_json(url, params):
        if "geocoding" in url:
            return {"results": [{"name": "서울", "latitude": 37.5, "longitude": 127.0, "timezone": "Asia/Seoul"}]}
        return {"current": {"temperature_2m": 28.0}, "current_units": {}}

    monkeypatch.setattr(weather_server, "_get_json", fake_get_json)
    recorder = _install_fake(
        monkeypatch,
        [
            _assistant_tool_call("weather__get_current_weather", {"location": "서울"}),
            _assistant_text("네, 실장님. 서울은 28도입니다."),
        ],
    )

    result = asyncio.run(_orchestrate(settings_with_key, "서울 날씨"))

    assert result.reply == "네, 실장님. 서울은 28도입니다."
    assert result.actions == [
        {
            "type": "tool.executed",
            "server": "weather",
            "tool": "get_current_weather",
            "status": "success",
            "request_id": result.actions[0]["request_id"],
        }
    ]
    # 2라운드째 요청에 tool 결과가 실려 나갔는지 (function-calling 프로토콜 준수)
    second_round = recorder["messages"][1]
    tool_messages = [m for m in second_round if isinstance(m, dict) and m.get("role") == "tool"]
    assert len(tool_messages) == 1
    assert json.loads(tool_messages[0]["content"])["status"] == "success"
    assert tool_messages[0]["tool_call_id"] == "call_weather__get_current_weather"


def test_tool_schemas_are_passed_to_the_model(client, mcp_data, settings_with_key, monkeypatch):
    recorder = _install_fake(monkeypatch, [_assistant_text("도구 없이 답합니다.")])
    asyncio.run(_orchestrate(settings_with_key))

    names = {tool["function"]["name"] for tool in recorder["tools"]}
    assert len(names) == 22
    assert {"weather__get_current_weather", "calendar__create_event", "files__read_file"} <= names


def test_approval_required_tool_is_not_executed(client, mcp_data, settings_with_key, monkeypatch):
    arguments = {"title": "이사회", "starts_at": "2026-08-01T09:00:00", "ends_at": "2026-08-01T10:00:00"}
    _install_fake(
        monkeypatch,
        [
            _assistant_tool_call("calendar__create_event", arguments),
            _assistant_text("승인해 주시면 등록하겠습니다."),
        ],
    )

    result = asyncio.run(_orchestrate(settings_with_key, "이사회 일정"))

    assert result.task_status == "waiting_for_approval"
    approval = next(a for a in result.actions if a["type"] == "approval.required")
    assert (approval["server"], approval["tool"]) == ("calendar", "create_event")

    async def calendar_count():
        async with AsyncSessionLocal() as db:
            found = await mcp_gateway.invoke(
                db=db, user_id="local-user", session_id="s-verify",
                server="calendar", tool="search_events", arguments={"query": "이사회"},
            )
        data = found.data.get("result", found.data)
        return data["count"]

    assert asyncio.run(calendar_count()) == 0  # 승인 전에는 실행되지 않는다

    # 보류된 호출이 작업 payload에 저장되어 승인 API가 실행할 수 있어야 한다
    task = next(t for t in client.get("/api/v1/tasks").json() if t["id"] == approval["task_id"])
    assert json.loads(task["payload"])["arguments"]["title"] == "이사회"


def test_round_limit_stops_endless_tool_calls(client, mcp_data, settings_with_key, monkeypatch):
    async def fake_get_json(url, params):
        if "geocoding" in url:
            return {"results": [{"name": "서울", "latitude": 37.5, "longitude": 127.0, "timezone": "Asia/Seoul"}]}
        return {"current": {"temperature_2m": 28.0}, "current_units": {}}

    monkeypatch.setattr(weather_server, "_get_json", fake_get_json)
    call = _assistant_tool_call("weather__get_current_weather", {"location": "서울"})
    _install_fake(monkeypatch, [call, call, call, call])

    result = asyncio.run(_orchestrate(settings_with_key, "날씨"))

    assert len([a for a in result.actions if a["type"] == "tool.executed"]) == orchestrator.MAX_TOOL_ROUNDS
    assert "한도" in result.reply


def test_llm_failure_falls_back_to_rule_router(client, mcp_data, settings_with_key, monkeypatch):
    class Boom:
        def __init__(self, *a, **kw):
            self.chat = self
            self.completions = self

        async def create(self, **kwargs):
            raise RuntimeError("API 장애")

    import app.core.llm as llm_module

    monkeypatch.setattr(llm_module, "AsyncOpenAI", Boom)

    result = asyncio.run(_orchestrate(settings_with_key, "아이스 아메리카노 선호 메모해줘"))

    # 규칙 라우터가 대신 처리해 메모가 저장되어야 한다
    assert result.actions[0]["tool"] == "create_note"
    assert result.actions[0]["status"] == "success"
