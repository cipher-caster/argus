"""
Trade Analyzer — pattern analysis on closed paper trading positions.

Queries Position + SignalLog tables to surface performance by symbol,
direction, market state, and conviction bucket. Also compares backtest
WR vs live WR and generates config recommendations.
"""

from __future__ import annotations

import json
from collections import defaultdict

from sqlmodel import select

from app.schemas.signal_log import SignalLog
from app.schemas.trading import Position
from app.storage import Database, RedisClient


def _bucket(conviction: int) -> str:
    if conviction >= 75:
        return "75+"
    if conviction >= 65:
        return "65-74"
    return "55-64"


def _coin_stats(positions: list[Position]) -> dict:
    wins = sum(1 for p in positions if p.outcome == "WIN")
    losses = sum(1 for p in positions if p.outcome == "LOSS")
    closed = wins + losses
    profit_r = 0.0
    hold_hours = []
    for p in positions:
        if p.filled_at and p.closed_at:
            hold_hours.append((p.closed_at - p.filled_at) / 3_600_000)
        risk = abs(p.intended_entry - p.intended_sl)
        reward = abs(p.intended_tp - p.intended_entry)
        rr = reward / risk if risk > 0 else 0
        if p.outcome == "WIN":
            profit_r += rr
        elif p.outcome == "LOSS":
            profit_r -= 1.0
    return {
        "count": len(positions),
        "wins": wins,
        "losses": losses,
        "win_rate": round(wins / closed * 100, 1) if closed > 0 else None,
        "profit_r": round(profit_r, 2),
        "avg_hold_hours": round(sum(hold_hours) / len(hold_hours), 1) if hold_hours else None,
    }


