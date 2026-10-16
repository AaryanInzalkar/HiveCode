"""Event router — task event streaming via polling."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from hivecode.db.base import get_db
from hivecode.db.repositories import TaskEventRepository

router = APIRouter()


class EventResponse(BaseModel):
    seq: int
    type: str
    stage: str | None
    attempt_no: int | None
    data: dict
    created_at: str


class EventsResponse(BaseModel):
    events: list[EventResponse]
    latest_seq: int


@router.get("")
async def get_events(
    task_id: UUID = Query(...),
    after_seq: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Get task events after a sequence number (polling)."""
    # TODO: Implement with auth
    events = await TaskEventRepository.get_events_after(db, task_id, after_seq, limit)
    latest_seq = await TaskEventRepository.get_latest_seq(db, task_id)

    return EventsResponse(
        events=[
            EventResponse(
                seq=e.seq,
                type=e.type,
                stage=e.stage,
                attempt_no=e.attempt_no,
                data=e.data,
                created_at=e.created_at.isoformat(),
            )
            for e in events
        ],
        latest_seq=latest_seq,
    )
