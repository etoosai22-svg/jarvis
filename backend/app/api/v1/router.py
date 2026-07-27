from fastapi import APIRouter

from app.api.v1.endpoints import chat, memory, tasks, voice

api_router = APIRouter()
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(voice.router, tags=["voice"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(memory.router, prefix="/memory", tags=["memory"])
