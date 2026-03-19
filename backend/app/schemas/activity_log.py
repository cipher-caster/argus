import json
import time
from typing import Optional

from sqlmodel import SQLModel, Field


class ActivityLog(SQLModel, table=True):
    __tablename__ = "activity_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    event_type: str = Field(index=True)  # STARTUP, SHUTDOWN, RECOVERY_SCAN, SIGNAL_RECOVERED, OUTCOME_RESOLVED, POSITION_RECOVERED, HEARTBEAT_GAP, ERROR
    severity: str = Field(default="INFO")  # INFO, WARN, ERROR
    details: Optional[str] = Field(default=None)  # JSON string with flexible payload

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "SIGNAL_RECOVERED",
                "severity": "INFO",
                "details": '{"symbol": "BTCUSDT", "direction": "LONG", "candle_close": "2026-03-19T16:00:00Z"}'
            }
        }


async def log_activity(event_type: str, severity: str = "INFO", **details):
    """Helper to log an activity event to the database."""
    from app.storage import Database
    async with Database.get_session() as session:
        entry = ActivityLog(
            event_type=event_type,
            severity=severity,
            details=json.dumps(details) if details else None,
        )
        session.add(entry)
        await session.commit()
