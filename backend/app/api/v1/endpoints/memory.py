from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.memory import Memory

router = APIRouter()


class MemoryCreate(BaseModel):
    category: str = Field(default="general", max_length=80)
    content: str = Field(..., min_length=1)
    title: str | None = None
    user_id: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)


class MemoryRead(BaseModel):
    id: str
    user_id: str | None
    category: str
    title: str | None
    content: str
    embedding_id: str | None
    confidence: float
    tags: list[str]
    created_at: datetime
    updated_at: datetime


class MemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    user_id: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


def _decode_tags(value: str | None) -> list[str]:
    return [tag for tag in (value or "").split(",") if tag]


def _to_read(memory: Memory) -> MemoryRead:
    return MemoryRead(
        id=memory.id,
        user_id=memory.user_id,
        category=memory.category,
        title=memory.title,
        content=memory.content,
        embedding_id=memory.embedding_id,
        confidence=memory.confidence,
        tags=_decode_tags(memory.tags),
        created_at=memory.created_at,
        updated_at=memory.updated_at,
    )


@router.get("", response_model=list[MemoryRead])
@router.get("/", response_model=list[MemoryRead], include_in_schema=False)
async def list_memory(user_id: str | None = None, category: str | None = None, db: AsyncSession = Depends(get_db)) -> list[MemoryRead]:
    stmt = select(Memory).order_by(Memory.updated_at.desc())
    if user_id:
        stmt = stmt.where(Memory.user_id == user_id)
    if category:
        stmt = stmt.where(Memory.category == category)
    result = await db.execute(stmt)
    return [_to_read(memory) for memory in result.scalars().all()]


@router.post("", response_model=MemoryRead, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=MemoryRead, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_memory(payload: MemoryCreate, db: AsyncSession = Depends(get_db)) -> MemoryRead:
    data = payload.model_dump()
    tags = data.pop("tags")
    memory = Memory(**data, tags=",".join(tags), embedding_id=None)
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    return _to_read(memory)


@router.post("/search", response_model=list[MemoryRead])
async def search_memory(payload: MemorySearchRequest, db: AsyncSession = Depends(get_db)) -> list[MemoryRead]:
    pattern = f"%{payload.query}%"
    stmt = select(Memory).where(or_(Memory.content.ilike(pattern), Memory.title.ilike(pattern))).limit(payload.limit)
    if payload.user_id:
        stmt = stmt.where(Memory.user_id == payload.user_id)
    result = await db.execute(stmt)
    return [_to_read(memory) for memory in result.scalars().all()]
