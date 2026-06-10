from sqlalchemy import BigInteger, Index, text
from sqlmodel import Field, SQLModel


class Position(SQLModel, table=True):
    __tablename__ = "position"

    id: int | None = Field(default=None, primary_key=True)
    signal_log_id: int | None = Field(default=None, foreign_key="signal_log.id", index=True)
    symbol: str = Field(index=True)
    direction: str  # "LONG" | "SHORT"
    status: str = Field(default="PENDING", index=True)  # PENDING | OPEN | CLOSED | CANCELLED

    # Prices
    intended_entry: float
    actual_entry: float | None = Field(default=None)
    intended_tp: float
    intended_sl: float
    actual_exit: float | None = Field(default=None)

    # Sizing
    quantity: float
    quote_amount: float
    risk_amount: float

    # Results
    pnl_usd: float | None = Field(default=None)
    pnl_pct: float | None = Field(default=None)
    outcome: str | None = Field(default=None)  # WIN | LOSS | EXPIRED

    # Context
    conviction: int
    market_state: str  # Market state at open
    market_state_at_close: str | None = Field(default=None)  # Market state at close
    fired_reason: str
    provider: str = Field(default="okx")

    # Timing
    created_at: int = Field(sa_type=BigInteger)
    filled_at: int | None = Field(default=None, sa_type=BigInteger)
    closed_at: int | None = Field(default=None, sa_type=BigInteger)

    __table_args__ = (
        # Only one active position per symbol+direction at a time
        Index(
            "uq_position_active",
            "symbol",
            "direction",
            unique=True,
            postgresql_where=text("status = 'PENDING' OR status = 'OPEN'"),
        ),
    )


class TradeEvent(SQLModel, table=True):
    __tablename__ = "trade_event"

    id: int | None = Field(default=None, primary_key=True)
    position_id: int = Field(foreign_key="position.id", index=True)
    event_type: (
        str  # CREATED | FILLED | TP_HIT | SL_HIT | CANCELLED | CIRCUIT_BREAKER | RISK_REJECTED
    )
    details: str  # JSON blob — prices, reason, balance snapshot
    timestamp: int = Field(sa_type=BigInteger)
