"""
Telegram notifier — fire-and-forget alerts for key trading events.
Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars (both optional).
If not set, all notify calls are no-ops.
"""
import json
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")

_TELEGRAM_URL = "https://api.telegram.org/bot{token}/sendMessage"


async def _send(text: str) -> None:
    """Fire-and-forget Telegram message. Never raises."""
    if not _BOT_TOKEN or not _CHAT_ID:
        return
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                _TELEGRAM_URL.format(token=_BOT_TOKEN),
                json={"chat_id": _CHAT_ID, "text": text, "parse_mode": "HTML"},
            )
    except Exception as e:
        logger.debug(f"Telegram notify failed (non-fatal): {e}")


def _fmt_price(p: float) -> str:
    if p >= 1000:
        return f"${p:,.2f}"
    if p >= 1:
        return f"${p:.4f}"
    return f"${p:.6f}"


async def notify_position_created(position) -> None:
    emoji = "🟢" if position.direction == "LONG" else "🔴"
    msg = (
        f"{emoji} <b>Position Created</b>\n"
        f"{position.symbol} {position.direction}\n"
        f"Entry: {_fmt_price(position.intended_entry)} | "
        f"TP: {_fmt_price(position.intended_tp)} | "
        f"SL: {_fmt_price(position.intended_sl)}\n"
        f"Size: ${position.quote_amount:.2f} | "
        f"Risk: ${position.risk_amount:.2f}\n"
        f"Conviction: {position.conviction}"
    )
    await _send(msg)


async def notify_position_filled(position) -> None:
    emoji = "🟢" if position.direction == "LONG" else "🔴"
    msg = (
        f"{emoji} <b>Position Filled</b>\n"
        f"{position.symbol} {position.direction}\n"
        f"Entry: {_fmt_price(position.actual_entry or position.intended_entry)}\n"
        f"TP: {_fmt_price(position.intended_tp)} | SL: {_fmt_price(position.intended_sl)}"
    )
    await _send(msg)


async def notify_position_closed(position) -> None:
    is_win = position.outcome == "WIN"
    emoji = "✅" if is_win else "❌"
    pnl = position.pnl_usd or 0.0
    pnl_pct = position.pnl_pct or 0.0
    sign = "+" if pnl >= 0 else ""
    msg = (
        f"{emoji} <b>Position Closed — {position.outcome}</b>\n"
        f"{position.symbol} {position.direction}\n"
        f"Entry: {_fmt_price(position.actual_entry or position.intended_entry)} → "
        f"Exit: {_fmt_price(position.actual_exit or 0)}\n"
        f"PnL: {sign}${pnl:.2f} ({sign}{pnl_pct:.1f}%)"
    )
    await _send(msg)


async def notify_risk_rejected(symbol: str, direction: str, reason: str) -> None:
    msg = (
        f"⛔ <b>Risk Rejected</b>\n"
        f"{symbol} {direction}\n"
        f"Reason: {reason}"
    )
    await _send(msg)


async def notify_circuit_breaker(balance: float, threshold: float) -> None:
    msg = (
        f"🚨 <b>Circuit Breaker Triggered</b>\n"
        f"Balance: ${balance:.2f} (below ${threshold:.2f})\n"
        f"Trading has been paused automatically."
    )
    await _send(msg)
