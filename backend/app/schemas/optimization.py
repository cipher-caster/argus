from sqlalchemy import BigInteger
from sqlmodel import Field, SQLModel


class OptimizationExperiment(SQLModel, table=True):
    __tablename__ = "optimization_experiment"

    id: int | None = Field(default=None, primary_key=True)
    run_id: str = Field(index=True)  # UUID grouping a sweep run
    name: str  # e.g. "sl2.0_tp_adaptive"
    created_at: int = Field(sa_type=BigInteger())

    # Params tested
    symbols: str  # "BTC,ETH,BNB"
    sl_mult: float
    tp_mult: float  # 0 = adaptive
    tp_adaptive: bool
    min_titan_confidence: int
    block_sleeping: bool
    block_volatile: bool
    macro_guard: bool
    strict_macro: bool
    min_conviction: int = Field(default=65)

    # Results
    total_signals: int
    wins: int
    losses: int
    reviews: int
    win_rate: float | None = None
    total_r: float
    ev_per_trade: float | None = None
    avg_rr: float | None = None
    coin_results: str = Field(default="{}")  # JSON per-coin breakdown

    notes: str | None = None  # Analysis notes
    is_production: bool = Field(default=False)
