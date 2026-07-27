import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1, max_length=12000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    reply: str
    task_status: str = "completed"
    actions: list[dict[str, Any]] = Field(default_factory=list)


def _fallback_reply(message: str) -> str:
    if any(keyword in message for keyword in ["일정", "회의", "할 일", "작업"]):
        return f"네, 실장님. 요청하신 내용을 작업으로 정리했습니다: {message}"
    return f"네, 실장님. '{message}' 요청을 확인했습니다."


@router.post("", response_model=ChatResponse)
@router.post("/", response_model=ChatResponse, include_in_schema=False)
async def create_chat(request: ChatRequest) -> ChatResponse:
    settings = get_settings()
    actions: list[dict[str, Any]] = []
    if any(keyword in request.message for keyword in ["일정", "회의", "할 일", "작업"]):
        actions.append({"type": "task.created", "status": "queued", "source": "chat"})

    if not settings.openai_api_key:
        return ChatResponse(reply=_fallback_reply(request.message), actions=actions)

    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        completion = await client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=[
                {"role": "system", "content": "당신은 JARVIS, 한국어 음성 개인 비서입니다. 간결하고 실행 중심으로 답합니다."},
                {"role": "user", "content": request.message},
            ],
            temperature=0.4,
        )
        reply = completion.choices[0].message.content or _fallback_reply(request.message)
        return ChatResponse(reply=reply, actions=actions)
    except Exception as exc:  # pragma: no cover - external API/network dependent
        logger.exception("OpenAI chat call failed; using fallback", exc_info=exc)
        return ChatResponse(reply=_fallback_reply(request.message), actions=actions)
