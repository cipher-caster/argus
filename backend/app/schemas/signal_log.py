from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Index, text
from typing import Optional


class SignalLog(SQLModel, table=True):
    __tablename__ = "signal_log"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Signal identity
    symbol: str = Field(index=True)           # e.g. "BTCUSDT"
    direction: str = Field(index=True)        # "LONG" | "SHORT"
    timeframe: str                             # e.g. "4h"

    # Levels
    entry: float
    tp: float
    sl: float

    # Scores
    conviction: int                            # 0–100
    oracle_signal: str                         # e.g. "STRONG_BUY"
    titan_signal: str                          # e.g. "BUY"
    oracle_score: int                          # -5 to +5
    titan_confidence: int                      # 0–100

    # Context at fire time
    market_state: str                          # e.g. "TRENDING", "RANGING", "VOLATILE"
    fired_reason: str                          # Human-readable: "Oracle +4/5 BULLISH | BUY 80%"

    # Timing
    fired_at: int = Field(sa_type=BigInteger)  # Epoch milliseconds

    # Source
    source: str = Field(default="live", index=True)  # "live" | "backtest"

    # Outcome
    outcome: str = Field(default="OPEN")       # "OPEN" | "WIN" | "LOSS" | "REVIEW"
    resolved_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    resolved_price: Optional[float] = Field(default=None)

    __table_args__ = (
        # Partial unique index: only one OPEN signal per symbol+direction at a time
        Index(
            "uq_signal_log_open",
            "symbol", "direction",
            unique=True,
            postgresql_where=text("outcome = 'OPEN'"),
        ),
        # Fast lookup for resolution job
        Index("ix_signal_log_outcome_fired", "outcome", "fired_at"),
    )
