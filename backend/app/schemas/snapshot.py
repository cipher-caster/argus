from sqlmodel import SQLModel, Field
from sqlalchemy import Index, text
from typing import Optional
from datetime import datetime


class SignalOutcomeSnapshot(SQLModel, table=True):
    __tablename__ = "signal_outcome_snapshot"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Slice dimensions
    snapshot_date: str          # ISO date, e.g. "2026-04-08"
    regime: str                 # "BULL" | "BEAR" | "ALL"
    conviction_band: str        # "55-64" | "65-74" | "75+" | "ALL"
    source: str                 # "live" | "backtest" | "scanner" | "ALL"
    coin: Optional[str] = Field(default=None)   # e.g. "BTCUSDT" or None for aggregate

    # Outcome counts
    wins: int = Field(default=0)
    losses: int = Field(default=0)
    reviews: int = Field(default=0)
    rejected: int = Field(default=0)
    total_resolved: int = Field(default=0)

    # Derived metrics
    win_rate: Optional[float] = Field(default=None)                  # wins/(wins+losses)*100
    avg_time_to_resolution_ms: Optional[float] = Field(default=None) # mean(resolved_at - fired_at)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        # Partial unique index for aggregate rows (coin IS NULL)
        Index(
            "uq_snapshot_aggregate",
            "snapshot_date", "regime", "conviction_band", "source",
            unique=True,
            postgresql_where=text("coin IS NULL"),
        ),
        # Partial unique index for per-coin rows (coin IS NOT NULL)
        Index(
            "uq_snapshot_per_coin",
            "snapshot_date", "regime", "conviction_band", "source", "coin",
            unique=True,
            postgresql_where=text("coin IS NOT NULL"),
        ),
    )
