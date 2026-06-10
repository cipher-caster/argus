"""
Portfolio Tracker — balance, exposure, and performance statistics.
All numbers are derived from the Position table + current prices from Redis.
"""

import logging

from sqlalchemy import func, select

from app.schemas.trading import Position
from app.storage import Database, RedisClient

logger = logging.getLogger(__name__)


def _price_map_from_tickers(tickers_raw: list) -> dict[str, float]:
    """Convert market:tickers list → {BTCUSDT: price}."""
    prices: dict[str, float] = {}
    for t in tickers_raw:
        sym = t.get("symbol", "").replace("/", "")  # "BTC/USDT" → "BTCUSDT"
        price = t.get("price")
        if sym and price:
            prices[sym] = float(price)
    return prices


class PortfolioTracker:
    def __init__(self, initial_capital: float = 100.0):
        self.initial_capital = initial_capital

    async def _get_closed_pnl(self) -> float:
        """Sum of pnl_usd on all CLOSED positions."""
        async with Database.get_session() as session:
            result = await session.execute(
                select(func.coalesce(func.sum(Position.pnl_usd), 0.0)).where(
                    Position.status == "CLOSED"
                )
            )
            return float(result.scalar())

    async def get_balance(self) -> float:
        """Realised equity: initial capital + sum of closed PnL."""
        closed_pnl = await self._get_closed_pnl()
        return self.initial_capital + closed_pnl

    async def get_unrealized_pnl(self, prices: dict | None = None) -> float:
        """Mark-to-market PnL on all OPEN positions."""
        if prices is None:
            tickers_raw = await RedisClient.get_json("market:tickers") or []
            prices = _price_map_from_tickers(tickers_raw)

        async with Database.get_session() as session:
            result = await session.execute(select(Position).where(Position.status == "OPEN"))
            open_positions = result.scalars().all()

        total_unrealized = 0.0
        for pos in open_positions:
            current = prices.get(pos.symbol)
            if current is None or pos.actual_entry is None:
                continue
            if pos.direction == "LONG":
                unrealized = (current - pos.actual_entry) * pos.quantity
            else:
                unrealized = (pos.actual_entry - current) * pos.quantity
            total_unrealized += unrealized

        return total_unrealized

    async def get_exposure(self) -> dict:
        """Total USDT locked in OPEN + PENDING positions."""
        async with Database.get_session() as session:
            result = await session.execute(
                select(Position).where(Position.status.in_(["PENDING", "OPEN"]))
            )
            active = result.scalars().all()

        total_exposure = sum(p.quote_amount for p in active)
        balance = await self.get_balance()
        exposure_pct = (total_exposure / balance * 100) if balance > 0 else 0.0
        open_count = sum(1 for p in active if p.status == "OPEN")
        pending_count = sum(1 for p in active if p.status == "PENDING")

        return {
            "total_usdt": round(total_exposure, 2),
            "pct_of_balance": round(exposure_pct, 1),
            "positions": len(active),
            "open": open_count,
            "pending": pending_count,
        }

    async def get_stats(self) -> dict:
        """Performance stats from all closed positions."""
        async with Database.get_session() as session:
            result = await session.execute(select(Position).where(Position.status == "CLOSED"))
            closed = result.scalars().all()

        if not closed:
            return {
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": None,
                "avg_win_pct": None,
                "avg_loss_pct": None,
                "profit_factor": None,
                "total_pnl_usd": 0.0,
                "max_drawdown_pct": 0.0,
            }

        wins = [p for p in closed if p.outcome == "WIN"]
        losses = [p for p in closed if p.outcome == "LOSS"]
        total = len(closed)
        win_rate = (len(wins) / total * 100) if total > 0 else None

        avg_win = (sum(p.pnl_pct for p in wins if p.pnl_pct) / len(wins)) if wins else None
        avg_loss = (sum(p.pnl_pct for p in losses if p.pnl_pct) / len(losses)) if losses else None

        gross_profit = sum(p.pnl_usd for p in wins if p.pnl_usd)
        gross_loss = abs(sum(p.pnl_usd for p in losses if p.pnl_usd))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else None

        total_pnl = sum(p.pnl_usd for p in closed if p.pnl_usd)

        # Max drawdown from equity curve
        max_dd = self._calc_max_drawdown(closed)

        return {
            "total_trades": total,
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(win_rate, 1) if win_rate is not None else None,
            "avg_win_pct": round(avg_win, 2) if avg_win is not None else None,
            "avg_loss_pct": round(avg_loss, 2) if avg_loss is not None else None,
            "profit_factor": round(profit_factor, 2) if profit_factor is not None else None,
            "total_pnl_usd": round(total_pnl, 2),
            "max_drawdown_pct": round(max_dd, 2),
        }

    def _calc_max_drawdown(self, closed_positions: list) -> float:
        """Max percentage drawdown from running equity curve."""
        if not closed_positions:
            return 0.0
        sorted_pos = sorted(closed_positions, key=lambda p: p.closed_at or 0)
        equity = self.initial_capital
        peak = equity
        max_dd = 0.0
        for p in sorted_pos:
            equity += p.pnl_usd or 0.0
            if equity > peak:
                peak = equity
            if peak > 0:
                dd = (peak - equity) / peak * 100
                if dd > max_dd:
                    max_dd = dd
        return max_dd

    async def get_equity_curve(self) -> list[dict]:
        """Running balance after each closed trade, for charting."""
        async with Database.get_session() as session:
            result = await session.execute(
                select(Position).where(Position.status == "CLOSED").order_by(Position.closed_at)
            )
            closed = result.scalars().all()

        curve = []
        balance = self.initial_capital
        for p in closed:
            balance += p.pnl_usd or 0.0
            curve.append(
                {
                    "timestamp": p.closed_at,
                    "balance": round(balance, 2),
                    "symbol": p.symbol,
                    "outcome": p.outcome,
                    "pnl_usd": round(p.pnl_usd or 0.0, 2),
                }
            )

        return curve
