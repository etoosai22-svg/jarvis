from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import CurrentUserDep
from app.services.chat_service import handle_chat

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=64)
    message: str = Field(..., min_length=1, max_length=12000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    reply: str
    task_status: str = "completed"
    actions: list[dict[str, Any]] = Field(default_factory=list)


@router.post("", response_model=ChatResponse)
@router.post("/", response_model=ChatResponse, include_in_schema=False)
async def create_chat(
    request: ChatRequest,
    user: CurrentUserDep,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ChatResponse:
    result = await handle_chat(
        db=db,
        settings=settings,
        user_id=user.id,
        session_id=request.session_id,
        user_message=request.message,
    )
    return ChatResponse(reply=result.reply, task_status=result.task_status, actions=result.actions)
