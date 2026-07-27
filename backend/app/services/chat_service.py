"""대화 처리: 이력 영속화 → 메모리 회수 → LLM 호출 → 작업 생성."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.llm import build_client
from app.models.conversation import Conversation
from app.models.memory import Memory
from app.models.message import Message
from app.models.task import Task

logger = logging.getLogger(__name__)

FALLBACK_SYSTEM_PROMPT = "당신은 JARVIS, 한국어 음성 개인 비서입니다. 사용자를 '실장님'이라 부르고 간결하고 실행 중심으로 답합니다."

TASK_KEYWORDS = ("일정", "회의", "할 일", "작업", "예약", "정리해", "보내줘", "찾아줘")

#: 음성 응답 지침 — 글로 읽을 때와 귀로 들을 때 좋은 길이가 다르다.
#: 출력 토큰이 응답 지연을 지배하므로(초당 ~60토큰) 길이 제한이 곧 체감 속도다.
VOICE_STYLE_PROMPT = (
    "지금은 음성으로 답합니다. 소리 내어 읽힐 문장만 쓰세요.\n"
    "- 2~3문장 안에 핵심만 말합니다. 목록·표·마크다운 기호(-, *, #)를 쓰지 마세요.\n"
    "- 숫자와 단위는 읽는 대로 씁니다 (예: 30.5°C → 30.5도).\n"
    "- 먼저 결론을 말하고, 덧붙일 것이 있으면 한 문장만 더합니다."
)


@dataclass
class ChatResult:
    reply: str
    task_status: str = "completed"
    actions: list[dict[str, Any]] = field(default_factory=list)
    #: 응답을 on_sentence로 이미 흘려보냈는지 (음성 경로가 중복 전송을 피하는 데 쓴다)
    streamed: bool = False


@lru_cache
def load_system_prompt(path: str) -> str:
    try:
        text = Path(path).read_text(encoding="utf-8").strip()
    except OSError as exc:
        logger.warning("system prompt not readable at %s (%s); using fallback", path, exc)
        return FALLBACK_SYSTEM_PROMPT
    return text or FALLBACK_SYSTEM_PROMPT


def looks_like_task(message: str) -> bool:
    return any(keyword in message for keyword in TASK_KEYWORDS)


def fallback_reply(message: str) -> str:
    if looks_like_task(message):
        return f"네, 실장님. 요청하신 내용을 작업으로 정리했습니다: {message}"
    return f"네, 실장님. '{message}' 요청을 확인했습니다."


async def get_or_create_conversation(db: AsyncSession, user_id: str, session_id: str) -> Conversation:
    stmt = select(Conversation).where(
        Conversation.user_id == user_id,
        Conversation.session_id == session_id,
        Conversation.ended_at.is_(None),
    )
    conversation = (await db.execute(stmt)).scalars().first()
    if conversation is None:
        conversation = Conversation(user_id=user_id, session_id=session_id)
        db.add(conversation)
        await db.flush()
    return conversation


async def recent_messages(db: AsyncSession, conversation_id: str, limit: int) -> list[Message]:
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(limit)
    )
    return list(reversed((await db.execute(stmt)).scalars().all()))


async def relevant_memories(db: AsyncSession, user_id: str, query: str, limit: int) -> list[Memory]:
    """키워드 기반 임시 회수. Phase 3에서 벡터 검색으로 교체한다."""
    keywords = [token for token in query.split() if len(token) >= 2][:5]
    stmt = select(Memory).where(Memory.user_id == user_id)
    if keywords:
        stmt = stmt.where(or_(*[Memory.content.ilike(f"%{token}%") for token in keywords]))
    stmt = stmt.order_by(Memory.updated_at.desc()).limit(limit)
    return list((await db.execute(stmt)).scalars().all())


def build_llm_messages(
    system_prompt: str,
    memories: list[Memory],
    history: list[Message],
    user_message: str,
    for_voice: bool = False,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    if for_voice:
        messages.append({"role": "system", "content": VOICE_STYLE_PROMPT})

    if memories:
        remembered = "\n".join(f"- {memory.title or memory.category}: {memory.content}" for memory in memories)
        messages.append({"role": "system", "content": f"실장님에 대해 기억하고 있는 정보:\n{remembered}"})

    for message in history:
        role = message.role if message.role in {"user", "assistant"} else "user"
        messages.append({"role": role, "content": message.content})

    messages.append({"role": "user", "content": user_message})
    return messages


async def call_llm(settings: Settings, messages: list[dict[str, str]]) -> str | None:
    client = build_client(settings)
    if client is None:
        return None
    try:
        extra = {} if settings.llm_temperature is None else {"temperature": settings.llm_temperature}
        completion = await client.chat.completions.create(
            model=settings.llm_chat_model,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=settings.llm_max_tokens,
            **extra,
        )
        return completion.choices[0].message.content
    except Exception as exc:  # pragma: no cover - 외부 API/네트워크 의존
        logger.exception("OpenAI chat call failed; using fallback", exc_info=exc)
        return None


async def handle_chat(
    db: AsyncSession,
    settings: Settings,
    user_id: str,
    session_id: str,
    user_message: str,
    for_voice: bool = False,
    on_sentence: Any = None,
    on_action: Any = None,
) -> ChatResult:
    from app.services.orchestrator import orchestrate  # 순환 import 방지

    conversation = await get_or_create_conversation(db, user_id, session_id)
    history = await recent_messages(db, conversation.id, settings.chat_history_limit)
    memories = await relevant_memories(db, user_id, user_message, settings.chat_memory_limit)

    db.add(Message(conversation_id=conversation.id, role="user", content=user_message))

    llm_messages = build_llm_messages(
        load_system_prompt(settings.system_prompt_path), memories, history, user_message, for_voice
    )

    # 1) 오케스트레이터 — 도구 의도가 있으면 게이트웨이 호출까지 끝내고 응답을 만든다.
    orchestration = await orchestrate(
        db, settings, user_id, session_id, user_message, llm_messages, on_sentence, on_action, for_voice
    )
    if orchestration.reply is not None:
        db.add(Message(conversation_id=conversation.id, role="assistant", content=orchestration.reply))
        await db.commit()
        return ChatResult(
            reply=orchestration.reply,
            task_status=orchestration.task_status,
            actions=orchestration.actions,
            streamed=orchestration.streamed,
        )

    # 2) 일반 대화 경로 — 도구 의도 없음.
    reply = await call_llm(settings, llm_messages) or fallback_reply(user_message)

    actions: list[dict[str, Any]] = []
    if looks_like_task(user_message):
        task = Task(
            user_id=user_id,
            title=user_message[:200],
            description="대화에서 생성된 작업입니다.",
            status="queued",
        )
        db.add(task)
        await db.flush()
        actions.append({"type": "task.created", "task_id": task.id, "status": task.status, "source": "chat"})

    db.add(Message(conversation_id=conversation.id, role="assistant", content=reply))
    await db.commit()

    return ChatResult(reply=reply, task_status="queued" if actions else "completed", actions=actions)
