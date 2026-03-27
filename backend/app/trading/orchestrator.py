"""
Trade Orchestrator — the simulation engine.

Lifecycle:
  process_signal()    → creates PENDING positions from new OPEN signals
  check_pending_fills() → PENDING → OPEN when price reaches entry
  check_open_positions() → OPEN → CLOSED when TP/SL hit, or EXPIRED
  check_circuit_breaker() → pauses trading if drawdown threshold hit
"""
import json
import logging
import time
from typing import Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.storage import Database, RedisClient
from app.schemas.signal_log import SignalLog
from app.schemas.trading import Position, TradeEvent
from app.trading.risk_manager import RiskManager
from app.trading.portfolio import PortfolioTracker, _price_map_from_tickers
from app.trading import notifier

logger = logging.getLogger(__name__)

TRADING_CONFIG_KEY = "trading:config"
TRADING_BALANCE_KEY = "trading:balance"

FEE_PCT = 0.001  # 0.1% simulated round-trip fee per side (0.05% * 2)

DEFAULT_TRADING_CONFIG = {
    "enabled": False,
    "initial_capital": 1000.0,
    "max_position_size_pct": 10.0,
    "max_concurrent_positions": 3,
    "max_correlated_positions": 2,
    "max_drawdown_pct": 15.0,
    "max_leverage": 3.0,
    "min_conviction": 50,
    "max_total_exposure_pct": 300.0,
    "order_expiry_hours": 24,
    "entry_tolerance_pct": 1.0,
    "correlation_groups": {
        "btc_correlated": [
            "BTCUSDT", "ETHUSDT", "BNBUSDT",
            "ARBUSDT", "NEARUSDT", "APTUSDT",
        ]
    },
}


async def get_trading_config() -> dict:
    data = await RedisClient.get_json(TRADING_CONFIG_KEY)
    if data:
        # Merge with defaults to handle newly added keys
        merged = {**DEFAULT_TRADING_CONFIG, **data}
        return merged
    return dict(DEFAULT_TRADING_CONFIG)


async def save_trading_config(config: dict) -> None:
    await RedisClient.set_json(TRADING_CONFIG_KEY, config, ttl=86400 * 365)


async def _get_prices() -> dict[str, float]:
    tickers_raw = await RedisClient.get_json("market:tickers") or []
    return _price_map_from_tickers(tickers_raw)


async def _log_event(session, position_id: int, event_type: str, details: dict) -> None:
    event = TradeEvent(
        position_id=position_id,
        event_type=event_type,
        details=json.dumps(details),
        timestamp=int(time.time() * 1000),
    )
    session.add(event)


async def _get_active_positions(session) -> list:
    result = await session.execute(
        select(Position).where(Position.status.in_(["PENDING", "OPEN"]))
    )
    return list(result.scalars().all())