class TradeAnalyzer:
    @staticmethod
    async def analyze_closed_trades() -> dict:
        """
        Analyse closed positions grouped by symbol, direction,
        market state, and conviction bucket.
        """
        async with Database.get_session() as session:
            result = await session.execute(select(Position).where(Position.status == "CLOSED"))
            positions: list[Position] = result.scalars().all()

            # Count rejections from SignalLog (RISK_REJECTED is recorded there
            # because no Position row exists yet at risk-rejection time).
            rejected_result = await session.execute(
                select(SignalLog).where(SignalLog.outcome == "REJECTED")
            )
            rejections = rejected_result.scalars().all()

        if not positions:
            return {
                "total_closed": 0,
                "message": "No closed positions yet. Paper trading needs more time.",
                "by_symbol": {},
                "by_direction": {},
                "by_market_state": {},
                "by_conviction_bucket": {},
                "streak_analysis": {},
                "rejection_count": len(rejections),
            }

        # Group by symbol
        by_symbol: dict[str, list[Position]] = defaultdict(list)
        by_direction: dict[str, list[Position]] = defaultdict(list)
        by_market_state: dict[str, list[Position]] = defaultdict(list)
        by_bucket: dict[str, list[Position]] = defaultdict(list)

        for p in positions:
            by_symbol[p.symbol].append(p)
            by_direction[p.direction].append(p)
            by_market_state[p.market_state].append(p)
            by_bucket[_bucket(p.conviction)].append(p)

        # Streak analysis (sorted by closed_at)
        closed_sorted = sorted(
            [p for p in positions if p.outcome in ("WIN", "LOSS") and p.closed_at],
            key=lambda p: p.closed_at,
        )
        longest_win = longest_loss = current_win = current_loss = 0
        for p in closed_sorted:
            if p.outcome == "WIN":
                current_win += 1
                current_loss = 0
                longest_win = max(longest_win, current_win)
            else:
                current_loss += 1
                current_win = 0
                longest_loss = max(longest_loss, current_loss)

        current_streak = None
        if closed_sorted:
            last = closed_sorted[-1]
            streak_len = current_win if last.outcome == "WIN" else current_loss
            current_streak = {"type": last.outcome, "length": streak_len}

        return {
            "total_closed": len(positions),
            "by_symbol": {sym: _coin_stats(ps) for sym, ps in by_symbol.items()},
            "by_direction": {d: _coin_stats(ps) for d, ps in by_direction.items()},
            "by_market_state": {s: _coin_stats(ps) for s, ps in by_market_state.items()},
            "by_conviction_bucket": {b: _coin_stats(ps) for b, ps in by_bucket.items()},
            "streak_analysis": {
                "longest_win_streak": longest_win,
                "longest_loss_streak": longest_loss,
                "current_streak": current_streak,
            },
            "rejection_count": len(rejections),
        }

    @staticmethod
    async def compare_backtest_vs_live(include_legacy: bool = False) -> dict:
        """
        Compare backtest WR (from SignalLog source=backtest) vs live WR
        (from Position table) per coin. Flags divergence > 15%.
        """
        async with Database.get_session() as session:
            bt_where = [
                SignalLog.source == "backtest",
                SignalLog.outcome.in_(["WIN", "LOSS"]),
            ]
            if not include_legacy:
                bt_where.append(SignalLog.methodology_version == "v2")
            bt_result = await session.execute(select(SignalLog).where(*bt_where))
            bt_signals: list[SignalLog] = bt_result.scalars().all()

            live_result = await session.execute(
                select(Position).where(
                    Position.status == "CLOSED",
                    Position.outcome.in_(["WIN", "LOSS"]),
                )
            )
            live_positions: list[Position] = live_result.scalars().all()

        bt_by_sym: dict[str, list] = defaultdict(list)
        for s in bt_signals:
            bt_by_sym[s.symbol].append(s)

        live_by_sym: dict[str, list] = defaultdict(list)
        for p in live_positions:
            live_by_sym[p.symbol].append(p)

        all_symbols = set(bt_by_sym) | set(live_by_sym)
        comparison = {}
        for sym in sorted(all_symbols):
            bt_sigs = bt_by_sym.get(sym, [])
            live_ps = live_by_sym.get(sym, [])

            bt_wins = sum(1 for s in bt_sigs if s.outcome == "WIN")
            bt_wr = round(bt_wins / len(bt_sigs) * 100, 1) if bt_sigs else None

            live_wins = sum(1 for p in live_ps if p.outcome == "WIN")
            live_wr = round(live_wins / len(live_ps) * 100, 1) if live_ps else None

            divergence = None
            flagged = False
            if bt_wr is not None and live_wr is not None:
                divergence = round(abs(live_wr - bt_wr), 1)
                flagged = divergence > 15

            comparison[sym] = {
                "backtest_wr": bt_wr,
                "backtest_count": len(bt_sigs),
                "live_wr": live_wr,
                "live_count": len(live_ps),
                "divergence": divergence,
                "flagged": flagged,
            }

        return comparison

    @staticmethod
    async def recommend_config() -> list[dict]:
        """
        Rule-based config recommendations from closed trade patterns.
        Each item: {param, current_value, suggested_value, reason, evidence}
        """
        analysis = await TradeAnalyzer.analyze_closed_trades()
        if analysis["total_closed"] < 10:
            return [
                {
                    "param": "data",
                    "current_value": analysis["total_closed"],
                    "suggested_value": 10,
                    "reason": "Not enough closed trades for reliable recommendations",
                    "evidence": f"Only {analysis['total_closed']} closed trades. Need at least 10.",
                }
            ]

        recs = []

        # Conviction: if 75+ WR >> 55-64 WR by 15%+, raise min_conviction
        buckets = analysis.get("by_conviction_bucket", {})
        high = buckets.get("75+", {})
        low = buckets.get("55-64", {})
        if (
            high.get("win_rate")
            and low.get("win_rate")
            and high["win_rate"] - low["win_rate"] > 15
            and high["count"] >= 5
        ):
            r = RedisClient.get_instance()
            t_cfg_raw = await r.get("trading:config")
            t_cfg = json.loads(t_cfg_raw) if t_cfg_raw else {}
            cur_conv = t_cfg.get("min_conviction", 65)
            if cur_conv < 70:
                recs.append(
                    {
                        "param": "min_conviction",
                        "current_value": cur_conv,
                        "suggested_value": 70,
                        "reason": "High-conviction trades (75+) significantly outperform low-conviction",
                        "evidence": f"75+ WR={high['win_rate']}% ({high['count']} trades) vs "
                        f"55-64 WR={low['win_rate']}% ({low['count']} trades)",
                    }
                )

        # Per-coin: if a coin is consistently losing (WR < 35%, >= 5 trades), suggest removal
        for sym, stats in analysis.get("by_symbol", {}).items():
            if stats["count"] >= 5 and stats["win_rate"] is not None and stats["win_rate"] < 35:
                recs.append(
                    {
                        "param": "watchlist",
                        "current_value": sym,
                        "suggested_value": f"remove {sym}",
                        "reason": f"{sym} is consistently losing in live trading",
                        "evidence": f"WR={stats['win_rate']}% over {stats['count']} trades, "
                        f"profit={stats['profit_r']:+.2f}R",
                    }
                )

        # Market state: if a state always loses (WR < 30%, >= 3 trades), suggest blocking
        for state, stats in analysis.get("by_market_state", {}).items():
            if stats["count"] >= 3 and stats["win_rate"] is not None and stats["win_rate"] < 30:
                recs.append(
                    {
                        "param": "block_market_state",
                        "current_value": state,
                        "suggested_value": f"block {state}",
                        "reason": f"{state} market state underperforms consistently",
                        "evidence": f"WR={stats['win_rate']}% over {stats['count']} trades",
                    }
                )

        # Shorts: if shorts WR < 35% with >= 5 trades, suggest blocking
        by_dir = analysis.get("by_direction", {})
        shorts = by_dir.get("SHORT", {})
        if (
            shorts.get("count", 0) >= 5
            and shorts.get("win_rate") is not None
            and shorts["win_rate"] < 35
        ):
            recs.append(
                {
                    "param": "block_shorts",
                    "current_value": False,
                    "suggested_value": True,
                    "reason": "SHORT trades are underperforming",
                    "evidence": f"SHORT WR={shorts['win_rate']}% over {shorts['count']} trades",
                }
            )

        # Backtest vs live divergence
        comparison = await TradeAnalyzer.compare_backtest_vs_live()
        flagged = [sym for sym, c in comparison.items() if c["flagged"]]
        if flagged:
            recs.append(
                {
                    "param": "re_optimization",
                    "current_value": "current config",
                    "suggested_value": "run /optimize",
                    "reason": "Live WR diverges from backtest by >15% for some coins",
                    "evidence": f"Flagged coins: {', '.join(flagged)}",
                }
            )

        if not recs:
            recs.append(
                {
                    "param": "none",
                    "current_value": "current config",
                    "suggested_value": "no change",
                    "reason": "Config looks healthy based on current data",
                    "evidence": f"{analysis['total_closed']} closed trades analyzed",
                }
            )

        return recs

    @staticmethod
    async def generate_report() -> str:
        """Full markdown report combining all analysis."""
        analysis = await TradeAnalyzer.analyze_closed_trades()
        comparison = await TradeAnalyzer.compare_backtest_vs_live()
        recs = await TradeAnalyzer.recommend_config()

        lines = ["# Argus Trade Analysis Report", ""]
        lines.append(f"**Total closed trades:** {analysis['total_closed']}")
        lines.append(f"**Rejection count:** {analysis['rejection_count']}")
        lines.append("")

        if analysis["total_closed"] == 0:
            lines.append("*No closed positions yet.*")
            return "\n".join(lines)

        # By symbol
        lines.append("## Performance by Symbol")
        for sym, s in sorted(analysis["by_symbol"].items()):
            lines.append(
                f"- **{sym}**: {s['count']} trades | WR={s['win_rate']}% | "
                f"Profit={s['profit_r']:+.2f}R | Hold={s['avg_hold_hours']}h"
            )
        lines.append("")

        # By direction
        lines.append("## Performance by Direction")
        for d, s in analysis["by_direction"].items():
            lines.append(
                f"- **{d}**: {s['count']} trades | WR={s['win_rate']}% | Profit={s['profit_r']:+.2f}R"
            )
        lines.append("")

        # By market state
        lines.append("## Performance by Market State")
        for state, s in sorted(analysis["by_market_state"].items()):
            lines.append(f"- **{state}**: {s['count']} trades | WR={s['win_rate']}%")
        lines.append("")

        # By conviction bucket
        lines.append("## Performance by Conviction Bucket")
        for bucket in ["55-64", "65-74", "75+"]:
            s = analysis["by_conviction_bucket"].get(bucket, {})
            if s:
                lines.append(
                    f"- **{bucket}**: {s['count']} trades | WR={s['win_rate']}% | Profit={s['profit_r']:+.2f}R"
                )
        lines.append("")

        # Streak
        streak = analysis.get("streak_analysis", {})
        lines.append("## Streak Analysis")
        lines.append(f"- Longest win streak: {streak.get('longest_win_streak', 0)}")
        lines.append(f"- Longest loss streak: {streak.get('longest_loss_streak', 0)}")
        cur = streak.get("current_streak")
        if cur:
            lines.append(f"- Current streak: {cur['length']}× {cur['type']}")
        lines.append("")

        # Backtest vs live
        flagged = {sym: c for sym, c in comparison.items() if c["flagged"]}
        if flagged:
            lines.append("## ⚠ Backtest vs Live Divergence (>15%)")
            for sym, c in flagged.items():
                lines.append(
                    f"- **{sym}**: backtest={c['backtest_wr']}% vs live={c['live_wr']}% "
                    f"(Δ{c['divergence']}%)"
                )
            lines.append("")

        # Recommendations
        lines.append("## Recommendations")
        for r in recs:
            lines.append(f"- **{r['param']}**: {r['reason']}")
            lines.append(f"  - Evidence: {r['evidence']}")
        lines.append("")

        return "\n".join(lines)
