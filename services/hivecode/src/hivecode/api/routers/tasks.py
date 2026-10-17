"""Task router — CRUD operations for tasks."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from hivecode.db.base import get_db

router = APIRouter()


class CreateTaskRequest(BaseModel):
    repository_id: UUID
    base_ref: str = "main"
    title: str = Field(..., min_length=3, max_length=200)
    objective: str = Field(..., min_length=20, max_length=5000)
    acceptance_criteria: list[dict] = Field(default_factory=list)
    scope: dict = Field(default_factory=dict)
    delivery_mode: str = "pr"  # "pr" or "report"


class CreateTaskResponse(BaseModel):
    task_id: UUID
    state: str


class TaskResponse(BaseModel):
    id: UUID
    title: str
    objective: str
    state: str
    stage: str | None
    outcome: str | None
    repair_attempts_used: int
    created_at: str
    repository_id: UUID


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    next_cursor: str | None


@router.post("", response_model=CreateTaskResponse, status_code=202)
async def create_task(
    request: Request,
    body: CreateTaskRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new task. Returns 202 — execution is asynchronous."""
    # TODO: Implement full task creation with auth, GitHub resolution, Celery enqueue
    # For now, return a placeholder
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    request: Request,
    repository_id: UUID | None = None,
    outcome: str | None = None,
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List tasks for the authenticated user."""
    # TODO: Implement with auth
    return TaskListResponse(tasks=[], next_cursor=None)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific task by ID."""
    # TODO: Implement with auth
    raise HTTPException(status_code=404, detail="Task not found")
