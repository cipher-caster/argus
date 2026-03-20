"""
Trading API routes — paper trading engine endpoints.
"""
import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, desc

from app.storage import Database, RedisClient
from app.schemas.trading import Position, TradeEvent
from app.trading.orchestrator import (
    TradeOrchestrator,
    get_trading_config,
    save_trading_config,
)
from app.trading.portfolio import PortfolioTracker, _price_map_from_tickers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trading", tags=["trading"])

_orchestrator = TradeOrchestrator()


# ------------------------------------------------------------------
# Pydantic models
# ------------------------------------------------------------------

class TradingConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    initial_capital: Optional[float] = None
    max_position_size_pct: Optional[float] = None
    max_concurrent_positions: Optional[int] = None
    max_correlated_positions: Optional[int] = None
    max_drawdown_pct: Optional[float] = None
    min_conviction: Optional[int] = None
    order_expiry_hours: Optional[int] = None


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

async def _get_portfolio(config: Optional[dict] = None) -> PortfolioTracker:
    if config is None:
        config = await get_trading_config()
    return PortfolioTracker(config["initial_capital"])


async def _get_current_prices() -> dict[str, float]:
    tickers_raw = await RedisClient.get_json("market:tickers") or []
    return _price_map_from_tickers(tickers_raw)


def _serialize_position(pos: Position) -> dict:
    return {
        "id": pos.id,
        "signal_log_id": pos.signal_log_id,
        "symbol": pos.symbol,
        "direction": pos.direction,
        "status": pos.status,
        "intended_entry": pos.intended_entry,
        "actual_entry": pos.actual_entry,
        "intended_tp": pos.intended_tp,
        "intended_sl": pos.intended_sl,
        "actual_exit": pos.actual_exit,
        "quantity": pos.quantity,
        "quote_amount": pos.quote_amount,
        "risk_amount": pos.risk_amount,
        "pnl_usd": pos.pnl_usd,
        "pnl_pct": pos.pnl_pct,
        "outcome": pos.outcome,
        "conviction": pos.conviction,
        "market_state": pos.market_state,
        "fired_reason": pos.fired_reason,
        "created_at": pos.created_at,
        "filled_at": pos.filled_at,
        "closed_at": pos.closed_at,
    }


# ------------------------------------------------------------------
# GET /api/trading/portfolio
# ------------------------------------------------------------------

@router.get("/portfolio")
async def get_portfolio():
    config = await get_trading_config()
    portfolio = await _get_portfolio(config)
    prices = await _get_current_prices()

    balance = await portfolio.get_balance()
    unrealized = await portfolio.get_unrealized_pnl(prices)
    exposure = await portfolio.get_exposure()

    # Cache balance for quick access
    await RedisClient.set_json("trading:balance", {"balance": balance}, ttl=300)

    return {
        "balance": round(balance, 2),
        "unrealized_pnl": round(unrealized, 2),
        "total_equity": round(balance + unrealized, 2),
        "exposure": exposure,
        "initial_capital": config["initial_capital"],
        "enabled": config.get("enabled", False),
        "mode": "paper",
    }


# ------------------------------------------------------------------
# GET /api/trading/positions
# ------------------------------------------------------------------

@router.get("/positions")
async def get_positions(
    status: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
):
    async with Database.get_session() as session:
        stmt = select(Position)
        if status:
            statuses = [s.strip().upper() for s in status.split(",")]
            stmt = stmt.where(Position.status.in_(statuses))
        if symbol:
            stmt = stmt.where(Position.symbol == symbol.upper())
        stmt = stmt.order_by(desc(Position.created_at))

        result = await session.execute(stmt)
        positions = result.scalars().all()

    prices = await _get_current_prices()

    data = []
    for pos in positions:
        serialized = _serialize_position(pos)
        # Add unrealized PnL for open positions
        if pos.status == "OPEN" and pos.actual_entry:
            current = prices.get(pos.symbol)
            if current:
                if pos.direction == "LONG":
                    unrealized = (current - pos.actual_entry) * pos.quantity
                else:
                    unrealized = (pos.actual_entry - current) * pos.quantity
                serialized["current_price"] = current
                serialized["unrealized_pnl_usd"] = round(unrealized, 4)
                serialized["unrealized_pnl_pct"] = round(
                    unrealized / pos.quote_amount * 100, 2
                ) if pos.quote_amount > 0 else 0.0
        data.append(serialized)

    return {"data": data, "total": len(data)}


