from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.task import Task

router = APIRouter()
VALID_STATUSES = {"queued", "planning", "waiting_for_approval", "running", "completed", "failed", "cancelled"}


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    user_id: str | None = None
    priority: int = Field(default=3, ge=1, le=5)


class TaskRead(BaseModel):
    id: str
    user_id: str | None
    title: str
    description: str | None
    status: str
    priority: int
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


@router.get("", response_model=list[TaskRead])
@router.get("/", response_model=list[TaskRead], include_in_schema=False)
async def list_tasks(user_id: str | None = None, db: AsyncSession = Depends(get_db)) -> list[Task]:
    stmt = select(Task).order_by(Task.created_at.desc())
    if user_id:
        stmt = stmt.where(Task.user_id == user_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_task(payload: TaskCreate, db: AsyncSession = Depends(get_db)) -> Task:
    task = Task(**payload.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task_status(task_id: str, status_value: str, db: AsyncSession = Depends(get_db)) -> Task:
    if status_value not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="invalid task status")
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    task.status = status_value
    if status_value == "completed":
        task.completed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(task)
    return task
