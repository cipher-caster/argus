"""
Risk Manager — gates every signal before a position is created.

All gates run in order; the first failure rejects the trade.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Minimum position size in USDT — smaller is not meaningful
MIN_QUOTE_USD = 3.0


class RiskManager:

    @staticmethod
    def check_drawdown(balance: float, config: dict) -> tuple[bool, str]:
        """Circuit breaker: stop trading if drawdown exceeds threshold."""
        initial = config.get("initial_capital", 100.0)
        max_dd = config.get("max_drawdown_pct", 15.0)
        floor = initial * (1 - max_dd / 100)
        if balance < floor:
            return False, f"Circuit breaker: balance ${balance:.2f} < floor ${floor:.2f} ({max_dd}% drawdown)"
        return True, ""

    @staticmethod
    def check_max_positions(active_positions: list) -> tuple[bool, str]:
        """Reject if we're already at max concurrent positions."""
        return True, ""  # checked with config in check_all

    @staticmethod
    def check_correlation(symbol: str, open_positions: list, config: dict) -> tuple[bool, str]:
        """Reject if too many correlated coins are already open."""
        max_corr = config.get("max_correlated_positions", 2)
        groups = config.get("correlation_groups", {})

        for group_name, group_symbols in groups.items():
            if symbol not in group_symbols:
                continue
            # Count how many open/pending positions are in this group
            count = sum(1 for p in open_positions if p.symbol in group_symbols)
            if count >= max_corr:
                return False, f"Correlation limit: {count}/{max_corr} {group_name} positions open"

        return True, ""

    @staticmethod
    def check_conviction(conviction: int, config: dict) -> tuple[bool, str]:
        """Reject low-conviction signals."""
        min_conv = config.get("min_conviction", 65)
        if conviction < min_conv:
            return False, f"Low conviction: {conviction} < {min_conv}"
        return True, ""

    @staticmethod
    def check_min_volatility(entry: float, sl: float) -> tuple[bool, str]:
        """Reject stablecoin-like trades where SL is too close to entry."""
        distance_pct = abs(entry - sl) / entry if entry > 0 else 0
        if distance_pct < 0.002:
            return False, f"Min volatility gate: SL distance {distance_pct:.4%} < 0.20% (stablecoin-like)"
        return True, ""

    @staticmethod
    def check_total_exposure(
        open_positions: list, quote_amount: float, balance: float, config: dict
    ) -> tuple[bool, str]:
        """Reject if total portfolio exposure would exceed cap."""
        max_exposure_pct = config.get("max_total_exposure_pct", 300.0)
        current_exposure = sum(p.quote_amount for p in open_positions if p.status in ("PENDING", "OPEN"))
        total = current_exposure + quote_amount
        cap = balance * (max_exposure_pct / 100)
        if total > cap:
            return False, (
                f"Total exposure ${total:.2f} would exceed "
                f"cap ${cap:.2f} ({max_exposure_pct}% of ${balance:.2f})"
            )
        return True, ""

    @staticmethod
    def check_min_order_size(quote_amount: float) -> tuple[bool, str]:
        """Reject positions too small to be meaningful."""
        if quote_amount < MIN_QUOTE_USD:
            return False, f"Position too small: ${quote_amount:.2f} < ${MIN_QUOTE_USD}"
        return True, ""

    @staticmethod
    def calculate_position_size(
        balance: float,
        entry: float,
        sl: float,
        config: dict,
    ) -> tuple[float, float, float]:
        """
        Returns (quantity, quote_amount, risk_amount).

        risk_amount = balance * risk_pct
        quantity    = risk_amount / |entry - sl|
        quote_amount = quantity * entry

        If quote_amount exceeds max_leverage * balance, scale down to cap exposure.
        """
        risk_pct = config.get("max_position_size_pct", 10.0) / 100
        risk_amount = balance * risk_pct
        max_leverage = config.get("max_leverage", 3.0)

        distance = abs(entry - sl)
        if distance <= 0:
            raise ValueError(f"Invalid entry/SL: entry={entry} sl={sl}")

        quantity = risk_amount / distance
        quote_amount = quantity * entry

        # Cap notional exposure at max_leverage * balance
        max_notional = balance * max_leverage
        if quote_amount > max_notional:
            quantity = max_notional / entry
            quote_amount = max_notional
            risk_amount = quantity * distance  # recalculate actual risk

        return quantity, quote_amount, risk_amount

    async def check_all(
        self,
        symbol: str,
        direction: str,
        conviction: int,
        entry: float,
        sl: float,
        config: dict,
        open_positions: list,
        balance: float,
    ) -> tuple[bool, str, Optional[tuple]]:
        """
        Run all gates in order.
        Returns (approved, reason, sizing_tuple).
        sizing_tuple is (quantity, quote_amount, risk_amount) if approved, else None.
        """
        # 1. Drawdown circuit breaker
        ok, reason = self.check_drawdown(balance, config)
        if not ok:
            return False, reason, None

        # 2. Max concurrent positions
        max_pos = config.get("max_concurrent_positions", 3)
        active_count = len([p for p in open_positions if p.status in ("PENDING", "OPEN")])
        if active_count >= max_pos:
            return False, f"Max positions: {active_count}/{max_pos} active", None

        # 3. Correlation
        ok, reason = self.check_correlation(symbol, open_positions, config)
        if not ok:
            return False, reason, None

        # 4. Conviction
        ok, reason = self.check_conviction(conviction, config)
        if not ok:
            return False, reason, None

        # 5. Min volatility (stablecoin filter)
        ok, reason = self.check_min_volatility(entry, sl)
        if not ok:
            return False, reason, None

        # 6. Position sizing
        try:
            quantity, quote_amount, risk_amount = self.calculate_position_size(
                balance, entry, sl, config
            )
        except ValueError as e:
            return False, str(e), None

        # 7. Min order size
        ok, reason = self.check_min_order_size(quote_amount)
        if not ok:
            return False, reason, None

        # 8. Total portfolio exposure
        ok, reason = self.check_total_exposure(open_positions, quote_amount, balance, config)
        if not ok:
            return False, reason, None

        logger.info(
            f"RiskManager: approved {symbol} {direction} "
            f"qty={quantity:.6f} quote=${quote_amount:.2f} risk=${risk_amount:.2f}"
        )
        return True, "approved", (quantity, quote_amount, risk_amount)