class TradeOrchestrator:

    def __init__(self):
        self.risk_manager = RiskManager()
        self._portfolio: Optional[PortfolioTracker] = None

    async def _get_portfolio(self, config: Optional[dict] = None) -> PortfolioTracker:
        if config is None:
            config = await get_trading_config()
        if self._portfolio is None or self._portfolio.initial_capital != config["initial_capital"]:
            self._portfolio = PortfolioTracker(config["initial_capital"])
        return self._portfolio

    # ------------------------------------------------------------------
    # process_signal: called by execute_signals job
    # ------------------------------------------------------------------
    async def process_signal(self, signal: SignalLog) -> Optional[Position]:
        config = await get_trading_config()
        if not config.get("enabled", False):
            return None

        async with Database.get_session() as session:
            # Skip if position already exists for this signal
            existing = await session.execute(
                select(Position).where(Position.signal_log_id == signal.id)
            )
            if existing.scalars().first() is not None:
                return None

            active = await _get_active_positions(session)
            portfolio = await self._get_portfolio(config)
            balance = await portfolio.get_balance()

            approved, reason, sizing = await self.risk_manager.check_all(
                symbol=signal.symbol,
                direction=signal.direction,
                conviction=signal.conviction,
                entry=signal.entry,
                sl=signal.sl,
                config=config,
                open_positions=active,
                balance=balance,
            )

            if not approved:
                logger.info(f"Orchestrator: rejected {signal.symbol} {signal.direction} — {reason}")
                # Mark signal_log as REJECTED for learning
                now_ms = int(time.time() * 1000)
                signal.outcome = "REJECTED"
                signal.rejection_reason = reason
                signal.resolved_at = now_ms
                session.add(signal)
                await notifier.notify_risk_rejected(signal.symbol, signal.direction, reason)
                return None

            quantity, quote_amount, risk_amount = sizing
            now_ms = int(time.time() * 1000)

            # Always fill at market price immediately; intended_entry is preserved for reference.
            prices = await _get_prices()
            current_price = prices.get(signal.symbol)
            is_market = True

            # Price tolerance gate: skip if current price has drifted too far from intended entry.
            # Prevents taking a trade where the setup's R:R is already degraded.
            if current_price and signal.entry:
                tolerance = config.get("entry_tolerance_pct", 1.0) / 100
                drift = (current_price - signal.entry) / signal.entry
                too_far = (
                    (signal.direction == "SHORT" and drift < -tolerance) or
                    (signal.direction == "LONG" and drift > tolerance)
                )
                if too_far:
                    reason = (
                        f"entry drift {drift*100:.1f}% exceeds tolerance "
                        f"±{tolerance*100:.1f}% (current={current_price} intended={signal.entry})"
                    )
                    logger.info(f"Orchestrator: {signal.symbol} {signal.direction} SKIPPED — {reason}")
                    await notifier.notify_risk_rejected(signal.symbol, signal.direction, reason)
                    return None

            position = Position(
                signal_log_id=signal.id,
                symbol=signal.symbol,
                direction=signal.direction,
                status="OPEN" if is_market and current_price else "PENDING",
                intended_entry=signal.entry,
                intended_tp=signal.tp,
                intended_sl=signal.sl,
                actual_entry=current_price if is_market and current_price else None,
                filled_at=now_ms if is_market and current_price else None,
                quantity=quantity,
                quote_amount=quote_amount,
                risk_amount=risk_amount,
                conviction=signal.conviction,
                market_state=signal.market_state,
                fired_reason=signal.fired_reason,
                created_at=now_ms,
            )
            session.add(position)

            try:
                await session.flush()  # get position.id
                event_type = "FILLED" if position.status == "OPEN" else "CREATED"
                await _log_event(session, position.id, event_type, {
                    "balance": balance,
                    "entry": signal.entry,
                    "actual_entry": position.actual_entry,
                    "tp": signal.tp,
                    "sl": signal.sl,
                    "quantity": quantity,
                    "quote_amount": quote_amount,
                    "risk_amount": risk_amount,
                    "market_fill": is_market,
                })
                await session.commit()
                await session.refresh(position)
            except Exception as e:
                await session.rollback()
                logger.warning(f"Orchestrator: position insert failed for {signal.symbol} — {e}")
                return None

        if position.status == "OPEN":
            logger.info(
                f"Orchestrator: position FILLED (market) {signal.symbol} {signal.direction} "
                f"@ {position.actual_entry} qty={quantity:.6f} quote=${quote_amount:.2f}"
            )
        else:
            logger.info(
                f"Orchestrator: position CREATED {signal.symbol} {signal.direction} "
                f"entry={signal.entry} qty={quantity:.6f} quote=${quote_amount:.2f}"
            )
        await notifier.notify_position_created(position)
        if position.status == "OPEN":
            await notifier.notify_position_filled(position)
        return position

    # ------------------------------------------------------------------
    # check_pending_fills: PENDING → OPEN or CANCELLED
    # ------------------------------------------------------------------
    async def check_pending_fills(self, config=None, prices=None) -> None:
        if config is None:
            config = await get_trading_config()
        if not config.get("enabled", False):
            return

        if prices is None:
            prices = await _get_prices()
        expiry_ms = config.get("order_expiry_hours", 8) * 3_600_000
        now_ms = int(time.time() * 1000)

        async with Database.get_session() as session:
            result = await session.execute(
                select(Position).where(Position.status == "PENDING")
            )
            pending = result.scalars().all()

            for pos in pending:
                current_price = prices.get(pos.symbol)

                # Check expiry first
                if (now_ms - pos.created_at) >= expiry_ms:
                    pos.status = "CANCELLED"
                    pos.outcome = "EXPIRED"
                    pos.closed_at = now_ms
                    session.add(pos)
                    await _log_event(session, pos.id, "CANCELLED", {
                        "reason": "order_expiry",
                        "age_hours": (now_ms - pos.created_at) / 3_600_000,
                    })
                    logger.info(f"Orchestrator: {pos.symbol} {pos.direction} CANCELLED (expired)")
                    continue

                if current_price is None:
                    continue

                # Fill at current market price; intended_entry preserved for reference
                pos.status = "OPEN"
                pos.actual_entry = current_price
                pos.filled_at = now_ms
                session.add(pos)
                await _log_event(session, pos.id, "FILLED", {
                    "actual_entry": pos.actual_entry,
                    "intended_entry": pos.intended_entry,
                    "current_price": current_price,
                })
                logger.info(
                    f"Orchestrator: {pos.symbol} {pos.direction} FILLED @ {pos.actual_entry} "
                    f"(intended: {pos.intended_entry})"
                )
                await notifier.notify_position_filled(pos)

            await session.commit()

    # ------------------------------------------------------------------
    # check_open_positions: OPEN → CLOSED (WIN/LOSS)
    # ------------------------------------------------------------------
    async def check_open_positions(self, config=None, prices=None) -> None:
        """
        Check TP/SL hits using candle high/low data (not just current price).
        Walks candles from filled_at to determine which target was hit first.
        """
        if config is None:
            config = await get_trading_config()
        if not config.get("enabled", False):
            return

        now_ms = int(time.time() * 1000)

        async with Database.get_session() as session:
            result = await session.execute(
                select(Position).where(Position.status == "OPEN")
            )
            open_positions = result.scalars().all()

            if not open_positions:
                return

            # Fetch candles for each unique symbol
            from app.routes.strategy import get_candles_df
            candle_cache = {}
            unique_symbols = {pos.symbol for pos in open_positions}
            for sym in unique_symbols:
                df = await get_candles_df(sym, timeframe="4h", limit=100)
                if df is not None and not df.empty:
                    candle_cache[sym] = df

            for pos in open_positions:
                if pos.actual_entry is None:
                    continue

                df = candle_cache.get(pos.symbol)
                if df is None or df.empty:
                    continue

                # Walk candles from fill time
                filled_at = pos.filled_at or pos.created_at
                filled_at_ts = pd.Timestamp(filled_at, unit="ms")
                candles_after = df[df["timestamp"] >= filled_at_ts].sort_values("timestamp")

                if candles_after.empty:
                    continue

                outcome = None
                exit_price = None

                for _, candle in candles_after.iterrows():
                    c_high = float(candle.get("high", 0))
                    c_low = float(candle.get("low", 0))
                    c_open = float(candle.get("open", 0))
                    c_close = float(candle.get("close", 0))

                    tp_hit = False
                    sl_hit = False

                    if pos.direction == "LONG":
                        if c_high >= pos.intended_tp:
                            tp_hit = True
                        if c_low <= pos.intended_sl:
                            sl_hit = True
                    else:  # SHORT
                        if c_low <= pos.intended_tp:
                            tp_hit = True
                        if c_high >= pos.intended_sl:
                            sl_hit = True

                    if tp_hit and sl_hit:
                        # Both hit in same candle — use candle direction to infer which hit first
                        if pos.direction == "LONG":
                            if c_close >= c_open:  # Bullish: price moved up → TP hit first
                                outcome, exit_price = "WIN", pos.intended_tp
                            else:  # Bearish: price moved down → SL hit first
                                outcome, exit_price = "LOSS", pos.intended_sl
                        else:
                            if c_close <= c_open:  # Bearish: price moved down → TP hit first
                                outcome, exit_price = "WIN", pos.intended_tp
                            else:  # Bullish: price moved up → SL hit first
                                outcome, exit_price = "LOSS", pos.intended_sl
                    elif tp_hit:
                        outcome, exit_price = "WIN", pos.intended_tp
                    elif sl_hit:
                        outcome, exit_price = "LOSS", pos.intended_sl

                    if outcome:
                        break

                if outcome is None:
                    continue

                # Calculate PnL
                if pos.direction == "LONG":
                    raw_pnl = (exit_price - pos.actual_entry) * pos.quantity
                else:
                    raw_pnl = (pos.actual_entry - exit_price) * pos.quantity

                fee = pos.quote_amount * FEE_PCT
                pnl_usd = raw_pnl - fee
                pnl_pct = (pnl_usd / pos.quote_amount * 100) if pos.quote_amount > 0 else 0.0

                pos.status = "CLOSED"
                pos.outcome = outcome
                pos.actual_exit = exit_price
                pos.pnl_usd = round(pnl_usd, 4)
                pos.pnl_pct = round(pnl_pct, 2)
                pos.closed_at = now_ms
                # Capture market state at close for learning
                summary = await RedisClient.get_json("analytics:signal-summary")
                if summary:
                    pos.market_state_at_close = summary.get("market_state", "")
                session.add(pos)

                event_type = "TP_HIT" if outcome == "WIN" else "SL_HIT"
                await _log_event(session, pos.id, event_type, {
                    "exit_price": exit_price,
                    "pnl_usd": pos.pnl_usd,
                    "pnl_pct": pos.pnl_pct,
                })

                logger.info(
                    f"Orchestrator: {pos.symbol} {pos.direction} CLOSED {outcome} "
                    f"@ {exit_price} pnl=${pnl_usd:.2f} ({pnl_pct:.1f}%)"
                )
                await notifier.notify_position_closed(pos)

            await session.commit()

    # ------------------------------------------------------------------
    # check_circuit_breaker: auto-disable trading on large drawdown
    # ------------------------------------------------------------------
    async def check_circuit_breaker(self, config=None) -> None:
        if config is None:
            config = await get_trading_config()
        if not config.get("enabled", False):
            return

        portfolio = await self._get_portfolio(config)
        balance = await portfolio.get_balance()
        initial = config["initial_capital"]
        max_dd = config.get("max_drawdown_pct", 15.0)
        floor = initial * (1 - max_dd / 100)

        if balance < floor:
            logger.warning(
                f"Orchestrator: CIRCUIT BREAKER triggered — balance ${balance:.2f} < ${floor:.2f}"
            )
            # Cancel all pending, disable trading
            now_ms = int(time.time() * 1000)
            async with Database.get_session() as session:
                result = await session.execute(
                    select(Position).where(Position.status == "PENDING")
                )
                pending = result.scalars().all()
                for pos in pending:
                    pos.status = "CANCELLED"
                    pos.outcome = "EXPIRED"
                    pos.closed_at = now_ms
                    session.add(pos)
                    await _log_event(session, pos.id, "CIRCUIT_BREAKER", {
                        "balance": balance,
                        "floor": floor,
                    })
                await session.commit()

            config["enabled"] = False
            await save_trading_config(config)
            await notifier.notify_circuit_breaker(balance, floor)

    # ------------------------------------------------------------------
    # manual_close: close a position at current market price
    # ------------------------------------------------------------------
    async def manual_close(self, position_id: int) -> Optional[Position]:
        prices = await _get_prices()
        now_ms = int(time.time() * 1000)

        async with Database.get_session() as session:
            result = await session.execute(
                select(Position).where(Position.id == position_id)
            )
            pos = result.scalars().first()
            if pos is None or pos.status not in ("PENDING", "OPEN"):
                return None

            current_price = prices.get(pos.symbol)

            if pos.status == "PENDING":
                pos.status = "CANCELLED"
                pos.outcome = "EXPIRED"
                pos.closed_at = now_ms
                session.add(pos)
                await _log_event(session, pos.id, "CANCELLED", {"reason": "manual_close"})
            else:
                # OPEN — close at market price
                entry = pos.actual_entry or pos.intended_entry
                exit_price = current_price or entry

                if pos.direction == "LONG":
                    raw_pnl = (exit_price - entry) * pos.quantity
                else:
                    raw_pnl = (entry - exit_price) * pos.quantity

                fee = pos.quote_amount * FEE_PCT
                pnl_usd = raw_pnl - fee
                pnl_pct = (pnl_usd / pos.quote_amount * 100) if pos.quote_amount > 0 else 0.0
                outcome = "WIN" if pnl_usd >= 0 else "LOSS"

                pos.status = "CLOSED"
                pos.outcome = outcome
                pos.actual_exit = exit_price
                pos.pnl_usd = round(pnl_usd, 4)
                pos.pnl_pct = round(pnl_pct, 2)
                pos.closed_at = now_ms
                session.add(pos)
                await _log_event(session, pos.id, "SL_HIT", {
                    "exit_price": exit_price,
                    "reason": "manual_close",
                    "pnl_usd": pos.pnl_usd,
                })

            await session.commit()
            await session.refresh(pos)
            return pos