# ------------------------------------------------------------------
# GET /api/trading/positions/{id}
# ------------------------------------------------------------------

@router.get("/positions/{position_id}")
async def get_position(position_id: int):
    async with Database.get_session() as session:
        result = await session.execute(
            select(Position).where(Position.id == position_id)
        )
        pos = result.scalars().first()
        if pos is None:
            raise HTTPException(status_code=404, detail="Position not found")

        # Fetch events
        events_result = await session.execute(
            select(TradeEvent)
            .where(TradeEvent.position_id == position_id)
            .order_by(TradeEvent.timestamp)
        )
        events = events_result.scalars().all()

    serialized = _serialize_position(pos)
    serialized["events"] = [
        {
            "id": e.id,
            "event_type": e.event_type,
            "details": json.loads(e.details),
            "timestamp": e.timestamp,
        }
        for e in events
    ]
    return serialized


# ------------------------------------------------------------------
# GET /api/trading/history
# ------------------------------------------------------------------

@router.get("/history")
async def get_history(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    symbol: Optional[str] = Query(None),
):
    async with Database.get_session() as session:
        # Total count
        from sqlalchemy import func as sa_func
        count_stmt = select(sa_func.count()).select_from(Position).where(Position.status == "CLOSED")
        if symbol:
            count_stmt = count_stmt.where(Position.symbol == symbol.upper())
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # Paginated data
        stmt = (
            select(Position)
            .where(Position.status == "CLOSED")
            .order_by(desc(Position.closed_at))
        )
        if symbol:
            stmt = stmt.where(Position.symbol == symbol.upper())
        stmt = stmt.offset(offset).limit(limit)

        result = await session.execute(stmt)
        positions = result.scalars().all()

    return {
        "data": [_serialize_position(p) for p in positions],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ------------------------------------------------------------------
# GET /api/trading/config
# ------------------------------------------------------------------

@router.get("/config")
async def get_config():
    return await get_trading_config()


# ------------------------------------------------------------------
# PUT /api/trading/config
# ------------------------------------------------------------------

@router.put("/config")
async def update_config(update: TradingConfigUpdate):
    config = await get_trading_config()
    patch = update.model_dump(exclude_none=True)
    config.update(patch)
    await save_trading_config(config)
    return config


# ------------------------------------------------------------------
# POST /api/trading/close/{id}
# ------------------------------------------------------------------

@router.post("/close/{position_id}")
async def close_position(position_id: int):
    pos = await _orchestrator.manual_close(position_id)
    if pos is None:
        raise HTTPException(
            status_code=404,
            detail="Position not found or not in an active state"
        )
    return _serialize_position(pos)


# ------------------------------------------------------------------
# POST /api/trading/close-all
# ------------------------------------------------------------------

@router.post("/close-all")
async def close_all_positions():
    async with Database.get_session() as session:
        result = await session.execute(
            select(Position).where(Position.status.in_(["PENDING", "OPEN"]))
        )
        active = result.scalars().all()

    closed = []
    for pos in active:
        result = await _orchestrator.manual_close(pos.id)
        if result:
            closed.append(result.id)

    return {"closed": len(closed), "position_ids": closed}


# ------------------------------------------------------------------
# POST /api/trading/pause
# ------------------------------------------------------------------

@router.post("/pause")
async def pause_trading():
    config = await get_trading_config()
    config["enabled"] = False
    await save_trading_config(config)
    return {"enabled": False, "message": "Trading paused"}


# ------------------------------------------------------------------
# GET /api/trading/stats
# ------------------------------------------------------------------

@router.get("/stats")
async def get_stats():
    config = await get_trading_config()
    portfolio = await _get_portfolio(config)
    stats = await portfolio.get_stats()
    equity_curve = await portfolio.get_equity_curve()
    balance = await portfolio.get_balance()
    return {
        **stats,
        "balance": round(balance, 2),
        "equity_curve": equity_curve,
    }
