"""문장 단위 스트리밍 검증 — 첫 소리까지의 시간을 결정하는 경로다."""

import asyncio

import pytest

from app.core.config import Settings, get_settings
from app.core.database import AsyncSessionLocal
from app.services import orchestrator
from app.services.chat_service import VOICE_STYLE_PROMPT, build_llm_messages
from app.services.orchestrator import _split_ready_sentences


@pytest.fixture
def mcp_data(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_MCP_DATA", str(tmp_path))
    monkeypatch.setenv("JARVIS_FILES_ROOT", str(tmp_path / "files"))
    return tmp_path


@pytest.fixture
def settings_with_key():
    base = get_settings()
    return Settings(**{**base.model_dump(), "llm_api_key": "sk-test", "llm_base_url": None})


# ---------------------------------------------------------------- 문장 분할

def test_splitter_emits_only_completed_sentences():
    ready, tail = _split_ready_sentences("네, 실장님. 서울은 30도입니다. 오후에는")
    assert ready == ["네, 실장님. 서울은 30도입니다."]
    assert tail == " 오후에는"


def test_splitter_merges_fragments_too_short_to_speak():
    """'네.' 하나로 TTS를 호출하면 호출만 늘고 말이 끊긴다."""
    ready, _ = _split_ready_sentences("네. 서울 기온은 30.5도입니다. ")
    assert len(ready) == 1
    assert ready[0].startswith("네.")


def test_splitter_holds_incomplete_tail():
    ready, tail = _split_ready_sentences("아직 문장이 끝나지 않았")
    assert ready == []
    assert tail == "아직 문장이 끝나지 않았"


# ---------------------------------------------------------------- 음성 프롬프트

def test_voice_mode_adds_style_prompt_only_when_asked():
    plain = build_llm_messages("sys", [], [], "안녕", for_voice=False)
    voice = build_llm_messages("sys", [], [], "안녕", for_voice=True)
    assert all(VOICE_STYLE_PROMPT not in m["content"] for m in plain)
    assert any(VOICE_STYLE_PROMPT == m["content"] for m in voice)


# ---------------------------------------------------------------- 스트리밍 경로

class _Delta:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class _Chunk:
    def __init__(self, delta):
        self.choices = [type("C", (), {"delta": delta})()]


class FakeStreamingClient:
    """content 델타를 흘리는 가짜 스트림. SDK와 같은 모양만 흉내낸다."""

    def __init__(self, pieces):
        self._pieces = pieces
        self.chat = self
        self.completions = self
        self.streamed = False

    async def create(self, *, stream=False, **kwargs):
        if not stream:
            raise AssertionError("on_sentence가 있으면 스트리밍으로 호출되어야 한다")
        self.streamed = True

        async def gen():
            for piece in self._pieces:
                yield _Chunk(_Delta(content=piece))

        return gen()


def test_final_reply_streams_sentence_by_sentence(client, mcp_data, settings_with_key, monkeypatch):
    import app.core.llm as llm_module

    fake = FakeStreamingClient(["네, 실장님. ", "서울 기온은 30.5도입니다. ", "오후에는 흐려지겠습니다."])
    monkeypatch.setattr(llm_module, "AsyncOpenAI", lambda **kw: fake)

    spoken: list[str] = []

    async def run():
        async with AsyncSessionLocal() as db:
            return await orchestrator.orchestrate(
                db=db,
                settings=settings_with_key,
                user_id="local-user",
                session_id="s-stream",
                user_message="서울 날씨",
                llm_messages=[{"role": "user", "content": "서울 날씨"}],
                on_sentence=lambda s: spoken.append(s) or asyncio.sleep(0),
            )

    result = asyncio.run(run())

    assert fake.streamed
    assert result.streamed is True
    # 마지막 문장을 기다리지 않고 앞 문장이 먼저 나갔어야 한다
    assert len(spoken) >= 2
    assert spoken[0].startswith("네, 실장님.")
    assert "".join(spoken).replace(" ", "") == result.reply.replace(" ", "")


def test_without_callback_the_path_stays_non_streaming(client, mcp_data, settings_with_key, monkeypatch):
    """텍스트 채팅(/chat)은 기존대로 한 번에 받는다 — 스트리밍 부작용이 없어야 한다."""
    import app.core.llm as llm_module
    from openai.types.chat import ChatCompletionMessage

    class NonStreaming:
        def __init__(self):
            self.chat = self
            self.completions = self

        async def create(self, *, stream=False, **kwargs):
            assert stream is False
            message = ChatCompletionMessage(role="assistant", content="한 번에 받은 응답입니다.")
            return type("Completion", (), {"choices": [type("C", (), {"message": message})()]})()

    monkeypatch.setattr(llm_module, "AsyncOpenAI", lambda **kw: NonStreaming())

    async def run():
        async with AsyncSessionLocal() as db:
            return await orchestrator.orchestrate(
                db=db, settings=settings_with_key, user_id="local-user", session_id="s-plain",
                user_message="안녕", llm_messages=[{"role": "user", "content": "안녕"}],
            )

    result = asyncio.run(run())
    assert result.streamed is False
    assert result.reply == "한 번에 받은 응답입니다."
