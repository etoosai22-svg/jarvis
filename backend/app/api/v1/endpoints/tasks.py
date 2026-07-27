import json
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import CurrentUserDep
from app.core.time import utcnow
from app.models.task import Task
from app.services import mcp_gateway

router = APIRouter()
VALID_STATUSES = {"queued", "planning", "waiting_for_approval", "running", "completed", "failed", "cancelled"}


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    priority: int = Field(default=3, ge=1, le=5)


class TaskRead(BaseModel):
    id: str
    user_id: str | None
    title: str
    description: str | None
    status: str
    priority: int
    payload: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


@router.get("", response_model=list[TaskRead])
@router.get("/", response_model=list[TaskRead], include_in_schema=False)
async def list_tasks(
    user: CurrentUserDep,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Task]:
    stmt = (
        select(Task)
        .where(Task.user_id == user.id)
        .order_by(Task.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_task(
    payload: TaskCreate,
    user: CurrentUserDep,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Task:
    task = Task(**payload.model_dump(), user_id=user.id)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task_status(
    task_id: str,
    status_value: str,
    user: CurrentUserDep,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Task:
    if status_value not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="invalid task status")
    task = await db.get(Task, task_id)
    # 남의 작업은 존재 여부도 알려주지 않는다.
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="task not found")

    # 승인 실행 규칙 (docs/09): 승인 대기 + payload 작업을 running으로 전이하면
    # 보류된 MCP 호출을 approved=True로 즉시 실행하고 결과 상태로 마무리한다.
    if task.status == "waiting_for_approval" and status_value == "running" and task.payload:
        pending = json.loads(task.payload)
        result = await mcp_gateway.invoke(
            db=db,
            user_id=user.id,
            session_id=f"approval:{task.id}",
            server=pending["server"],
            tool=pending["tool"],
            arguments=pending.get("arguments") or {},
            approved=True,
        )
        if result.status == "success":
            task.status = "completed"
            task.completed_at = utcnow()
            task.description = f"승인 후 실행 완료: {pending['server']}.{pending['tool']}"
        else:
            task.status = "failed"
            task.completed_at = None
            task.description = f"승인 후 실행 실패: {result.error or result.status}"
        await db.commit()
        await db.refresh(task)
        return task

    task.status = status_value
    task.completed_at = utcnow() if status_value == "completed" else None
    await db.commit()
    await db.refresh(task)
    return task
