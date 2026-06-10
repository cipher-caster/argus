from fastapi import APIRouter, Query
from sqlalchemy import desc, func, select

from app.schemas.activity_log import ActivityLog
from app.storage import Database

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/activity-log")
async def get_activity_log(
    limit: int = Query(30, ge=1, le=200),
    offset: int = Query(0, ge=0),
    event_type: str | None = Query(None),
):
    async with Database.get_session() as session:
        base = select(ActivityLog)
        if event_type:
            base = base.where(ActivityLog.event_type == event_type)

        count_result = await session.execute(select(func.count()).select_from(base.subquery()))
        total = count_result.scalar() or 0

        stmt = base.order_by(desc(ActivityLog.timestamp)).limit(limit).offset(offset)
        result = await session.execute(stmt)
        logs = result.scalars().all()
        return {"data": [log.model_dump() for log in logs], "total": total}
