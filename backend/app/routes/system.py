from typing import Optional

from fastapi import APIRouter, Query
from sqlalchemy import desc, select

from app.schemas.activity_log import ActivityLog
from app.storage import Database

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/activity-log")
async def get_activity_log(
    limit: int = Query(50, ge=1, le=200),
    event_type: Optional[str] = Query(None),
):
    async with Database.get_session() as session:
        stmt = select(ActivityLog).order_by(desc(ActivityLog.timestamp))
        if event_type:
            stmt = stmt.where(ActivityLog.event_type == event_type)
        stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        logs = result.scalars().all()
        return {"data": [log.model_dump() for log in logs]}
